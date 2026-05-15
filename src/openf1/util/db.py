from dataclasses import dataclass
from enum import Enum
import os
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from functools import lru_cache

from bson.codec_options import CodecOptions
from loguru import logger
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import InsertOne, MongoClient, ReplaceOne
from pymongo.errors import BulkWriteError

from openf1.util.misc import hash_obj, timed_cache

_MONGO_CONNECTION_STRING = os.getenv("MONGO_CONNECTION_STRING")
_MONGO_DATABASE = os.getenv("OPENF1_DB_NAME", "openf1-livetiming")

_SORT_KEYS = [
    "date_start",
    "meeting_key",
    "session_key",
    "position_current",
    "_id",
]

_MAX_QUERY_TIME_MS = 5000

_client_sync = None
_client_async = None


class MongoOp(str, Enum):
    EQ = "$eq"
    GTE = "$gte"
    LTE = "$lte"
    GT = "$gt"
    LT = "$lt"
    AND = "$and"
    OR = "$or"


@dataclass(frozen=True)
class MongoPredicate:
    op: MongoOp
    value: str | int | float | datetime

    def to_dict(self) -> dict[MongoOp, str | int | float | datetime]:
        return {self.op: self.value}


def _get_mongo_client_sync():
    """Creates the Sync client only when called (lazy loading), ensuring fork safety"""
    global _client_sync
    if _client_sync is None:
        _client_sync = MongoClient(_MONGO_CONNECTION_STRING, maxPoolSize=100)
    return _client_sync


def _get_mongo_client_async():
    """Creates the Async client only when called (lazy loading), ensuring fork safety"""
    global _client_async
    if _client_async is None:
        _client_async = AsyncIOMotorClient(_MONGO_CONNECTION_STRING, maxPoolSize=100)
    return _client_async


def _get_mongo_db_sync():
    opts = CodecOptions(tz_aware=True, tzinfo=timezone.utc)
    return _get_mongo_client_sync().get_database(_MONGO_DATABASE, codec_options=opts)


def _get_mongo_db_async():
    opts = CodecOptions(tz_aware=True, tzinfo=timezone.utc)
    return _get_mongo_client_async().get_database(_MONGO_DATABASE, codec_options=opts)


async def get_documents(
    collection_name: str, filters: dict[str, list[MongoPredicate]]
) -> list[dict]:
    """Retrieves documents from a specified MongoDB collection, applies filters,
    and sorts.
    The latest document is returned to ensure the most up-to-date information.
    """
    collection = _get_mongo_db_async()[collection_name]
    pipeline = [
        # Apply user filters
        {"$match": _generate_query_predicate(filters)},
        {"$sort": {"_id": -1}},
        # Group all versions of the same document and keep only the first one
        {"$group": {"_id": "$_key", "document": {"$first": "$$ROOT"}}},
        {"$replaceRoot": {"newRoot": "$document"}},
        # Sort
        {"$sort": {key: 1 for key in _SORT_KEYS}},
    ]

    cursor = collection.aggregate(pipeline, maxTimeMS=_MAX_QUERY_TIME_MS)
    results = await cursor.to_list(length=None)

    cleaned_results = []
    for doc in results:
        cleaned_doc = {k: v for k, v in doc.items() if not k.startswith("_")}
        cleaned_results.append(cleaned_doc)

    return cleaned_results


def _get_inequality_predicate_pairs(
    predicates: list[MongoPredicate],
) -> tuple[list[tuple[MongoPredicate, MongoPredicate]], list[MongoPredicate]]:
    """
    Greedy algorithm for pairing predicates such that each pair represents a bounded interval.
    Predicates that are not paired are ignored, and predicate pairs representing overlapping intervals are merged.

    Args:
        predicates: A list of inequality predicates without duplicates (i.e. no two predicates can have the same op and value).
                    Predicates have a MongoDB operator such as "$eq", "$gt", "$gte", "$lt", or "$lte", and a numeric value (e.g. int, float, datetime).

    Returns:
        A tuple:
        - A list of predicate pairs where the first predicate of the pair represents a lower bound ("$gt", "$gte"),
            and the second predicate of the pair represents an upper bound ("$lt", "$lte").
        - A list of unpaired predicates (unbounded).

    Examples:
        [] --> [], []                                                                                   (empty predicates)
        [{"$eq": 5}] --> [], []                                                                         (equality predicates are ignored)
        [{"$gt": 5}] --> [], [{"$gt": 5}]                                                               (unbounded interval)
        [{"$gt": 10}, {"$lt": 5}] --> [], [{"$gt": 10}, {"$lt": 5}]                                     (unbounded intervals)
        [{"$gt": 5}, {"$lt": 10}] --> [({"$gt": 5}, {"$lt": 10})], []                                   (bounded interval)
        [{"$gt": 5}, {"$lt": 10}, {"$lt": 12}] --> [({"$gt": 5}, {"$lt": 10})], [{"$lt": 12}]           (bounded interval with unbounded interval)
        [{"$gt": 5}, {"$lt": 10}, {"$gt": 8}, {"$lt": 12}] --> [({"$gt": 5}, {"$lt": 12})], []          (bounded intervals merged due to overlap)
    """
    if not predicates:
        return [], []

    # Filter out equality predicates
    lower_bound_predicates = [
        predicate
        for predicate in predicates
        if predicate.op in (MongoOp.GT, MongoOp.GTE)
    ]
    upper_bound_predicates = [
        predicate
        for predicate in predicates
        if predicate.op in (MongoOp.LT, MongoOp.LTE)
    ]

    # Sort predicates in descending order so we can pop from list ends
    lower_bound_predicates.sort(key=lambda predicate: predicate.value, reverse=True)
    upper_bound_predicates.sort(key=lambda predicate: predicate.value, reverse=True)

    bounded_ineq_predicate_pairs = []

    unbounded_ineq_predicate_pairs = []
    lower_bound_unpaired_predicates = []

    # Repeat pairing until either predicate list is exhausted
    while lower_bound_predicates and upper_bound_predicates:
        lower_bound_predicate = lower_bound_predicates.pop()

        # Check potential upper bound predicates starting from the smallest predicate
        closest_upper_bound_predicate = None
        for i in reversed(range(len(upper_bound_predicates))):
            upper_bound_predicate = upper_bound_predicates[i]

            if lower_bound_predicate.value < upper_bound_predicate.value:
                # Pair found
                closest_upper_bound_predicate = upper_bound_predicates.pop(i)
                break
            if lower_bound_predicate.value == upper_bound_predicate.value:
                if (
                    lower_bound_predicate.op == MongoOp.GTE
                    and upper_bound_predicate.op == MongoOp.LTE
                ):
                    # Special case: when values are equal and ops are >= and <=, this is a bounded pair consisting of a single value
                    closest_upper_bound_predicate = upper_bound_predicates.pop(i)
                    break

        # Terminate early if no suitable upper bound predicate exists (no more pairs can be made)
        if closest_upper_bound_predicate is None:
            # Keep track of the popped lower bound unpaired predicate
            lower_bound_unpaired_predicates.append(lower_bound_predicate)
            break

        bounded_ineq_predicate_pairs.append(
            (lower_bound_predicate, closest_upper_bound_predicate)
        )

    # Collect remaining unpaired predicates
    unbounded_ineq_predicate_pairs.extend(
        lower_bound_unpaired_predicates + lower_bound_predicates
    )
    unbounded_ineq_predicate_pairs.extend(upper_bound_predicates)

    if not bounded_ineq_predicate_pairs:
        # All predicates are unbounded (no valid pairs found)
        return [], unbounded_ineq_predicate_pairs

    # Merge overlapping pairs, first sorting pairs by lower bound, then upper bound
    bounded_ineq_predicate_pairs.sort(key=lambda pair: (pair[0].value, pair[1].value))
    merged_bounded_ineq_predicate_pairs = []
    curr_pair = bounded_ineq_predicate_pairs[0]

    for next_pair in bounded_ineq_predicate_pairs[1:]:
        curr_lower_bound_predicate, curr_upper_bound_predicate = curr_pair
        next_lower_bound_predicate, next_upper_bound_predicate = next_pair

        if curr_upper_bound_predicate.value > next_lower_bound_predicate.value:
            # Extend upper bound of current pair
            curr_pair = (curr_lower_bound_predicate, next_upper_bound_predicate)
            continue
        if curr_upper_bound_predicate.value < next_lower_bound_predicate.value:
            # For integer values, if values differ by 1 and both ops contain an equality =, this is considered an overlapping pair
            if (
                isinstance(curr_upper_bound_predicate.value, int)
                and isinstance(next_lower_bound_predicate.value, int)
                and curr_upper_bound_predicate.value + 1
                == next_lower_bound_predicate.value
                and curr_upper_bound_predicate.op == MongoOp.LTE
                and next_lower_bound_predicate.op == MongoOp.GTE
            ):
                curr_pair = (curr_lower_bound_predicate, next_upper_bound_predicate)
                continue
            # Fall through to no overlap path
        if curr_upper_bound_predicate.value == next_lower_bound_predicate.value:
            if (
                next_lower_bound_predicate.op == MongoOp.GTE
                or curr_upper_bound_predicate.op == MongoOp.LTE
            ):
                # Special case: when values are equal and we have either a >= or <= op, this is considered an overlapping pair
                curr_pair = (curr_lower_bound_predicate, next_upper_bound_predicate)
                continue
            # Fall through to no overlap path

        # No overlap, pairs overlapping the current pair are all merged
        merged_bounded_ineq_predicate_pairs.append(curr_pair)
        curr_pair = next_pair

    merged_bounded_ineq_predicate_pairs.append(curr_pair)

    return merged_bounded_ineq_predicate_pairs, unbounded_ineq_predicate_pairs


def _get_unique_predicates(predicates: list[MongoPredicate]) -> list[MongoPredicate]:
    """
    Returns a list of unique predicates where no two predicates have the same op and the same value.
    """
    seen_predicates = set()
    filtered_predicates: list[MongoPredicate] = []

    for predicate in predicates:
        hashed_predicate = hash_obj(predicate)

        if hashed_predicate not in seen_predicates:
            filtered_predicates.append(predicate)
            seen_predicates.add(hashed_predicate)

    return filtered_predicates


def _generate_query_predicate(filters: dict[str, list[MongoPredicate]]) -> dict:
    """
    Returns a MongoDB query predicate that supports:
        - repeated query params
        - query param intervals
        - any combination of the above

    Examples:
        A query string "position=1&position=3" returns documents with position equal to 1 OR 3
        A query string "position>=4&position<=7&position>=5&position<=15" returns documents with position between 4 and 15 (overlapping intervals are merged)
        A query string "position>=4&position<=7&position>=10&position<=15" returns documents with position between 4 and 7 OR 10 and 15
        A query string "position=1&position=3&position>=4&position<=7&position>=10&position<=15" returns documents matching either of the above criteria
    """
    query_predicates = defaultdict(list)

    for key, predicates in filters.items():
        filtered_predicates = _get_unique_predicates(predicates)

        eq_predicates = [
            predicate for predicate in filtered_predicates if predicate.op == MongoOp.EQ
        ]

        (
            bounded_ineq_predicate_pairs,
            unbounded_ineq_predicates,
        ) = _get_inequality_predicate_pairs(filtered_predicates)

        # Guaranteed to have at least one predicate at this stage
        # Predicates for the same query param are joined with logical OR except for bounded pairs (logical AND)
        inner_predicate = defaultdict(list)
        if eq_predicates:
            inner_predicate[MongoOp.OR].append(
                {
                    MongoOp.OR: [
                        {key: predicate.to_dict()} for predicate in eq_predicates
                    ]
                }
            )
        if unbounded_ineq_predicates:
            inner_predicate[MongoOp.OR].append(
                {
                    MongoOp.OR: [
                        {key: predicate.to_dict()}
                        for predicate in unbounded_ineq_predicates
                    ]
                }
            )
        if bounded_ineq_predicate_pairs:
            inner_predicate[MongoOp.OR].append(
                {
                    MongoOp.OR: [
                        {
                            MongoOp.AND: [
                                {key: predicate.to_dict()}
                                for predicate in bounded_ineq_predicate_pair
                            ]
                        }
                        for bounded_ineq_predicate_pair in bounded_ineq_predicate_pairs
                    ]
                }
            )

        # Predicates for different query params are joined with logical AND
        query_predicates[MongoOp.AND].append(dict(inner_predicate))

    return dict(query_predicates)


@timed_cache(60)  # Cache the output for 1 minute
def get_latest_session_info() -> dict:
    sessions = _get_mongo_db_sync()["sessions"]
    threshold = datetime.now(timezone.utc) + timedelta(seconds=60)
    latest_session = sessions.find_one(
        {"date_start": {MongoOp.LTE: threshold}, "is_cancelled": {"$eq": False}},
        sort=[("date_start", -1)],
    )

    if latest_session:
        return latest_session
    else:
        raise SystemError("Could not find any past or current session in MongoDB")


@timed_cache(1800)  # Cache the output for 30 minutes
def get_closest_session_info() -> dict:
    """Returns the session closest to the current time"""
    sessions = _get_mongo_db_sync()["sessions"]
    now = datetime.now(timezone.utc)

    # First, try to find an active session
    active_session = sessions.find_one(
        {"date_start": {MongoOp.LTE: now}, "date_end": {MongoOp.GTE: now}}
    )

    if active_session:
        return active_session

    # If no active session, find the closest one
    # Get the most recent past session (by end time)
    past_session = sessions.find_one(
        {"date_end": {MongoOp.LT: now}, "is_cancelled": {"$eq": False}},
        sort=[("date_end", -1)],
    )

    # Get the nearest future session (by start time)
    future_session = sessions.find_one(
        {"date_start": {MongoOp.GT: now}, "is_cancelled": {"$eq": False}},
        sort=[("date_start", 1)],
    )

    # Return whichever is closer
    if past_session and future_session:
        past_diff = (now - past_session["date_end"]).total_seconds()
        future_diff = (future_session["date_start"] - now).total_seconds()
        return past_session if past_diff <= future_diff else future_session
    elif past_session:
        return past_session
    elif future_session:
        return future_session
    else:
        raise SystemError("Could not find any session in MongoDB")


@lru_cache()
def session_key_to_path(session_key: int) -> str | None:
    sessions = _get_mongo_db_sync()["sessions"]

    session = sessions.find_one(
        {"session_key": session_key, "_path": {"$exists": True}},
        projection={"_path": 1},
    )

    return session["_path"] if session else None


def insert_data_sync(collection_name: str, docs: list[dict], batch_size: int = 50_000):
    """Inserts documents into a MongoDB collection in batches"""
    collection = _get_mongo_db_sync()[collection_name]

    for i in range(0, len(docs), batch_size):
        batch = docs[i : i + batch_size]

        try:
            operations = [InsertOne(doc) for doc in batch]
            collection.bulk_write(operations, ordered=False)
        except BulkWriteError as bwe:
            for error in bwe.details.get("writeErrors", []):
                logger.error(f"Error during bulk write operation: {error}")
        except Exception:
            logger.exception("Error during bulk write operation")


def upsert_data_sync(collection_name: str, docs: list[dict], batch_size: int = 50_000):
    """Upserts (inserts or replaces) documents into a MongoDB collection in batches
    based on _key."""
    collection = _get_mongo_db_sync()[collection_name]

    for i in range(0, len(docs), batch_size):
        batch = docs[i : i + batch_size]
        operations = [
            ReplaceOne({"_key": doc["_key"]}, doc, upsert=True) for doc in batch
        ]
        collection.bulk_write(operations, ordered=False)


async def insert_data_async(collection_name: str, docs: list[dict]):
    collection = _get_mongo_db_async()[collection_name]

    try:
        operations = [InsertOne(doc) for doc in docs]
        await collection.bulk_write(operations, ordered=False)
    except BulkWriteError as bwe:
        for error in bwe.details.get("writeErrors", []):
            logger.error(f"Error during bulk write operation: {error}")
    except Exception:
        logger.exception("Error during bulk write operation")
