import json
from functools import lru_cache

import requests

from openf1.util.db import get_latest_session_info
from openf1.util.misc import join_url

MISSING_SESSIONS = {
    # TODO: Add sessions for year 2022 (which are all missing)
    2024: {
        1228: [
            {
                "session_key": 9462,
                "path": "2024/2024-02-23_Pre-Season_Testing/2024-02-21_Practice_1/",
            },
            {
                "session_key": 9463,
                "path": "2024/2024-02-23_Pre-Season_Testing/2024-02-22_Practice_2/",
            },
            {
                "session_key": 9464,
                "path": "2024/2024-02-23_Pre-Season_Testing/2024-02-23_Practice_3/",
            },
        ],
        1229: [
            {
                "session_key": 9465,
                "path": "2024/2024-03-02_Bahrain_Grand_Prix/2024-02-29_Practice_1/",
            },
            {
                "session_key": 9466,
                "path": "2024/2024-03-02_Bahrain_Grand_Prix/2024-02-29_Practice_2/",
            },
            {
                "session_key": 9467,
                "path": "2024/2024-03-02_Bahrain_Grand_Prix/2024-03-01_Practice_3/",
            },
            {
                "session_key": 9468,
                "path": "2024/2024-03-02_Bahrain_Grand_Prix/2024-03-01_Qualifying/",
            },
            {
                "session_key": 9472,
                "path": "2024/2024-03-02_Bahrain_Grand_Prix/2024-03-02_Race/",
            },
        ],
        1230: [
            {
                "session_key": 9473,
                "path": "2024/2024-03-09_Saudi_Arabian_Grand_Prix/2024-03-07_Practice_1/",
            },
            {
                "session_key": 9474,
                "path": "2024/2024-03-09_Saudi_Arabian_Grand_Prix/2024-03-07_Practice_2/",
            },
            {
                "session_key": 9475,
                "path": "2024/2024-03-09_Saudi_Arabian_Grand_Prix/2024-03-08_Practice_3/",
            },
            {
                "session_key": 9476,
                "path": "2024/2024-03-09_Saudi_Arabian_Grand_Prix/2024-03-08_Qualifying/",
            },
            {
                "session_key": 9480,
                "path": "2024/2024-03-09_Saudi_Arabian_Grand_Prix/2024-03-09_Race/",
            },
        ],
        1231: [
            {
                "session_key": 9481,
                "path": "2024/2024-03-24_Australian_Grand_Prix/2024-03-22_Practice_1/",
            },
            {
                "session_key": 9482,
                "path": "2024/2024-03-24_Australian_Grand_Prix/2024-03-22_Practice_2/",
            },
            {
                "session_key": 9483,
                "path": "2024/2024-03-24_Australian_Grand_Prix/2024-03-23_Practice_3/",
            },
            {
                "session_key": 9484,
                "path": "2024/2024-03-24_Australian_Grand_Prix/2024-03-23_Qualifying/",
            },
            {
                "session_key": 9488,
                "path": "2024/2024-03-24_Australian_Grand_Prix/2024-03-24_Race/",
            },
        ],
        1232: [
            {
                "session_key": 9489,
                "path": "2024/2024-04-07_Japanese_Grand_Prix/2024-04-05_Practice_1/",
            },
            {
                "session_key": 9490,
                "path": "2024/2024-04-07_Japanese_Grand_Prix/2024-04-05_Practice_2/",
            },
            {
                "session_key": 9491,
                "path": "2024/2024-04-07_Japanese_Grand_Prix/2024-04-06_Practice_3/",
            },
            {
                "session_key": 9492,
                "path": "2024/2024-04-07_Japanese_Grand_Prix/2024-04-06_Qualifying/",
            },
            {
                "session_key": 9496,
                "path": "2024/2024-04-07_Japanese_Grand_Prix/2024-04-07_Race/",
            },
        ],
        1233: [
            {
                "session_key": 9663,
                "path": "2024/2024-04-21_Chinese_Grand_Prix/2024-04-19_Practice_1/",
            },
            {
                "session_key": 9668,
                "path": "2024/2024-04-21_Chinese_Grand_Prix/2024-04-19_Sprint_Qualifying/",
            },
            {
                "session_key": 9672,
                "path": "2024/2024-04-21_Chinese_Grand_Prix/2024-04-20_Sprint/",
            },
            {
                "session_key": 9664,
                "path": "2024/2024-04-21_Chinese_Grand_Prix/2024-04-20_Qualifying/",
            },
            {
                "session_key": 9673,
                "path": "2024/2024-04-21_Chinese_Grand_Prix/2024-04-21_Race/",
            },
        ],
        1234: [
            {
                "session_key": 9497,
                "path": "2024/2024-05-05_Miami_Grand_Prix/2024-05-03_Practice_1/",
            },
            {
                "session_key": 9502,
                "path": "2024/2024-05-05_Miami_Grand_Prix/2024-05-03_Sprint_Qualifying/",
            },
            {
                "session_key": 9506,
                "path": "2024/2024-05-05_Miami_Grand_Prix/2024-05-04_Sprint/",
            },
            {
                "session_key": 9498,
                "path": "2024/2024-05-05_Miami_Grand_Prix/2024-05-04_Qualifying/",
            },
            {
                "session_key": 9507,
                "path": "2024/2024-05-05_Miami_Grand_Prix/2024-05-05_Race/",
            },
        ],
        1235: [
            {
                "session_key": 9508,
                "path": "2024/2024-05-19_Emilia_Romagna_Grand_Prix/2024-05-17_Practice_1/",
            },
            {
                "session_key": 9509,
                "path": "2024/2024-05-19_Emilia_Romagna_Grand_Prix/2024-05-17_Practice_2/",
            },
            {
                "session_key": 9510,
                "path": "2024/2024-05-19_Emilia_Romagna_Grand_Prix/2024-05-18_Practice_3/",
            },
            {
                "session_key": 9511,
                "path": "2024/2024-05-19_Emilia_Romagna_Grand_Prix/2024-05-18_Qualifying/",
            },
            {
                "session_key": 9515,
                "path": "2024/2024-05-19_Emilia_Romagna_Grand_Prix/2024-05-19_Race/",
            },
        ],
        1236: [
            {
                "session_key": 9516,
                "path": "2024/2024-05-26_Monaco_Grand_Prix/2024-05-24_Practice_1/",
            },
            {
                "session_key": 9517,
                "path": "2024/2024-05-26_Monaco_Grand_Prix/2024-05-24_Practice_2/",
            },
            {
                "session_key": 9518,
                "path": "2024/2024-05-26_Monaco_Grand_Prix/2024-05-25_Practice_3/",
            },
            {
                "session_key": 9519,
                "path": "2024/2024-05-26_Monaco_Grand_Prix/2024-05-25_Qualifying/",
            },
            {
                "session_key": 9523,
                "path": "2024/2024-05-26_Monaco_Grand_Prix/2024-05-26_Race/",
            },
        ],
        1237: [
            {
                "session_key": 9524,
                "path": "2024/2024-06-09_Canadian_Grand_Prix/2024-06-07_Practice_1/",
            },
            {
                "session_key": 9525,
                "path": "2024/2024-06-09_Canadian_Grand_Prix/2024-06-07_Practice_2/",
            },
            {
                "session_key": 9526,
                "path": "2024/2024-06-09_Canadian_Grand_Prix/2024-06-08_Practice_3/",
            },
            {
                "session_key": 9527,
                "path": "2024/2024-06-09_Canadian_Grand_Prix/2024-06-08_Qualifying/",
            },
            {
                "session_key": 9531,
                "path": "2024/2024-06-09_Canadian_Grand_Prix/2024-06-09_Race/",
            },
        ],
    }
}


@lru_cache()
def get_schedule(year: int) -> dict:
    """Fetches the Formula 1 race schedule for a specified year (past sessions only)"""
    BASE_URL = "https://livetiming.formula1.com/static"
    url = join_url(BASE_URL, f"{year}/Index.json")
    response = requests.get(url)
    content_json = response.content
    content_dict = json.loads(content_json)

    # Add missing sessions
    if year in MISSING_SESSIONS:
        for meeting_key, sessions in MISSING_SESSIONS[year].items():
            content_dict["Meetings"].append(
                {
                    "Key": meeting_key,
                    "Sessions": [
                        {"Key": s["session_key"], "Path": s["path"]} for s in sessions
                    ],
                }
            )

    # Sort results by meeting key
    content_dict["Meetings"] = sorted(content_dict["Meetings"], key=lambda x: x["Key"])

    return content_dict


def get_meeting_keys(year: int) -> list[int]:
    """Returns the keys of the meetings for a specific year (past meetings only)"""
    keys = [m["Key"] for m in get_schedule(year)["Meetings"]]
    return keys


def get_session_keys(year: int, meeting_key: int) -> list[int]:
    """Returns the keys of the sessions for a specific meeting (past sessions only)"""
    for meeting in get_schedule(year)["Meetings"]:
        if meeting["Key"] == meeting_key:
            session_keys = [e["Key"] for e in meeting["Sessions"] if e["Key"] != -1]
            return session_keys

    raise SystemError(
        f"Meeting not found (year: `{year}`, meeting_key: `{meeting_key}`)"
    )


def get_latest_meeting_key() -> int:
    return get_latest_session_info()["meeting_key"]


def get_latest_session_key() -> int:
    return get_latest_session_info()["session_key"]
