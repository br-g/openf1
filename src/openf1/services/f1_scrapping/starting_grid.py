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


def _parse_starting_grid_page(html_file: Path) -> list[dict]:
    """Parses an HTML file containing session results and extracts the data"""
    with open(html_file, "r", encoding="utf-8") as f:
        html_content = f.read()

    soup = BeautifulSoup(html_content, "lxml")
    table = soup.find("table", class_="Table-module_table__cKsW2")
    headers = [
        header.get_text(strip=True).upper()
        for header in table.find("thead").find_all("th")
    ]

    header_map = {
        "POS.": "position",
        "NO.": "driver_number",
        "TIME": "lap_duration",
    }

    if "no results available" in str(table).lower():
        raise ValueError("No results available")

    rows = table.find("tbody").find_all("tr")

    results_data = []
    for row in rows:
        cols = row.find_all("td")
        driver_data = {}

        for i, header_text in enumerate(headers):
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
                    elif output_key == "driver_number":
                        driver_data[output_key] = int(cell_value)
                    elif output_key == "lap_duration":
                        driver_data[output_key] = (
                            to_timedelta(cell_value).total_seconds()
                            if cell_value is not None
                            else None
                        )
                except (ValueError, IndexError):
                    logger.exception(
                        "Unhandled value format for "
                        f"output_key '{output_key}': {cell_value}"
                    )
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

    if session_data["session_name"].lower() in {"sprint qualifying", "sprint shootout"}:
        page_name = "sprint-grid"
    elif session_data["session_name"].lower() == "qualifying":
        page_name = "starting-grid"
    else:
        raise ValueError(
            f"Session {session_key} is not a qualifying session and has "
            "no starting grid"
        )

    return BASE_URL + f"{session_data['meeting_key']}/aa/{page_name}"


@cli.command()
def ingest_starting_grid(
    meeting_key: int | None = None, session_key: int | None = None
):
    """
    Downloads, parses, and ingests the starting grid for a given qualifying session.

    If `meeting_key` and `session_key` is None, defaults to the latest session
    (or session in progress).
    """
    if (meeting_key is None) is not (session_key is None):
        raise ValueError("Provide meeting_key and session_key params, or none of them.")

    if meeting_key is None and session_key is None:
        meeting_key = get_latest_meeting_key()
        session_key = get_latest_session_key()

    grid_url = _session_key_to_page_url(session_key)
    logger.info(f"Ingesting starting grid of session {session_key}, from {grid_url}")

    with tempfile.NamedTemporaryFile(
        mode="w", delete=True, suffix=".html"
    ) as temp_file:
        download_page(
            url=grid_url,
            output_file=Path(temp_file.name),
        )
        docs = _parse_starting_grid_page(Path(temp_file.name))
        if not docs:
            logger.error(f"No starting grid data found for meeting_key={meeting_key}")
            return

        # Add missing fields
        for idx, doc in enumerate(docs):
            doc["meeting_key"] = meeting_key
            doc["session_key"] = session_key
            doc["_id"] = f"{session_key}_{str(idx).zfill(2)}"
            doc["_key"] = doc["_id"]

        upsert_data_sync(collection_name="starting_grid", docs=docs)


if __name__ == "__main__":
    cli()
