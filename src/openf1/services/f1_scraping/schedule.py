from datetime import datetime, timedelta, timezone

import requests
import typer
from loguru import logger
from tqdm import tqdm

from openf1.util.db import upsert_data_sync

BASE_URL = "http://api.formula1.com/v1"
HEADERS = {
    "apiKey": "v1JVGPgXlahatAqwhakbrGtFdxW5rQBz",  # Is this key rotated sometimes?
    "locale": "en",
}

app = typer.Typer()
session = requests.Session()
session.headers.update(HEADERS)


def _to_utc(date_str: str, offset_str: str) -> datetime:
    """Combines date and offset strings into a timezone-aware UTC datetime."""
    local_dt = datetime.fromisoformat(date_str)

    is_negative = offset_str.startswith("-")
    clean_offset = offset_str.lstrip("-")
    hours, minutes, seconds = map(int, clean_offset.split(":"))
    offset_delta = timedelta(hours=hours, minutes=minutes, seconds=seconds)
    if is_negative:
        offset_delta = -offset_delta

    utc_dt = local_dt - offset_delta
    utc_dt = utc_dt.replace(tzinfo=timezone.utc)
    return utc_dt


def _convert_gmt_offset(offset_str: str) -> str:
    """
    Converts GMT offset like "+04:00" to "04:00:00"
    and "-04:00" to "-04:00:00".
    """
    cleaned_offset = offset_str.lstrip("+")
    return f"{cleaned_offset}:00"


def _normalize_session_name(session_name: str) -> str:
    """
    Replaces legacy session names with their modern equivalents.
    If the session name is not a legacy name, returns the session name unmodified.
    See https://docs.fastf1.dev/events.html#session-identifiers for background information.
    """
    match session_name:
        case "Sprint Shootout":
            return "Sprint Qualifying"
        case _:
            return session_name


def _normalize_session_type(session_type: str) -> str:
    """
    Replaces legacy session types with more general types to be consistent with other sessions.
    If the session type is not a legacy type, returns the session type unmodified.
    See https://docs.fastf1.dev/events.html#session-identifiers for background information.
    """
    match session_type:
        case "Sprint Shootout":
            return "Qualifying"
        case "Sprint Qualifying":
            return "Race"
        case _:
            return session_type


def get_meetings(year: int | None = None) -> list[dict]:
    """Fetches list of meetings for a specific year or the latest season."""
    url = f"{BASE_URL}/editorial-eventlisting/events"
    params = {"season": year} if year else {}

    resp = session.get(url, params=params)
    resp.raise_for_status()
    data = resp.json()

    results = []
    for event in data["events"]:
        offset = _convert_gmt_offset(event["gmtOffset"])
        results.append(
            {
                "meeting_key": int(event["meetingKey"]),
                "meeting_name": event["meetingName"],
                "meeting_official_name": event["meetingOfficialName"],
                "location": event["meetingLocation"],
                "country_key": int(event["countryKey"]),
                "country_code": event["meetingCountryCode"],
                "country_name": event["meetingIsoCountryName"],
                "country_flag": event["countryFlag"],
                "circuit_key": int(event["circuitKey"]),
                "circuit_short_name": event["circuitShortName"],
                "circuit_type": event["circuitType"],
                "circuit_image": event["circuitMediumImage"],
                "gmt_offset": offset,
                "date_start": _to_utc(event["meetingStartDate"], offset),
                "date_end": _to_utc(event["meetingEndDate"], offset),
                "year": int(data["year"]),
            }
        )

    return results


def _get_timetable(meeting_key: int) -> list[dict]:
    """Fetches raw session timetable for a specific meeting."""
    url = f"{BASE_URL}/event-tracker/meeting/{meeting_key}"
    resp = session.get(url)
    resp.raise_for_status()
    return resp.json()["meetingContext"]["timetables"]


def get_sessions(year: int | None = None) -> list[dict]:
    """Fetches all sessions for a specific year or the latest season."""
    meetings = get_meetings(year)
    sessions = []

    for meeting in tqdm(meetings, desc="Fetching sessions"):
        timetable = _get_timetable(meeting["meeting_key"])

        for sess in timetable:
            sessions.append(
                {
                    "session_key": sess["meetingSessionKey"],
                    "session_type": _normalize_session_type(sess["sessionType"]),
                    "session_name": _normalize_session_name(sess["description"]),
                    "date_start": _to_utc(sess["startTime"], meeting["gmt_offset"]),
                    "date_end": _to_utc(sess["endTime"], meeting["gmt_offset"]),
                    "meeting_key": meeting["meeting_key"],
                    "circuit_key": meeting["circuit_key"],
                    "circuit_short_name": meeting["circuit_short_name"],
                    "country_key": meeting["country_key"],
                    "country_code": meeting["country_code"],
                    "country_name": meeting["country_name"],
                    "location": meeting["location"],
                    "gmt_offset": meeting["gmt_offset"],
                    "year": meeting["year"],
                }
            )

    return sessions


def _ingest(data: list[dict], collection: str, id_field: str):
    """Helper to process and upsert data."""
    if not data:
        logger.warning(f"No data found for collection {collection}")
        return

    logger.info(f"Ingesting {len(data)} documents into '{collection}'")
    for doc in data:
        doc["_id"] = doc[id_field]
        doc["_key"] = doc[id_field]

    upsert_data_sync(collection_name=collection, docs=data)


@app.command()
def ingest_meetings(year: int = typer.Option(None, help="Season year")):
    """Ingest meeting data into the database."""
    data = get_meetings(year)
    _ingest(data, "meetings", "meeting_key")


@app.command()
def ingest_sessions(year: int = typer.Option(None, help="Season year")):
    """Ingest session data into the database."""
    data = get_sessions(year)
    _ingest(data, "sessions", "session_key")


if __name__ == "__main__":
    app()
