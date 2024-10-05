from datetime import datetime
from functools import lru_cache
from typing import Any

from dateutil.parser import parse as parse_date
from dateutil.tz import tzutc


def _try_parse_date(s: str) -> datetime | str:
    """Attempts to convert a string to a datetime object"""
    try:
        dt = parse_date(s)
    except:
        return s

    if dt.tzinfo is None or dt.tzinfo.utcoffset(dt) is None:
        dt = dt.replace(tzinfo=tzutc())
    else:
        dt = dt.astimezone(tzutc())
    return dt


def _try_parse_number(s: str) -> int | float | str:
    """Attempts to convert a string to an integer or float"""
    try:
        return int(s)
    except ValueError:
        try:
            return float(s)
        except ValueError:
            return s


def _try_parse_boolean(s: str) -> bool | str:
    """Attempts to convert a string to a boolean value"""
    if s.lower() == "true":
        return True
    elif s.lower() == "false":
        return False
    else:
        return s


@lru_cache(maxsize=2048)
def _cast(s: str) -> str | datetime | bool | int | float:
    """Casts a string to the most specific native type possible"""
    s = _try_parse_boolean(s)
    if isinstance(s, bool):
        return s

    s = _try_parse_number(s)
    if isinstance(s, int) or isinstance(s, float):
        return s

    s = _try_parse_date(s)
    return s


def cast(obj: Any) -> Any:
    """Recursively casts an object to the most specific type possible"""
    if isinstance(obj, str):
        return _cast(obj)
    elif isinstance(obj, dict):
        return {k: cast(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [cast(e) for e in obj]
    else:
        return obj
