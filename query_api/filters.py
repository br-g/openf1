"""Helper functions and assets to filter results based on parameters provided by
   the user in the URL.
"""

from typing import Dict, List, Iterator, Optional
import operator
from datetime import datetime, timedelta
from collections import defaultdict
from util import has_time_info, try_cast


# Operators allowed in the URL to filter results
OPERATORS_MAP = {
    '>=': {
        'mongo': '$gte',
        'python': operator.ge,
    },
    '<=': {
        'mongo': '$lte',
        'python': operator.le,
    },
    '=': {
        'mongo': '$eq',
        'python': operator.eq,
    },
    '>': {
        'mongo': '$gt',
        'python': operator.gt,
    },
    '<': {
        'mongo': '$lt',
        'python': operator.lt,
    },
}


def _adjust_time(filter_: Dict) -> Iterator[Dict]:
    """Adjusts time filter when time info is not specified, to keep things consistent"""
    if filter_['op'] == '>':
        yield {
            'left': filter_['left'],
            'op': '>=',
            'right': filter_['right'] + timedelta(days=1),
        }
    if filter_['op'] == '<':
        yield filter_
    if filter_['op'] in {'=', '>='}:
        yield {
            'left': filter_['left'],
            'op': '>=',
            'right': filter_['right'],
        }
    if filter_['op'] in {'=', '<='}:
        yield {
            'left': filter_['left'],
            'op': '<',
            'right': filter_['right'] + timedelta(days=1),
        }


def _parse_query_filter(filter_: str) -> Iterator[Dict]:
    """Splits the filter into 3 parts: 'left', 'op' and 'right'"""
    # Prevent circular import
    from db import get_latest_meeting_key, get_latest_session_key

    for op in OPERATORS_MAP:
        if op in filter_:
            loc = filter_.find(op)
            parsed = {
                'left': filter_[:loc].lower(),
                'op': op,
                'right': filter_[loc+len(op):],
            }
            assert parsed['right'], f'Invalid query filter: `{filter_}`.'
            _right = parsed['right']
            parsed['right'] = try_cast(parsed['right'])

            # Handle value `latest` for meeting_key and session_key attributes
            if parsed['left'] == 'meeting_key' and parsed['right'] == 'latest':
                parsed['right'] = get_latest_meeting_key()
            if parsed['left'] == 'session_key' and parsed['right'] == 'latest':
                parsed['right'] = get_latest_session_key()

            # Handle time filters without time info
            if isinstance(parsed['right'], datetime) and not has_time_info(_right):
                yield from _adjust_time(parsed)
            else:
                yield parsed
            return

    raise ValueError(f'Operator not found in `{filter_}`.')

def parse_query_filters(filters: List[str]) -> Dict:
    """Parses each filter and groups them by attribute"""
    res = defaultdict(list)
    for filter_ in filters:
        for r in _parse_query_filter(filter_=filter_):
            res[r['left']].append({'op': r['op'], 'right': r['right']})
    return dict(res)


def _should_be_filtered(result: Dict, filters: Dict[str, List[Dict]]) -> Optional[Dict]:
    """Returns whether the `result` should be filtered out according to the `filters`"""
    for key, filters in filters.items():
        if result[key] is None:
            return True
        for filter_ in filters:
            if not OPERATORS_MAP[filter_['op']]['python'](result[key], filter_['right']):
                return True
    return False

def filter_results(results: List[Dict], filters: Dict[str, List[Dict]]) -> List[Dict]:
    """Filters `results` based on the provided `filters`"""
    return [e for e in results if not _should_be_filtered(e, filters)]
