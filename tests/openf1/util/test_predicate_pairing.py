import pytest

from datetime import datetime, timezone
from typing import Any

from openf1.util.db import _get_bounded_inequality_predicate_pairs


def _p(op: str, value: Any):
    return {op: value}


@pytest.mark.parametrize(
    "predicates, expected",
    [
        # Empty/unbounded/non-inequality op
        ([], []),
        ([_p("$eq", 5)], []),
        ([_p("$gt", 5)], []),
        ([_p("$lt", 5)], []),
        ([_p("$gt", 10), _p("$lt", 5)], []),

        # Bounded pairs (unordered)
        (
            [_p("$lt", 10), _p("$gt", 5)],
            [(_p("$gt", 5), _p("$lt", 10))],
        ),
        (
            [_p("$gt", 6), _p("$gt", 1), _p("$lt", 9), _p("$lt", 4)],
            [(_p("$gt", 1), _p("$lt", 4)), (_p("$gt", 6), _p("$lt", 9))],
        ),
        # Single-value bounded pair
        (
            [_p("$gte", 5), _p("$lte", 5)],
            [(_p("$gte", 5), _p("$lte", 5))],  
        ),

        # Bounded pairs ignoring unpaired predicates
        (
            [_p("$gt", 5), _p("$lt", 10), _p("$lt", 12)],
            [(_p("$gt", 5), _p("$lt", 10))],
        ),
        (
            [_p("$gt", 5), _p("$lt", 3), _p("$lt", 10)],
            [(_p("$gt", 5), _p("$lt", 10))],
        ),

        # Overlapping pairs
        (
            [_p("$gt", 5), _p("$lt", 10), _p("$gt", 8), _p("$lt", 12)],
            [(_p("$gt", 5), _p("$lt", 12))],
        ),

        # Overlapping pairs, boundary case
        (
            [_p("$gte", 4), _p("$lte", 7), _p("$gte", 7), _p("$lte", 10)],
            [(_p("$gte", 4), _p("$lte", 10))],
        ),

        # Overlapping pairs, integer adjacency
        (
            [_p("$gte", 4), _p("$lte", 7), _p("$gte", 8), _p("$lte", 10)],
            [(_p("$gte", 4), _p("$lte", 10))],
        ),

        # Non-overlapping pairs, boundary case
        (
            [_p("$gt", 1), _p("$lt", 5), _p("$gt", 5), _p("$lt", 8)],
            [(_p("$gt", 1), _p("$lt", 5)), (_p("$gt", 5), _p("$lt", 8))],
        ),

        # Float
        (
            [_p("$gt", 1.5), _p("$lt", 2.5), _p("$gt", 2.0), _p("$lt", 3.5)],
            [(_p("$gt", 1.5), _p("$lt", 3.5))],
        ),

        # Datetime
        (
            [
                _p("$gte", datetime(2026, 4, 12, 10, 0, tzinfo=timezone.utc)),
                _p("$lte", datetime(2026, 4, 12, 11, 0, tzinfo=timezone.utc)),
                _p("$gte", datetime(2026, 4, 12, 10, 30, tzinfo=timezone.utc)),
                _p("$lte", datetime(2026, 4, 12, 12, 0, tzinfo=timezone.utc)),
            ],
            [
                (
                    _p("$gte", datetime(2026, 4, 12, 10, 0, tzinfo=timezone.utc)),
                    _p("$lte", datetime(2026, 4, 12, 12, 0, tzinfo=timezone.utc)),
                )
            ],
        ),
    ],
)
def test_predicate_pairing(predicates, expected):
    actual = _get_bounded_inequality_predicate_pairs(predicates)
    assert actual == expected