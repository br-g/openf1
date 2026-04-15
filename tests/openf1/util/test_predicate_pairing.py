import pytest

from datetime import datetime, timezone
from typing import Any

from openf1.util.db import (
    MongoOp,
    MongoPredicate,
    _get_bounded_inequality_predicate_pairs,
)


# MongoDB query predicate helper
def _p(op: MongoOp, value: Any) -> MongoPredicate:
    return MongoPredicate(op=op, value=value)


@pytest.mark.parametrize(
    "predicates, expected",
    [
        # Empty/unbounded/non-inequality op
        ([], []),
        ([_p(MongoOp.EQ, 5)], []),
        ([_p(MongoOp.GT, 5)], []),
        ([_p(MongoOp.LT, 5)], []),
        ([_p(MongoOp.GT, 10), _p(MongoOp.LT, 5)], []),
        # Bounded pairs (unordered)
        (
            [_p(MongoOp.LT, 10), _p(MongoOp.GT, 5)],
            [(_p(MongoOp.GT, 5), _p(MongoOp.LT, 10))],
        ),
        (
            [
                _p(MongoOp.GT, 6),
                _p(MongoOp.GT, 1),
                _p(MongoOp.LT, 9),
                _p(MongoOp.LT, 4),
            ],
            [
                (_p(MongoOp.GT, 1), _p(MongoOp.LT, 4)),
                (_p(MongoOp.GT, 6), _p(MongoOp.LT, 9)),
            ],
        ),
        # Single-value bounded pair
        (
            [_p(MongoOp.GTE, 5), _p(MongoOp.LTE, 5)],
            [(_p(MongoOp.GTE, 5), _p(MongoOp.LTE, 5))],
        ),
        # Bounded pairs ignoring unpaired predicates
        (
            [_p(MongoOp.GT, 5), _p(MongoOp.LT, 10), _p(MongoOp.LT, 12)],
            [(_p(MongoOp.GT, 5), _p(MongoOp.LT, 10))],
        ),
        (
            [_p(MongoOp.GT, 5), _p(MongoOp.LT, 3), _p(MongoOp.LT, 10)],
            [(_p(MongoOp.GT, 5), _p(MongoOp.LT, 10))],
        ),
        # Overlapping pairs
        (
            [
                _p(MongoOp.GT, 5),
                _p(MongoOp.LT, 10),
                _p(MongoOp.GT, 8),
                _p(MongoOp.LT, 12),
            ],
            [(_p(MongoOp.GT, 5), _p(MongoOp.LT, 12))],
        ),
        # Overlapping pairs, boundary case
        (
            [
                _p(MongoOp.GTE, 4),
                _p(MongoOp.LTE, 7),
                _p(MongoOp.GTE, 7),
                _p(MongoOp.LTE, 10),
            ],
            [(_p(MongoOp.GTE, 4), _p(MongoOp.LTE, 10))],
        ),
        # Overlapping pairs, integer adjacency
        (
            [
                _p(MongoOp.GTE, 4),
                _p(MongoOp.LTE, 7),
                _p(MongoOp.GTE, 8),
                _p(MongoOp.LTE, 10),
            ],
            [(_p(MongoOp.GTE, 4), _p(MongoOp.LTE, 10))],
        ),
        # Non-overlapping pairs, boundary case
        (
            [
                _p(MongoOp.GT, 1),
                _p(MongoOp.LT, 5),
                _p(MongoOp.GT, 5),
                _p(MongoOp.LT, 8),
            ],
            [
                (_p(MongoOp.GT, 1), _p(MongoOp.LT, 5)),
                (_p(MongoOp.GT, 5), _p(MongoOp.LT, 8)),
            ],
        ),
        # Float
        (
            [
                _p(MongoOp.GT, 1.5),
                _p(MongoOp.LT, 2.5),
                _p(MongoOp.GT, 2.0),
                _p(MongoOp.LT, 3.5),
            ],
            [(_p(MongoOp.GT, 1.5), _p(MongoOp.LT, 3.5))],
        ),
        # Datetime
        (
            [
                _p(MongoOp.GTE, datetime(2026, 4, 12, 10, 0, tzinfo=timezone.utc)),
                _p(MongoOp.LTE, datetime(2026, 4, 12, 11, 0, tzinfo=timezone.utc)),
                _p(MongoOp.GTE, datetime(2026, 4, 12, 10, 30, tzinfo=timezone.utc)),
                _p(MongoOp.LTE, datetime(2026, 4, 12, 12, 0, tzinfo=timezone.utc)),
            ],
            [
                (
                    _p(MongoOp.GTE, datetime(2026, 4, 12, 10, 0, tzinfo=timezone.utc)),
                    _p(MongoOp.LTE, datetime(2026, 4, 12, 12, 0, tzinfo=timezone.utc)),
                )
            ],
        ),
    ],
)
def test_predicate_pairing(predicates, expected):
    actual = _get_bounded_inequality_predicate_pairs(predicates)
    assert actual == expected
