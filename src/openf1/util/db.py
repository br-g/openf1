import asyncio
import os
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from functools import lru_cache
from typing import Any

from bson.codec_options import CodecOptions
from loguru import logger
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import InsertOne, MongoClient, ReplaceOne
from pymongo.errors import BulkWriteError

from openf1.util.misc import batched, hash_obj, timed_cache

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
    collection_name: str, filters: dict[str, list[dict]]
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


def _get_bounded_inequality_predicate_pairs(
    predicates: list[dict],
) -> list[tuple[dict, dict]]:
    """
    Greedy matching algorithm for pairing predicates in the form {op: value}
    where op is a MongoDB inequality operator such as "$gt", "$gte", "$lt", or "$lte".

    Args:
        predicates: A list of inequality predicates without duplicates (i.e. no two predicates can have the same op and value).

    Returns:
        A list of predicate pairs where the first predicate of the pair represents a lower bound ("$gt", "$gte"),
        the second predicate of the pair represents an upper bound ("$lt", "$lte"),
        and the value difference among all pairs is minimized (i.e. the value difference in each pair is as small as possible).

    Examples:
        [] --> []
        [{"$gt": 5}] --> []
        [{"$gt": 10}, {"$lt": 5}] --> []
        [{"$gt": 5}, {"$lt": 10}] --> [({"$gt": 5}, {"$lt": 10})]
        [{"$gt": 5}, {"$lt": 10}, {"$lt": 12}] --> [({"$gt": 5}, {"$lt": 10})]
        [{"$gt": 5}, {"$lt": 10}, {"$gt": 8}, {"$lt": 12}] --> [({"$gt": 5}, {"$lt": 10}), ({"$gt": 8}, {"$lt": 12})]
    """
    lower_bound_predicates = [
        predicate
        for predicate in predicates
        if "$gt" in predicate or "$gte" in predicate
    ]
    upper_bound_predicates = [
        predicate
        for predicate in predicates
        if "$lt" in predicate or "$lte" in predicate
    ]

    # Sort predicates in reverse order for some minor optimization
    lower_bound_predicates.sort(
        key=lambda predicate: _get_predicate_value(predicate), reverse=True
    )
    upper_bound_predicates.sort(
        key=lambda predicate: _get_predicate_value(predicate), reverse=True
    )

    bounded_ineq_predicate_pairs = []

    # Repeat pairing until either predicate list is exhausted
    while lower_bound_predicates and upper_bound_predicates:
        lower_bound_predicate = lower_bound_predicates.pop()

        # Check each upper bound predicate starting from the smallest valued predicate
        # If the lower bound predicate is <= the upper bound predicate, a pair has been found
        closest_upper_bound_predicate = None
        for i in reversed(range(len(upper_bound_predicates))):
            if _get_predicate_value(lower_bound_predicate) <= _get_predicate_value(
                upper_bound_predicates[i]
            ):
                closest_upper_bound_predicate = upper_bound_predicates.pop(i)
                break

        # Terminate early if no suitable upper bound predicate exists (no more pairs can be made)
        if closest_upper_bound_predicate is None:
            break

        bounded_ineq_predicate_pairs.append(
            (lower_bound_predicate, closest_upper_bound_predicate)
        )

    return bounded_ineq_predicate_pairs


def _get_predicate_value(predicate: dict) -> Any:
    """
    Returns the first value in a predicate if it exists, otherwise returns None.
    """
    return next((value for value in predicate.values()), None)


def _get_unique_predicates(predicates: list[dict]) -> list[dict]:
    """
    Returns a list of predicates in the form {op: value} where no two predicates have the same op and the same value.
    """
    seen_predicates = set()
    filtered_predicates = []

    for predicate in predicates:
        hashed_predicate = hash_obj(predicate)

        if hashed_predicate not in seen_predicates:
            filtered_predicates.append(predicate)
            seen_predicates.add(hashed_predicate)

    return filtered_predicates


def _generate_query_predicate(filters: dict[str, list[dict]]) -> dict:
    """
    Returns a MongoDB query predicate that supports:
        - repeated query params
        - query param intervals
        - any combination of the above

    Examples:
        A query string "position=1&position=3" returns documents with position equal to 1 OR 3
        A query string "position>=4&position<=7&position>=10&position<=15" returns documents with position between 4 and 7 OR 10 and 15)
        A query string "position=1&position=3&position>=4&position<=7&position>=10&position<=15" returns documents matching either of the above criteria
    """
    query_predicates = defaultdict(list)

    for key, predicates in filters.items():
        filtered_predicates = _get_unique_predicates(predicates)

        eq_predicates = [
            predicate for predicate in filtered_predicates if "$eq" in predicate
        ]

        bounded_ineq_predicate_pairs = _get_bounded_inequality_predicate_pairs(
            filtered_predicates
        )

        # Predicates that are neither paired nor equality predicates are unbounded inequality predicates
        bounded_ineq_predicates = [
            predicate
            for predicate_pair in bounded_ineq_predicate_pairs
            for predicate in predicate_pair
        ]
        unbounded_ineq_predicates = [
            predicate
            for predicate in filtered_predicates
            if predicate not in bounded_ineq_predicates
            and predicate not in eq_predicates
        ]

        # Guaranteed to have at least one predicate at this stage
        # Predicates for the same query param are joined with logical OR except for bounded pairs (logical AND)
        inner_predicate = defaultdict(list)
        if eq_predicates:
            inner_predicate["$or"].append(
                {"$or": [{key: predicate} for predicate in eq_predicates]}
            )
        if unbounded_ineq_predicates:
            inner_predicate["$or"].append(
                {"$or": [{key: predicate} for predicate in unbounded_ineq_predicates]}
            )
        if bounded_ineq_predicate_pairs:
            inner_predicate["$or"].append(
                {
                    "$or": [
                        {
                            "$and": [
                                {key: predicate}
                                for predicate in bounded_ineq_predicate_pair
                            ]
                        }
                        for bounded_ineq_predicate_pair in bounded_ineq_predicate_pairs
                    ]
                }
            )

        # Predicates for different query params are joined with logical AND
        query_predicates["$and"].append(dict(inner_predicate))

    return dict(query_predicates)


@timed_cache(60)  # Cache the output for 1 minute
def get_latest_session_info() -> dict:
    sessions = _get_mongo_db_sync()["sessions"]
    threshold = datetime.now(timezone.utc) + timedelta(seconds=60)
    latest_session = sessions.find_one(
        {"date_start": {"$lte": threshold}}, sort=[("date_start", -1)]
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
        {"date_start": {"$lte": now}, "date_end": {"$gte": now}}
    )

    if active_session:
        return active_session

    # If no active session, find the closest one
    # Get the most recent past session (by end time)
    past_session = sessions.find_one(
        {"date_end": {"$lt": now}}, sort=[("date_end", -1)]
    )

    # Get the nearest future session (by start time)
    future_session = sessions.find_one(
        {"date_start": {"$gt": now}}, sort=[("date_start", 1)]
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


async def insert_data_async(
    collection_name: str, docs: list[dict], batch_size: int = 50_000
):
    collection = _get_mongo_db_async()[collection_name]

    try:
        await asyncio.gather(
            *[
                collection.bulk_write([InsertOne(doc) for doc in batch], ordered=False)
                for batch in batched(docs, batch_size)
            ]
        )
    except BulkWriteError as bwe:
        for error in bwe.details.get("writeErrors", []):
            logger.error(f"Error during bulk write operation: {error}")
    except Exception:
        logger.exception("Error during bulk write operation")
