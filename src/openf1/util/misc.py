import json
import time
from datetime import datetime, timedelta
from enum import Enum
from functools import wraps
from threading import Lock
from typing import Callable

import pytz
from dateutil.tz import tzutc


def join_url(*args) -> str:
    """Join URL parts with a forward slash"""
    if any(len(e) == 0 or e is None for e in args):
        raise ValueError(f"Invalid URL components: {args}")
    return "/".join([e.strip("/") for e in args])

def timed_cache(expiration_time: float) -> Callable:
    """A decorator to cache the function output for a given duration.
    `expiration_time` is in seconds.
    """
    cache = {}
    timestamps = {}

    def decorator(func):

        @wraps(func)
        def wrapper(*args, **kwargs):
            # Convert the arguments and keyword arguments to a single hashable key
            key = (args, frozenset(kwargs.items()))

            # Check if value is in cache and not expired
            if key in cache:
                if time.time() - timestamps[key] < expiration_time:
                    return cache[key]
                else:
                    # Remove the expired data
                    del cache[key]
                    del timestamps[key]

            # Compute the result and cache it
            result = func(*args, **kwargs)
            cache[key] = result
            timestamps[key] = time.time()

            return result

        return wrapper

    return decorator


def json_serializer(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, Enum):
        return str(obj)
    elif isinstance(obj, object):
        return obj.__dict__
    raise TypeError(f"Type {type(obj)} not serializable")


def deduplicate_dicts(dicts: list[dict]) -> list[dict]:
    if len(dicts) <= 1:
        return dicts

    seen = set()
    res = []
    for d in dicts:
        d_json = json.dumps(d, default=json_serializer)
        if d_json not in seen:
            seen.add(d_json)
            res.append(d)
    return res


class SingletonMeta(type):
    """Thread-safe metaclass to create singleton classes"""

    _instances = {}

    _lock: Lock = Lock()

    def __call__(cls, *args, **kwargs):
        # Synchronize access to instance
        with cls._lock:
            if cls not in cls._instances:
                instance = super().__call__(*args, **kwargs)
                cls._instances[cls] = instance
        return cls._instances[cls]


def to_datetime(x: str | datetime) -> datetime | None:
    """This function is taken from FastF1: https://github.com/theOehrly/Fast-F1/blob/317bacf8c61038d7e8d0f48165330167702b349f/fastf1/utils.py#L178

    Fast datetime object creation from a date string.

    Permissible string formats:

        For example '2020-12-13T13:27:15.320000Z' with:

            - optional milliseconds and microseconds with
              arbitrary precision (1 to 6 digits)
            - with optional trailing letter 'Z'

        Examples of valid formats:

            - `2020-12-13T13:27:15.320000`
            - `2020-12-13T13:27:15.32Z`
            - `2020-12-13T13:27:15`

    Args:
        x: timestamp
    """
    if isinstance(x, str):
        try:
            date, time = x.strip("Z").split("T")
            year, month, day = date.split("-")
            hours, minutes, seconds = time.split(":")
            if "." in seconds:
                seconds, msus = seconds.split(".")
                if len(msus) < 6:
                    msus = msus + "0" * (6 - len(msus))
                elif len(msus) > 6:
                    msus = msus[0:6]
            else:
                msus = 0

            return datetime(
                int(year),
                int(month),
                int(day),
                int(hours),
                int(minutes),
                int(seconds),
                int(msus),
            )

        except Exception as exc:
            return None

    elif isinstance(x, datetime):
        return x

    else:
        return None


def to_timedelta(x: str | timedelta) -> timedelta | None:
    """This function is taken from FastF1: https://github.com/theOehrly/Fast-F1/blob/317bacf8c61038d7e8d0f48165330167702b349f/fastf1/utils.py#L120

    Fast timedelta object creation from a time string

    Permissible string formats:

        For example: `13:24:46.320215` with:

            - optional hours and minutes
            - optional microseconds and milliseconds with
              arbitrary precision (1 to 6 digits)

        Examples of valid formats:

            - `24.3564` (seconds + milli/microseconds)
            - `36:54` (minutes + seconds)
            - `8:45:46` (hours, minutes, seconds)

    Args:
        x: timestamp
    """
    # this is faster than using pd.timedelta on a string
    if isinstance(x, str) and len(x):
        try:
            hours, minutes = 0, 0
            hms = x.split(":")
            if len(hms) == 3:
                hours, minutes, seconds = hms
            elif len(hms) == 2:
                minutes, seconds = hms
            else:
                seconds = hms[0]

            if "." in seconds:
                seconds, msus = seconds.split(".")
                if len(msus) < 6:
                    msus = msus + "0" * (6 - len(msus))
                elif len(msus) > 6:
                    msus = msus[0:6]
            else:
                msus = 0

            return timedelta(
                hours=int(hours),
                minutes=int(minutes),
                seconds=int(seconds),
                microseconds=int(msus),
            )

        except Exception as exc:
            print(f"Failed to parse timedelta string '{x}'", exc_info=exc)
            return None

    elif isinstance(x, timedelta):
        return x

    else:
        return None


def add_timezone_info(dt: datetime, gmt_offset: str) -> datetime:
    h, _, _ = map(int, gmt_offset.split(":"))
    offset_tz = pytz.FixedOffset(h * 60)
    return dt.replace(tzinfo=offset_tz).astimezone(tzutc())
