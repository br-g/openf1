"""Helper functions for parsing and transforming raw F1 data.

This module provides a collection of utility functions to decode, 
normalize, and prepare raw F1 data (either historical or real-time)
before indexing into MongoDB. This includes JSON decoding, data type casting,
key modifications, array exploding, and more.
"""

from typing import List, Dict, Iterator, Optional, Union, Any
import json
from functools import lru_cache
from collections import defaultdict
import base64
import zlib
from datetime import datetime
from util import to_datetime


def _decode(raw: str) -> Dict:
    """Decodes raw F1 data from either JSON or Base64 encoded compressed JSON"""
    try:
        return json.loads(raw.strip('"'))
    except:
        s = zlib.decompress(base64.b64decode(raw), -zlib.MAX_WBITS)
        return json.loads(s.decode('utf-8-sig'))


def _is_number(s: Any) -> bool:
    """Checks if the given argument can be converted to a float"""
    try:
        float(s)
        return True
    except ValueError:
        return False

@lru_cache(maxsize=None)
def _is_identifier(s: Any) -> bool:
    """Checks if the given argument is an identifier (a team name, a driver number, ...)"""
    TEAM_NAMES = {
        'Red Bull Racing Honda RBPT',
        'Mercedes',
        'Aston Martin Aramco Mercedes',
        'Ferrari',
        'Alpine Renault',
        'McLaren Mercedes',
        'Haas Ferrari',
        'Alfa Romeo Ferrari',
        'Williams Mercedes',
        'AlphaTauri Honda RBPT',
    }
    return (
        _is_number(s)
        or s in TEAM_NAMES
        or (len(s) >= 2 and s[0] == 'p' and s[1].isupper())
    )

def _add_key(obj: Any, key: Any) -> Any:
    """Utility function to store the key information from a flattened dict"""
    if isinstance(obj, dict):
        key_field = '_key'
        while key_field in set(obj.keys()):
            key_field = '_' + key_field
        obj[key_field] = key
        return obj
    elif isinstance(obj, list):
        return [_add_key(e, key=key) for e in obj]
    else:
        return {
            '_key': key,
            '_val': obj,
        }

def _remove_key_identifiers(obj: Any) -> Any:
    """Transforms `obj` such that there are no more identifiers (team name, driver number, ...)
       as dictionary keys. Such fields would be impossible to query in the database otherwise.
    """
    if isinstance(obj, dict):
        if any(_is_identifier(k) for k in obj):
            return [_add_key(_remove_key_identifiers(v), k) for k, v in obj.items()]
        else:
            return {k: _remove_key_identifiers(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_remove_key_identifiers(e) for e in obj]
    else:
        return obj


def _explode_arrays(collection_id: str, obj: Any,
                    attributes: Optional[Dict] = None) -> Union[Any, List[Any]]:
    """Transforms `obj` to remove arrays, because they could not be easily indexed
       and retrieved in the database.
    """
    if attributes is None:
        attributes = {}
    else:
        attributes = {f'{k}_': v for k, v in attributes.items()}

    if isinstance(obj, list):
        res = []
        for i, e in enumerate(obj):
            attributes['idx'] = i
            _exploded = _explode_arrays(collection_id, e, attributes=attributes)
            if not isinstance(_exploded, list):
                _exploded = [_exploded]
            for j, _ in enumerate(_exploded):
                _exploded[j] = (_exploded[j][0], {'_val': _exploded[j][1]})
                for k, v in attributes.items():
                    _exploded[j][1][f'_{k}'] = v
            res.extend(_exploded)
        return res

    elif isinstance(obj, dict):
        for k, v in obj.items():
            if not isinstance(v, list) and not isinstance(v, dict):
                attributes[k] = v

        exploded = []
        remaining = {}
        for k, v in obj.items():
            _exploded = _explode_arrays(f'{collection_id}-{k}', v, attributes=attributes)
            if isinstance(_exploded, list):
                exploded.extend(_exploded)
            else:
                remaining[k] = _exploded[1]
        
        if remaining and exploded:
            return [(collection_id, remaining)] + exploded
        elif not remaining and exploded:
            return exploded
        else:
            return (collection_id, remaining)

    else:
        return (collection_id, obj)


def _try_parse_date(s: str) -> Union[datetime, str]:
    """Turns `s` into a datetime object if possible"""
    time = to_datetime(s)
    return time if time is not None else s

def _try_parse_number(s: str) -> Union[int, float, str]:
    """Turns `s` into a number (int or float) if possible"""
    try:
        return int(s)
    except ValueError:
        try:
            return float(s)
        except ValueError:
            return s

def _try_parse_boolean(s: str):
    """Turns `s` into a boolean if possible"""
    if s.lower() == 'true':
        return True
    elif s.lower() == 'false':
        return False
    else:
        return s

@lru_cache(maxsize=None)
def _cast(s: str) -> Union[str, datetime, bool, int, float]:
    """Casts `s` to the most specific type possible (str, datetime, bool, int or float)"""
    s = _try_parse_date(s)
    if isinstance(s, datetime):
        return s
    s = _try_parse_boolean(s)
    if isinstance(s, bool):
        return s
    return _try_parse_number(s)

def cast(obj: Any) -> Any:
    """Casts `obj` to the most specific type possible, recursively"""
    if isinstance(obj, str):
        return _cast(obj)
    elif isinstance(obj, dict):
        return {k: cast(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [cast(e) for e in obj]
    else:
        return obj


def _flatten_list(obj: Any) -> Iterator[Any]:
    if isinstance(obj, list):
        for e in obj:
            yield from _flatten_list(e)
    else:
        yield obj


def _apply_custom_transformations(topic: str, data: Dict) -> None:
    """Transforms some raw data for storage optimization"""
    if topic == 'CarData.z':  # This topic has a very large memory footprint in the database
        for elem in data:
            for entry in elem['Entries']:
                new_cars = []
                for old_car in entry['Cars']:
                    new_car = {k: v for k, v in old_car.items() if k != 'Channels'}
                    for channel in old_car['Channels']:
                        new_car[f'ch_{channel["_key"]}'] = channel['_val']
                    new_cars.append(new_car)
                
                entry['Cars'] = new_cars


def parse_line(topic: str, content: str, session_key: str, meeting_key: str, time: datetime,
               session_time: Optional[float] = None) -> Dict[str, Dict]:
    """Parses a single raw line of F1 data.

    This function decodes and transforms a raw F1 data line into a more
    structured and usable format for indexing into MongoDB.
    """
    decoded = _decode(content) if isinstance(content, str) else content
    flattened = list(_flatten_list(_remove_key_identifiers(decoded)))

    _apply_custom_transformations(topic=topic, data=flattened)

    parsed = defaultdict(list)
    for content in flattened:
        # Explode
        exploded = _explode_arrays(topic, content)
        if not isinstance(exploded, list):
            exploded = [exploded]

        for collection_id, data in exploded:
            if not data:
                continue
            data = cast(data)

            # Add metadata
            data['_time'] = time
            data['_session_key'] = session_key
            data['_meeting_key'] = meeting_key
            if session_time:
                data['_session_time'] = session_time

            parsed[collection_id].append(data)

    return dict(parsed)
