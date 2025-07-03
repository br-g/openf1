import tempfile
from pathlib import Path

import typer
from bs4 import BeautifulSoup
from loguru import logger

from openf1.services.f1_scrapping.util import download_page
from openf1.util import openf1_client
from openf1.util.db import upsert_data_sync
from openf1.util.misc import to_timedelta
from openf1.util.schedule import get_latest_meeting_key, get_latest_session_key

BASE_URL = "https://www.formula1.com/en/results/aa/races/"

cli = typer.Typer()


def _parse_time_gap(time_gap: str | None) -> str | float | None:
    if time_gap is None or time_gap == "" or time_gap in {"DNS", "DNF"}:
        return None

    # Handle leader
    try:
        return to_timedelta(time_gap).total_seconds()
    except:
        pass

    if time_gap.startswith("+"):
        # Handle cases like '+1 LAP'
        if "LAP" in time_gap.upper():
            return time_gap.upper()

        # Handle cases like '+67.754s'
        elif time_gap.endswith("s"):
            return float(time_gap[1:-1])

    logger.error(f"Unrecognized time_gap format: {time_gap}")


def _parse_page(html_file: Path) -> list[dict]:
    """
    Parses an HTML file containing Formula 1 session results and extracts the data.
    This function is designed to work with different session types (Race, Practice, Qualifying).
    """
    with open(html_file, "r", encoding="utf-8") as f:
        html_content = f.read()

    soup = BeautifulSoup(html_content, "lxml")

    results_data = []

    table = soup.find("table", class_="f1-table")

    if not table:
        return results_data

    headers = [
        header.get_text(strip=True).upper()
        for header in table.find("thead").find_all("th")
    ]

    # A more robust mapping that handles variations in header text
    header_map = {
        "POS.": "position",
        "NO.": "driver_number",
        "LAPS": "number_of_laps",
        "TIME/RETIRED": "time_gap",
        "TIME / RETIRED": "time_gap",  # Added variation
        "TIME / GAP": "time_gap",
        "TIME": "time_gap",  # Added variation
        "PTS.": "points",
        "PTS": "points",  # Added variation
        "Q1": "Q1",
        "Q2": "Q2",
        "Q3": "Q3",
    }

    rows = table.find("tbody").find_all("tr")

    for row in rows:
        cols = row.find_all("td")
        driver_data = {}

        for i, header_text in enumerate(headers):
            # Use the normalized (uppercase) header to find the output key
            output_key = header_map.get(header_text.upper())

            if output_key and i < len(cols):
                cell_value = cols[i].get_text(strip=True)

                if not cell_value:
                    driver_data[output_key] = None
                    continue

                try:
                    if output_key == "position":
                        driver_data[output_key] = (
                            int(cell_value) if cell_value != "NC" else None
                        )
                    elif output_key in ["driver_number", "number_of_laps"]:
                        driver_data[output_key] = int(cell_value)
                    elif output_key == "points":
                        driver_data[output_key] = float(cell_value)
                    elif output_key in {"time_gap", "Q1", "Q2", "Q3"}:
                        driver_data[output_key] = _parse_time_gap(cell_value)
                    else:
                        driver_data[output_key] = cell_value
                except (ValueError, IndexError):
                    driver_data[output_key] = cell_value

        if driver_data:
            results_data.append(driver_data)

    return results_data


def _session_key_to_page_url(session_key: int) -> str:
    api_results = openf1_client.get(f"v1/sessions?session_key={session_key}")
    if len(api_results) != 1:
        raise ValueError(
            "Unexpected number of sessions for "
            f"session_key={session_key}: {len(api_results)}"
        )
    session_data = api_results[0]

    if session_data["session_type"].lower() == "practice":
        practice_number = int(session_data["session_name"].split()[1])
        page_name = f"practice/{practice_number}"
    elif session_data["session_name"].lower() in {
        "sprint qualifying",
        "sprint shootout",
    }:
        page_name = "sprint-qualifying"
    elif session_data["session_name"].lower() == "qualifying":
        page_name = "qualifying"
    elif session_data["session_name"].lower() == "sprint":
        page_name = "sprint-results"
    elif session_data["session_name"].lower() == "race":
        page_name = "race-result"

    return BASE_URL + f"{session_data['meeting_key']}/aa/{page_name}"


@cli.command()
def ingest_session_result(
    meeting_key: str | None = None, session_key: int | None = None
):
    """
    If meeting_key and session_key is None, defaults to the latest session
    (or session in progress).
    """
    if (meeting_key is None) is not (session_key is None):
        raise ValueError("Provide meeting_key and session_key params, or none of them.")

    if meeting_key is None and session_key is None:
        meeting_key = get_latest_meeting_key()
        session_key = get_latest_session_key()

    session_url = _session_key_to_page_url(session_key)

    with tempfile.NamedTemporaryFile(mode="w", delete=True) as temp:
        download_page(
            url=session_url,
            output_file=Path(temp.name),
        )
        docs = _parse_page(Path(temp.name))

        # Add missing fields
        for i, doc in enumerate(docs):
            doc["meeting_key"] = meeting_key
            doc["session_key"] = session_key
            doc["_id"] = f"{session_key}_{i}"
            doc["_key"] = doc["_id"]

        upsert_data_sync(collection_name="session_result", docs=docs)


if __name__ == "__main__":
    cli()
