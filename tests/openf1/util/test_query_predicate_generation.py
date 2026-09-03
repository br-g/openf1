from openf1.util.db import (
    MongoOp,
    MongoPredicate,
    _generate_query_predicate,
)


def test_generate_query_predicate_empty_filters():
    """Empty filters."""
    filters = {}
    expected = {}
    result = _generate_query_predicate(filters)
    assert result == expected


def test_generate_query_predicate_equality_predicates():
    """Single field with multiple equality predicates."""
    filters = {
        "position": [
            MongoPredicate(op=MongoOp.EQ, value=1),
            MongoPredicate(op=MongoOp.EQ, value=3),
        ]
    }
    expected = {
        MongoOp.AND: [
            {
                MongoOp.OR: [
                    {
                        MongoOp.OR: [
                            {"position": {MongoOp.EQ: 1}},
                            {"position": {MongoOp.EQ: 3}},
                        ]
                    }
                ]
            }
        ]
    }
    result = _generate_query_predicate(filters)
    assert result == expected


def test_generate_query_predicate_bounded_inequality_predicates():
    """Single field with bounded inequality predicates."""
    filters = {
        "position": [
            MongoPredicate(op=MongoOp.GTE, value=4),
            MongoPredicate(op=MongoOp.LTE, value=7),
        ]
    }
    expected = {
        MongoOp.AND: [
            {
                MongoOp.OR: [
                    {
                        MongoOp.OR: [
                            {
                                MongoOp.AND: [
                                    {"position": {MongoOp.GTE: 4}},
                                    {"position": {MongoOp.LTE: 7}},
                                ]
                            }
                        ]
                    }
                ]
            }
        ]
    }
    result = _generate_query_predicate(filters)
    assert result == expected


def test_generate_query_predicate_unbounded_inequality_predicates():
    """Single field with unbounded inequality predicates."""
    filters = {"position": [MongoPredicate(op=MongoOp.GT, value=5)]}
    expected = {
        MongoOp.AND: [
            {
                MongoOp.OR: [
                    {
                        MongoOp.OR: [
                            {"position": {MongoOp.GT: 5}},
                        ]
                    }
                ]
            }
        ]
    }
    result = _generate_query_predicate(filters)
    assert result == expected


def test_generate_query_predicate_multiple_bounded_intervals():
    """Multiple fields with multiple predicates."""
    filters = {
        "position": [
            MongoPredicate(op=MongoOp.EQ, value=1),
            MongoPredicate(op=MongoOp.EQ, value=3),
        ],
        "lap_number": [
            MongoPredicate(op=MongoOp.EQ, value=5),
            MongoPredicate(op=MongoOp.EQ, value=10),
        ],
    }
    expected = {
        MongoOp.AND: [
            {
                MongoOp.OR: [
                    {
                        MongoOp.OR: [
                            {"position": {MongoOp.EQ: 1}},
                            {"position": {MongoOp.EQ: 3}},
                        ]
                    }
                ]
            },
            {
                MongoOp.OR: [
                    {
                        MongoOp.OR: [
                            {"lap_number": {MongoOp.EQ: 5}},
                            {"lap_number": {MongoOp.EQ: 10}},
                        ]
                    }
                ]
            },
        ]
    }
    result = _generate_query_predicate(filters)
    assert result == expected


def test_generate_query_predicate_mixed_predicates():
    """Mix of equality, bounded intervals, and unbounded intervals."""
    filters = {
        "position": [
            MongoPredicate(op=MongoOp.EQ, value=1),
            MongoPredicate(op=MongoOp.GTE, value=5),
            MongoPredicate(op=MongoOp.LTE, value=10),
            MongoPredicate(op=MongoOp.GT, value=15),
        ],
        "lap_number": [
            MongoPredicate(op=MongoOp.EQ, value=3),
            MongoPredicate(op=MongoOp.GTE, value=20),
            MongoPredicate(op=MongoOp.LTE, value=50),
        ],
    }
    expected = {
        MongoOp.AND: [
            {
                MongoOp.OR: [
                    {
                        MongoOp.OR: [
                            {"position": {MongoOp.EQ: 1}},
                        ]
                    },
                    {
                        MongoOp.OR: [
                            {"position": {MongoOp.GT: 15}},
                        ]
                    },
                    {
                        MongoOp.OR: [
                            {
                                MongoOp.AND: [
                                    {"position": {MongoOp.GTE: 5}},
                                    {"position": {MongoOp.LTE: 10}},
                                ]
                            }
                        ]
                    },
                ]
            },
            {
                MongoOp.OR: [
                    {
                        MongoOp.OR: [
                            {"lap_number": {MongoOp.EQ: 3}},
                        ]
                    },
                    {
                        MongoOp.OR: [
                            {
                                MongoOp.AND: [
                                    {"lap_number": {MongoOp.GTE: 20}},
                                    {"lap_number": {MongoOp.LTE: 50}},
                                ]
                            }
                        ]
                    },
                ]
            },
        ]
    }
    result = _generate_query_predicate(filters)
    assert result == expected


def test_generate_query_predicate_deduplication():
    """Duplicate predicates should be deduplicated."""
    filters = {
        "position": [
            MongoPredicate(op=MongoOp.EQ, value=1),
            MongoPredicate(op=MongoOp.EQ, value=1),
        ]
    }
    expected = {
        MongoOp.AND: [
            {
                MongoOp.OR: [
                    {
                        MongoOp.OR: [
                            {"position": {MongoOp.EQ: 1}},
                        ]
                    }
                ]
            }
        ]
    }
    result = _generate_query_predicate(filters)
    assert result == expected


def test_generate_query_predicate_merge_overlapping_intervals():
    """Overlapping intervals should be merged."""
    filters = {
        "position": [
            MongoPredicate(op=MongoOp.GTE, value=4),
            MongoPredicate(op=MongoOp.LTE, value=7),
            MongoPredicate(op=MongoOp.GTE, value=6),
            MongoPredicate(op=MongoOp.LTE, value=10),
        ]
    }
    expected = {
        MongoOp.AND: [
            {
                MongoOp.OR: [
                    {
                        MongoOp.OR: [
                            {
                                MongoOp.AND: [
                                    {"position": {MongoOp.GTE: 4}},
                                    {"position": {MongoOp.LTE: 10}},
                                ]
                            }
                        ]
                    }
                ]
            }
        ]
    }
    result = _generate_query_predicate(filters)
    assert result == expected
