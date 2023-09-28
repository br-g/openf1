from typing import Dict, List, Tuple, Iterator, Callable, Any, Union, Optional
from functools import wraps
import sys
import time
from collections import defaultdict
import importlib
from datetime import datetime, timedelta
from pathlib import Path
from dateutil.parser import parse
from dateutil.tz import tzutc
import pytz


def parse_date(date_string: str) -> datetime:
    dt = parse(date_string)
    if dt.tzinfo is None or dt.tzinfo.utcoffset(dt) is None:
        dt = dt.replace(tzinfo=tzutc())
    else:
        dt = dt.astimezone(tzutc())
    return dt


def do_try(fn: Callable, *args, **kwargs) -> Any:
    try:
        return fn(*args, **kwargs)
    except:
        return None


def add_timezone_info(dt: datetime, gmt_offset: str) -> datetime:
    h, _, _ = map(int, gmt_offset.split(':'))
    offset_tz = pytz.FixedOffset(h * 60)
    return dt.replace(tzinfo=offset_tz).astimezone(tzutc())


def to_timedelta(x: Union[str, timedelta]) \
        -> Optional[timedelta]:
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
            if len(hms := x.split(':')) == 3:
                hours, minutes, seconds = hms
            elif len(hms) == 2:
                minutes, seconds = hms
            else:
                seconds = hms[0]

            if '.' in seconds:
                seconds, msus = seconds.split('.')
                if len(msus) < 6:
                    msus = msus + '0' * (6 - len(msus))
                elif len(msus) > 6:
                    msus = msus[0:6]
            else:
                msus = 0

            return timedelta(
                hours=int(hours), minutes=int(minutes),
                seconds=int(seconds), microseconds=int(msus)
            )

        except Exception as exc:
            print(f"Failed to parse timedelta string '{x}'",
                          exc_info=exc)
            return None

    elif isinstance(x, timedelta):
        return x

    else:
        return None


def group_dicts_by(dicts: List[Dict], attributes: List[str]) -> Dict[Tuple, List[Dict]]:
    """Groups dicts by a set of attributes"""
    assert attributes
    res = defaultdict(list)
    for dic in dicts:
        if any(e not in dic for e in attributes):
            continue
        key = tuple([dic[e] for e in attributes]) if len(attributes) > 1 else dic[attributes[0]]
        res[key].append(dic)
    return dict(res)


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


def has_time_info(date_str: str) -> bool:
    """Returns whether the date string has time info.
       eg.
           - "2021-09-10" -> False
           - "2021-09-10T14:30:20" -> True
    """
    # Parse the string with the first default datetime
    default_datetime1 = datetime(1, 1, 1, 5, 0)  # 5:00
    dt1 = parse(date_str, default=default_datetime1)
    
    # Parse the string with the second default datetime
    default_datetime2 = datetime(1, 1, 1, 10, 0)  # 10:00
    dt2 = parse(date_str, default=default_datetime2)
    
    # Check if hours and minutes are the same
    return dt1.hour == dt2.hour


def _try_parse_boolean(s: str) -> Union[bool, str]:
    """Casts to boolean if possible"""
    if s.lower() == 'true':
        return True
    elif s.lower() == 'false':
        return False
    else:
        return s

def _try_parse_number(s: str) -> Union[int, float, str]:
    """Casts to int or float if possible"""
    try:
        return int(s)
    except ValueError:
        try:
            return float(s)
        except ValueError:
            return s

def _try_parse_date(s: str) -> Union[datetime, str]:
    """Casts to datetime if possible"""
    try:
        return parse_date(s)
    except:
        return s

def try_cast(obj: Any) -> Any:
    """Casts to boolean, float or datetime if possible"""
    if isinstance(obj, str):
        obj = _try_parse_boolean(obj)
        if not isinstance(obj, str):
            return obj
        obj = _try_parse_number(obj)
        if not isinstance(obj, str):
            return obj
        return _try_parse_date(obj)
    else:
        return obj


def _get_python_filepaths(base_dir: Path) -> Iterator[Path]:
    """Yields Python files from a given directory (and nested sub-directories)"""
    for path in base_dir.iterdir():
        if path.name[0] == '_':
            continue
        if path.is_dir():
            yield from _get_python_filepaths(path)
        elif path.suffix == '.py':
            yield path

def _get_classes_from_file(filepath: Path) -> Iterator[type]:
    """Yields classes from a Python file"""
    spec = importlib.util.spec_from_file_location(filepath.stem, filepath)
    module = importlib.util.module_from_spec(spec)
    
    sys.modules[filepath.stem] = module
    spec.loader.exec_module(module)

    for obj in vars(module).values():
        if isinstance(obj, type):
            yield obj

def get_api_methods(base_dir: Path) -> Iterator[Tuple[str, 'BaseMethod']]:
    """Yields the API methods (URL and class)"""
    # Prevent circular import
    from base_method import BaseMethod

    for filepath in _get_python_filepaths(base_dir):
        classes = [e for e in _get_classes_from_file(filepath)
                   if issubclass(e, BaseMethod) and e != BaseMethod]
        assert len(classes) <= 1, classes
        if classes:
            filepath = filepath.relative_to(base_dir)
            yield str(filepath.parent / filepath.stem), classes[0]


def deduplicate_dicts(dicts: List[Dict]) -> List[Dict]:
    seen = set()
    res = []
    for d in dicts:
        t = tuple(sorted(d.items()))
        if t not in seen:
            seen.add(t)
            res.append(d)
    return res
