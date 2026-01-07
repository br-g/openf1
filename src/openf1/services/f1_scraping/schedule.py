from datetime import datetime, timedelta, timezone

import requests
import typer
from loguru import logger
from tqdm import tqdm

from openf1.util.db import upsert_data_sync

HEADERS = {
    "apiKey": "v1JVGPgXlahatAqwhakbrGtFdxW5rQBz",  # Is this key rotated sometimes?
    "locale": "en",
}

cli = typer.Typer()


def _convert_gmt_offset(offset_str: str) -> str:
    """
    Converts GMT offset like "+04:00" to "04:00:00"
    and "-04:00" to "-04:00:00".
    """
    cleaned_offset = offset_str.lstrip("+")
    return f"{cleaned_offset}:00"


def _convert_to_utc(date_str: str, offset_str: str) -> str:
    local_dt = datetime.fromisoformat(date_str)

    is_negative = offset_str.startswith("-")
    clean_offset = offset_str.lstrip("-")
    hours, minutes, seconds = map(int, clean_offset.split(":"))
    offset_delta = timedelta(hours=hours, minutes=minutes, seconds=seconds)
    if is_negative:
        offset_delta = -offset_delta

    utc_dt = local_dt - offset_delta
    utc_dt = utc_dt.replace(tzinfo=timezone.utc)
    return utc_dt.isoformat()


def fetch_meetings(year: int | None = None) -> dict:
    """If year param is not provided, returns list of meeting for the latest available season."""
    url = "http://api.formula1.com/v1/editorial-eventlisting/events"
    params = {"season": year} if year else {}
    response = requests.get(url, params=params, headers=HEADERS)
    response.raise_for_status()
    data = response.json()

    results = []
    for event in data["events"]:
        gmt_offset = _convert_gmt_offset(event["gmtOffset"])
        date_start = datetime.fromisoformat(
            _convert_to_utc(date_str=event["meetingStartDate"], offset_str=gmt_offset)
        )
        date_end = datetime.fromisoformat(
            _convert_to_utc(date_str=event["meetingEndDate"], offset_str=gmt_offset)
        )
        results.append(
            {
                "meeting_key": int(event["meetingKey"]),
                "circuit_key": int(event["circuitKey"]),
                "circuit_short_name": event["circuitShortName"],
                "circuit_type": event["circuitType"],
                "circuit_image": event["circuitMediumImage"],
                "meeting_code": event["meetingCountryCode"],
                "location": event["meetingLocation"],
                "country_key": int(event["countryKey"]),
                "country_code": event["meetingCountryCode"],
                "country_flag": event["countryFlag"],
                "country_name": event["meetingIsoCountryName"],
                "meeting_name": event["meetingName"],
                "meeting_official_name": event["meetingOfficialName"],
                "gmt_offset": gmt_offset,
                "date_start": date_start,
                "date_end": date_end,
                "year": int(data["year"]),
            }
        )

    return results


def _fetch_raw_sessions_data(meeting_key: int) -> dict:
    url = f"https://api.formula1.com/v1/event-tracker/meeting/{meeting_key}"
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    data = response.json()
    timetables = data["meetingContext"]["timetables"]
    return timetables


def fetch_sessions(year: int | None = None) -> dict:
    """If year param is not provided, returns list of sessions for the latest available season."""
    meetings = fetch_meetings(year)

    sessions = []
    for meeting in tqdm(meetings):
        raw_sessions_data = _fetch_raw_sessions_data(meeting["meeting_key"])
        for raw_sess_data in raw_sessions_data:
            date_start = datetime.fromisoformat(
                _convert_to_utc(
                    date_str=raw_sess_data["startTime"],
                    offset_str=meeting["gmt_offset"],
                )
            )
            date_end = datetime.fromisoformat(
                _convert_to_utc(
                    date_str=raw_sess_data["endTime"], offset_str=meeting["gmt_offset"]
                )
            )
            sessions.append(
                {
                    "meeting_key": meeting["meeting_key"],
                    "session_key": raw_sess_data["meetingSessionKey"],
                    "location": meeting["location"],
                    "date_start": date_start,
                    "date_end": date_end,
                    "session_type": raw_sess_data["sessionType"],
                    "session_name": raw_sess_data["description"],
                    "country_key": meeting["country_key"],
                    "country_code": meeting["country_code"],
                    "country_name": meeting["country_name"],
                    "circuit_key": meeting["circuit_key"],
                    "circuit_short_name": meeting["circuit_short_name"],
                    "gmt_offset": meeting["gmt_offset"],
                    "year": meeting["year"],
                }
            )
    return sessions


@cli.command()
def ingest_meetings(year: int | None = None):
    """If year param is not provided, returns list of meetings for the latest available season."""
    meetings = fetch_meetings(year)
    logger.info(f"Ingesting {len(meetings)} meetings")

    # Add meta fields
    for doc in meetings:
        doc["_id"] = doc["meeting_key"]
        doc["_key"] = doc["_id"]

    upsert_data_sync(collection_name="meetings", docs=meetings)


@cli.command()
def ingest_sessions(year: int | None = None):
    """If year param is not provided, returns list of sessions for the latest available season."""
    sessions = fetch_sessions(year)
    logger.info(f"Ingesting {len(sessions)} sessions")

    # Add meta fields
    for doc in sessions:
        doc["_id"] = doc["session_key"]
        doc["_key"] = doc["_id"]

    upsert_data_sync(collection_name="sessions", docs=sessions)


if __name__ == "__main__":
    cli()
