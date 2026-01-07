import tempfile
from pathlib import Path

import typer
from bs4 import BeautifulSoup
from bs4.element import Tag
from loguru import logger

from openf1.services.f1_scraping.util import download_page
from openf1.util import openf1_client
from openf1.util.db import upsert_data_sync
from openf1.util.misc import to_timedelta
from openf1.util.schedule import get_latest_meeting_key, get_latest_session_key

cli = typer.Typer()


def _parse_time_gap(time_gap: str | None) -> str | float | None:
    """
    Parses a time string, which can be an absolute lap time (e.g., "1:10.899"),
    a gap time (e.g., "+0.281s"), or a status string (e.g., "DNF").
    """
    if time_gap is None or time_gap == "":
        return None

    if time_gap in {"DNS", "DNF", "DSQ"}:
        return time_gap

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
            logger.exception(f"Unrecognized time gap format: {time_gap}")


def _extract_raw_results(table: Tag) -> list[dict]:
    """Extracts data from the table rows into a list of dictionaries"""
    headers = [
        th.get_text(strip=True).upper() for th in table.find("thead").find_all("th")
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

    if "no results available" in str(table).lower():
        raise ValueError("No results available")

    results = []
    for row in table.find("tbody").find_all("tr"):
        cols = row.find_all("td")
        driver_data = {}

        for i, header_text in enumerate(headers):
            output_key = header_map.get(header_text)
            if not output_key or i >= len(cols):
                continue

            cell_value = cols[i].get_text(strip=True)
            if not cell_value:
                driver_data[output_key] = None
                continue

            try:
                if output_key == "position":
                    driver_data[output_key] = (
                        int(cell_value) if cell_value not in {"DQ", "NC"} else None
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
                logger.exception(
                    "Unhandled value format for "
                    f"output_key '{output_key}': {cell_value}"
                )
                driver_data[output_key] = cell_value

        if driver_data:
            results.append(driver_data)

    return results


def _process_qualifying_results(results_data: list[dict]) -> list[dict]:
    """Processes qualifying results to calculate gaps and set status flags"""
    # Find the best sector times, which are the baseline durations
    best_times = {
        q_key: min(
            [d[q_key] for d in results_data if isinstance(d.get(q_key), float)],
            default=None,
        )
        for q_key in ["Q1", "Q2", "Q3"]
    }

    for doc in results_data:
        q_times = {"Q1": doc.get("Q1"), "Q2": doc.get("Q2"), "Q3": doc.get("Q3")}

        statuses = {q for q in q_times.values() if isinstance(q, str)}
        doc["dnf"], doc["dns"], doc["dsq"] = (
            "DNF" in statuses,
            "DNS" in statuses,
            "DSQ" in statuses,
        )
        doc["duration"] = [
            q_times[k] if isinstance(q_times[k], float) else None
            for k in ["Q1", "Q2", "Q3"]
        ]
        doc["gap_to_leader"] = [
            (
                round(q_times[k] - best_times[k], 3)
                if isinstance(q_times.get(k), float) and best_times[k]
                else None
            )
            for k in ["Q1", "Q2", "Q3"]
        ]

        # Clean up original Q1, Q2, Q3 fields
        doc.pop("Q1", None), doc.pop("Q2", None), doc.pop("Q3", None)

    return results_data


def _process_practice_and_race_results(results_data: list[dict]) -> list[dict]:
    """Processes results to calculate duration, gaps, and set status flags"""
    # Find the leader's time, which is the baseline duration
    leader_duration = None
    leader = next((d for d in results_data if d.get("position") == 1), None)
    if leader and isinstance(leader.get("time_gap"), float):
        leader_duration = leader["time_gap"]

    for doc in results_data:
        time_info = doc.pop("time_gap", None)

        for status in ["DNF", "DNS", "DSQ"]:
            doc[status.lower()] = time_info == status
        if time_info in {"DNF", "DNS", "DSQ"}:
            time_info = None

        is_leader = doc.get("position") == 1

        if is_leader and leader_duration is not None:
            doc["duration"], doc["gap_to_leader"] = leader_duration, 0
        elif isinstance(time_info, float) and leader_duration is not None:
            doc["gap_to_leader"] = time_info
            doc["duration"] = round(leader_duration + time_info, 3)
        else:
            # Handles strings like "+1 Lap" or cases where leader time is unknown
            doc["gap_to_leader"] = time_info
            doc["duration"] = None

    return results_data


def _parse_page(html_file: Path) -> list[dict]:
    """
    Parses an HTML file for session results, orchestrating the extraction and processing
    """
    with open(html_file, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f, "lxml")

    table = soup.find("table", class_="Table-module_table__cKsW2")
    raw_results = _extract_raw_results(table)

    is_qualifying = "Q1" in raw_results[0]
    if is_qualifying:
        return _process_qualifying_results(raw_results)
    else:
        return _process_practice_and_race_results(raw_results)


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
        "https://www.formula1.com/en/results/"
        + f"{session_data['year']}/races/{session_data['meeting_key']}/aa/{page_name}"
    )


@cli.command()
def ingest_session_result(
    meeting_key: int | None = None, session_key: int | None = None
):
    """
    If `meeting_key` and `session_key` is None, defaults to the latest session
    (or session in progress).
    """
    if (meeting_key is None) is not (session_key is None):
        raise ValueError("Provide meeting_key and session_key params, or none of them.")

    if meeting_key is None and session_key is None:
        meeting_key = get_latest_meeting_key()
        session_key = get_latest_session_key()

    session_url = _session_key_to_page_url(session_key)
    logger.info(f"Ingesting result of session {session_key}, from {session_url}")

    with tempfile.NamedTemporaryFile(mode="w", delete=True) as temp:
        download_page(
            url=session_url,
            output_file=Path(temp.name),
        )
        docs = _parse_page(Path(temp.name))

        # Add missing fields
        for idx, doc in enumerate(docs):
            doc["meeting_key"] = meeting_key
            doc["session_key"] = session_key
            doc["_id"] = f"{session_key}_{str(idx).zfill(2)}"
            doc["_key"] = doc["_id"]

        upsert_data_sync(collection_name="session_result", docs=docs)


if __name__ == "__main__":
    cli()
