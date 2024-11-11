import json
from functools import lru_cache

import requests

from openf1.util.misc import join_url
from openf1.util.db import get_latest_session_info
from openf1.util.misc import join_url


@lru_cache()
def get_schedule(year: int) -> dict:
    """Fetches the Formula 1 race schedule for a specified year (past sessions only)"""
    BASE_URL = "https://livetiming.formula1.com/static"
    url = join_url(BASE_URL, f"{year}/Index.json")
    response = requests.get(url)
    content_json = response.content
    content_dict = json.loads(content_json)
    return content_dict


def get_meeting_keys(year: int) -> list[int]:
    """Returns the keys of the meetings for a specific year (past meetings only)"""
    keys = [m["Key"] for m in get_schedule(year)["Meetings"]]
    return keys


def get_session_keys(year: int, meeting_key: int) -> list[int]:
    """Returns the keys of the sessions for a specific meeting (past sessions only)"""
    for meeting in get_schedule(year)["Meetings"]:
        if meeting["Key"] == meeting_key:
            session_keys = [e["Key"] for e in meeting["Sessions"]]
            return session_keys

    raise SystemError(
        f"Meeting not found (year: `{year}`, meeting_key: `{meeting_key}`)"
    )


def get_latest_meeting_key() -> int:
    return get_latest_session_info()["meeting_key"]


def get_latest_session_key() -> int:
    return get_latest_session_info()["session_key"]
