"""
Test each API method individually using the `example_filters` and `example_response` provided.
To run this test from the `query_api` directory: `pytest tests/integration.py`.
"""

from typing import List, Dict
import sys
from pathlib import Path
from datetime import datetime
import pytest

sys.path.append('.')
from util import get_api_methods
from filters import parse_query_filters

_METHODS_DIR = Path('./methods')


def _datetimes_to_iso(list_of_dicts: List[Dict]):
    # Convert all datetime objects to ISO format
    for dct in list_of_dicts:
        for key, value in dct.items():
            if isinstance(value, datetime):
                dct[key] = value.isoformat()


_all_methods = list(get_api_methods(_METHODS_DIR))

@pytest.mark.parametrize('url, method', _all_methods)
def test_api_method(url, method):
    print(f'Testing method: `{url}`')
    filters = parse_query_filters(method.example_filters)
    res = list(method.query_process_filter(filters))
    _datetimes_to_iso(res)
    assert res == method.example_response
