from datetime import datetime, timezone

from openf1.util.db import (
    MongoOp,
    MongoPredicate,
    _get_inequality_predicate_pairs,
)


def test_get_inequality_predicate_pairs_empty_predicates():
    """Empty predicates."""
    predicates = []
    expected = ([], [])
    actual = _get_inequality_predicate_pairs(predicates)
    assert actual == expected


def test_get_inequality_predicate_pairs_single_predicate():
    """Single predicate."""
    predicates = [MongoPredicate(op=MongoOp.LT, value=5)]
    expected = ([], [MongoPredicate(op=MongoOp.LT, value=5)])
    actual = _get_inequality_predicate_pairs(predicates)
    assert actual == expected


def test_get_inequality_predicate_pairs_unbounded():
    """Unbounded predicate pair."""
    predicates = [
        MongoPredicate(op=MongoOp.GT, value=10),
        MongoPredicate(op=MongoOp.LT, value=5),
    ]
    expected = (
        [],
        [
            MongoPredicate(op=MongoOp.GT, value=10),
            MongoPredicate(op=MongoOp.LT, value=5),
        ],
    )
    actual = _get_inequality_predicate_pairs(predicates)
    assert actual == expected


def test_get_inequality_predicate_pairs_bounded_pairs():
    """Bounded pair."""
    predicates = [
        MongoPredicate(op=MongoOp.LT, value=10),
        MongoPredicate(op=MongoOp.GT, value=5),
    ]
    expected = (
        [
            (
                MongoPredicate(op=MongoOp.GT, value=5),
                MongoPredicate(op=MongoOp.LT, value=10),
            )
        ],
        [],
    )
    actual = _get_inequality_predicate_pairs(predicates)
    assert actual == expected


def test_get_inequality_predicate_pairs_multiple_bounded_pairs():
    """Multiple bounded pairs."""
    predicates = [
        MongoPredicate(op=MongoOp.GT, value=6),
        MongoPredicate(op=MongoOp.GT, value=1),
        MongoPredicate(op=MongoOp.LT, value=9),
        MongoPredicate(op=MongoOp.LT, value=4),
    ]
    expected = (
        [
            (
                MongoPredicate(op=MongoOp.GT, value=1),
                MongoPredicate(op=MongoOp.LT, value=4),
            ),
            (
                MongoPredicate(op=MongoOp.GT, value=6),
                MongoPredicate(op=MongoOp.LT, value=9),
            ),
        ],
        [],
    )
    actual = _get_inequality_predicate_pairs(predicates)
    assert actual == expected


def test_get_inequality_predicate_pairs_single_value_bounded_pair():
    """Single-value bounded pair."""
    predicates = [
        MongoPredicate(op=MongoOp.GTE, value=5),
        MongoPredicate(op=MongoOp.LTE, value=5),
    ]
    expected = (
        [
            (
                MongoPredicate(op=MongoOp.GTE, value=5),
                MongoPredicate(op=MongoOp.LTE, value=5),
            )
        ],
        [],
    )
    actual = _get_inequality_predicate_pairs(predicates)
    assert actual == expected


def test_get_inequality_predicate_pairs_ignore_unpaired():
    """Ignore unpaired predicates."""
    predicates = [
        MongoPredicate(op=MongoOp.GT, value=5),
        MongoPredicate(op=MongoOp.LT, value=10),
        MongoPredicate(op=MongoOp.LT, value=12),
    ]
    expected = (
        [
            (
                MongoPredicate(op=MongoOp.GT, value=5),
                MongoPredicate(op=MongoOp.LT, value=10),
            )
        ],
        [MongoPredicate(op=MongoOp.LT, value=12)],
    )
    actual = _get_inequality_predicate_pairs(predicates)
    assert actual == expected


def test_get_inequality_predicate_pairs_overlapping_pairs():
    """Overlapping pairs should be merged."""
    predicates = [
        MongoPredicate(op=MongoOp.GT, value=5),
        MongoPredicate(op=MongoOp.LT, value=10),
        MongoPredicate(op=MongoOp.GT, value=8),
        MongoPredicate(op=MongoOp.LT, value=12),
    ]
    expected = (
        [
            (
                MongoPredicate(op=MongoOp.GT, value=5),
                MongoPredicate(op=MongoOp.LT, value=12),
            )
        ],
        [],
    )
    actual = _get_inequality_predicate_pairs(predicates)
    assert actual == expected


def test_get_inequality_predicate_pairs_non_strict_inequality_boundary():
    """Pairs with non-strict inequalities where one pair's upper bound is equal to the other pair's lower bound should be merged."""
    predicates = [
        MongoPredicate(op=MongoOp.GTE, value=4),
        MongoPredicate(op=MongoOp.LTE, value=7),
        MongoPredicate(op=MongoOp.GTE, value=7),
        MongoPredicate(op=MongoOp.LTE, value=10),
    ]
    expected = (
        [
            (
                MongoPredicate(op=MongoOp.GTE, value=4),
                MongoPredicate(op=MongoOp.LTE, value=10),
            )
        ],
        [],
    )
    actual = _get_inequality_predicate_pairs(predicates)
    assert actual == expected


def test_get_inequality_predicate_pairs_integer_adjacency():
    """Integer pairs where one pair's upper bound is one less than the other pair's lower bound should be merged."""
    predicates = [
        MongoPredicate(op=MongoOp.GTE, value=4),
        MongoPredicate(op=MongoOp.LTE, value=7),
        MongoPredicate(op=MongoOp.GTE, value=8),
        MongoPredicate(op=MongoOp.LTE, value=10),
    ]
    expected = (
        [
            (
                MongoPredicate(op=MongoOp.GTE, value=4),
                MongoPredicate(op=MongoOp.LTE, value=10),
            )
        ],
        [],
    )
    actual = _get_inequality_predicate_pairs(predicates)
    assert actual == expected


def test_get_inequality_predicate_pairs_strict_inequality_boundary():
    """Pairs with strict inequalities where one pair's upper bound is equal to the other pair's lower bound should not be merged."""
    predicates = [
        MongoPredicate(op=MongoOp.GT, value=1),
        MongoPredicate(op=MongoOp.LT, value=5),
        MongoPredicate(op=MongoOp.GT, value=5),
        MongoPredicate(op=MongoOp.LT, value=8),
    ]
    expected = (
        [
            (
                MongoPredicate(op=MongoOp.GT, value=1),
                MongoPredicate(op=MongoOp.LT, value=5),
            ),
            (
                MongoPredicate(op=MongoOp.GT, value=5),
                MongoPredicate(op=MongoOp.LT, value=8),
            ),
        ],
        [],
    )
    actual = _get_inequality_predicate_pairs(predicates)
    assert actual == expected


def test_get_inequality_predicate_pairs_float_values():
    """Float values are supported."""
    predicates = [
        MongoPredicate(op=MongoOp.GT, value=1.5),
        MongoPredicate(op=MongoOp.LT, value=2.5),
        MongoPredicate(op=MongoOp.GT, value=2.0),
        MongoPredicate(op=MongoOp.LT, value=3.5),
    ]
    expected = (
        [
            (
                MongoPredicate(op=MongoOp.GT, value=1.5),
                MongoPredicate(op=MongoOp.LT, value=3.5),
            )
        ],
        [],
    )
    actual = _get_inequality_predicate_pairs(predicates)
    assert actual == expected


def test_get_inequality_predicate_pairs_datetime_values():
    """Datetime values are supported."""
    dt1 = datetime(2026, 4, 12, 10, 0, tzinfo=timezone.utc)
    dt2 = datetime(2026, 4, 12, 11, 0, tzinfo=timezone.utc)
    dt3 = datetime(2026, 4, 12, 10, 30, tzinfo=timezone.utc)
    dt4 = datetime(2026, 4, 12, 12, 0, tzinfo=timezone.utc)

    predicates = [
        MongoPredicate(op=MongoOp.GTE, value=dt1),
        MongoPredicate(op=MongoOp.LTE, value=dt2),
        MongoPredicate(op=MongoOp.GTE, value=dt3),
        MongoPredicate(op=MongoOp.LTE, value=dt4),
    ]
    expected = (
        [
            (
                MongoPredicate(op=MongoOp.GTE, value=dt1),
                MongoPredicate(op=MongoOp.LTE, value=dt4),
            )
        ],
        [],
    )
    actual = _get_inequality_predicate_pairs(predicates)
    assert actual == expected
