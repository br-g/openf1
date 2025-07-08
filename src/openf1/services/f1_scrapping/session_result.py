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

BASE_URL = "https://www.formula1.com/en/results/"

cli = typer.Typer()


def _parse_time_gap(time_gap: str | None) -> str | float | None:
    """
    Parses a time string, which can be an absolute lap time (e.g., "1:10.899"),
    a gap time (e.g., "+0.281s"), or a status string (e.g., "DNF").
    """
    if time_gap in {"DNS", "DNF", "DSQ"}:
        return time_gap

    if time_gap is None or time_gap == "":
        return None

    # Check for gap formats (e.g., "+0.281s" or "+1 LAP").
    if time_gap.startswith("+"):
        if "LAP" in time_gap.upper():
            return time_gap.upper()
        elif time_gap.endswith("s"):
            try:
                return float(time_gap[1:-1])
            except ValueError:
                logger.error(f"Unrecognized time gap format: {time_gap}")

    # Handle durations like "1:10.899"
    else:
        try:
            return to_timedelta(time_gap).total_seconds()
        except (ValueError, AttributeError):
            logger.error(f"Unrecognized time gap format: {time_gap}")


def _parse_page(html_file: Path) -> list[dict]:
    """Parses an HTML file containing Formula 1 session results and extracts the data"""
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

    header_map = {
        "POS.": "position",
        "NO.": "driver_number",
        "LAPS": "number_of_laps",
        "TIME/RETIRED": "time_gap",
        "TIME / RETIRED": "time_gap",
        "TIME / GAP": "time_gap",
        "TIME": "time_gap",
        "PTS.": "points",
        "PTS": "points",
        "Q1": "Q1",
        "Q2": "Q2",
        "Q3": "Q3",
    }

    # Step 1: Initial parse of the table into a list of dictionaries
    rows = table.find("tbody").find_all("tr")
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
                    elif output_key in ["driver_number", "number_of_laps"]:
                        driver_data[output_key] = int(cell_value)
                    elif output_key == "points":
                        driver_data[output_key] = float(cell_value)
                    elif output_key in {"time_gap", "Q1", "Q2", "Q3"}:
                        # _parse_time_gap now correctly returns status strings or parsed times
                        driver_data[output_key] = _parse_time_gap(cell_value)
                    else:
                        driver_data[output_key] = cell_value
                except (ValueError, IndexError):
                    driver_data[output_key] = cell_value
        if driver_data:
            results_data.append(driver_data)

    if not results_data:
        return []

    # Step 2: Determine session type and process the data accordingly
    is_qualifying = bool(results_data and "Q1" in results_data[0])

    if is_qualifying:
        # --- QUALIFYING SESSION PROCESSING ---
        valid_q1_times = [
            d["Q1"] for d in results_data if isinstance(d.get("Q1"), float)
        ]
        valid_q2_times = [
            d["Q2"] for d in results_data if isinstance(d.get("Q2"), float)
        ]
        valid_q3_times = [
            d["Q3"] for d in results_data if isinstance(d.get("Q3"), float)
        ]

        fastest_q1 = min(valid_q1_times) if valid_q1_times else None
        fastest_q2 = min(valid_q2_times) if valid_q2_times else None
        fastest_q3 = min(valid_q3_times) if valid_q3_times else None

        for doc in results_data:
            q1_duration = doc.get("Q1")
            q2_duration = doc.get("Q2")
            q3_duration = doc.get("Q3")

            # Set status flags based on explicit strings from the website
            q_statuses = {
                str(q)
                for q in [q1_duration, q2_duration, q3_duration]
                if isinstance(q, str)
            }
            doc["dnf"] = "DNF" in q_statuses
            doc["dns"] = "DNS" in q_statuses
            doc["dsq"] = "DSQ" in q_statuses

            # If driver has a status, nullify duration and gap fields
            if doc["dnf"] or doc["dns"] or doc["dsq"]:
                doc["duration"] = None
                doc["gap_to_leader"] = None
            else:
                # Otherwise, calculate duration and gap arrays as normal
                doc["duration"] = [q1_duration, q2_duration, q3_duration]
                gap_q1 = (
                    round(q1_duration - fastest_q1, 3)
                    if isinstance(q1_duration, float) and fastest_q1 is not None
                    else None
                )
                gap_q2 = (
                    round(q2_duration - fastest_q2, 3)
                    if isinstance(q2_duration, float) and fastest_q2 is not None
                    else None
                )
                gap_q3 = (
                    round(q3_duration - fastest_q3, 3)
                    if isinstance(q3_duration, float) and fastest_q3 is not None
                    else None
                )
                doc["gap_to_leader"] = [gap_q1, gap_q2, gap_q3]

            # Remove original qualifying fields
            doc.pop("Q1", None)
            doc.pop("Q2", None)
            doc.pop("Q3", None)

    else:
        # --- RACE SESSION PROCESSING ---
        # Add dnf, dns, and dsq columns based on the parsed status
        for doc in results_data:
            time_status = doc.get("time_gap")
            doc["dnf"] = time_status == "DNF"
            doc["dns"] = time_status == "DNS"
            doc["dsq"] = time_status == "DSQ"

        leader_duration = None
        leader_data = next((d for d in results_data if d.get("position") == 1), None)

        if leader_data and isinstance(leader_data.get("time_gap"), float):
            leader_duration = leader_data["time_gap"]
        elif results_data and isinstance(results_data[0].get("time_gap"), float):
            leader_duration = results_data[0].get("time_gap")

        for doc in results_data:
            time_info = doc.pop("time_gap", None)
            is_leader = doc.get("position") == 1

            if is_leader and leader_duration is not None:
                doc["duration"] = leader_duration
                doc["gap_to_leader"] = 0.0
            # If driver has a status, nullify duration and gap fields
            elif time_info in {"DNF", "DNS", "DSQ"}:
                doc["duration"] = None
                doc["gap_to_leader"] = None
            else:
                if isinstance(time_info, float):
                    doc["gap_to_leader"] = time_info
                    if leader_duration is not None:
                        doc["duration"] = leader_duration + time_info
                    else:
                        doc["duration"] = None
                elif isinstance(time_info, str):  # Handles cases like "+1 LAP"
                    doc["gap_to_leader"] = time_info
                    doc["duration"] = None
                else:
                    doc["duration"] = None
                    doc["gap_to_leader"] = None

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

    return (
        BASE_URL
        + f"{session_data['year']}/races/{session_data['meeting_key']}/aa/{page_name}"
    )


@cli.command()
def ingest_session_result(
    meeting_key: int | None = None, session_key: int | None = None
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
            print(doc)
            doc["meeting_key"] = meeting_key
            doc["session_key"] = session_key
            doc["_id"] = f"{session_key}_{doc['driver_number']}"
            doc["_key"] = doc["_id"]

        upsert_data_sync(collection_name="session_result", docs=docs)


if __name__ == "__main__":
    cli()
