from collections import defaultdict
import json
import os
from datetime import datetime, timezone
from functools import lru_cache

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
    "_id",
]


@lru_cache()
def _get_mongo_db_sync():
    client = MongoClient(_MONGO_CONNECTION_STRING)
    return client[_MONGO_DATABASE]


@lru_cache()
def _get_mongo_db_async():
    client = AsyncIOMotorClient(_MONGO_CONNECTION_STRING)
    return client[_MONGO_DATABASE]


def _get_bounded_query_predicate_pairs(predicates: list[dict]) -> list[tuple[dict, dict]]:
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
        if predicate.get("$gt") is not None or predicate.get("$gte") is not None
    ]
    upper_bound_predicates = [
        predicate
        for predicate in predicates
        if predicate.get("$lt") is not None or predicate.get("$lte") is not None
    ]

    # Sort predicates in reverse order for some minor optimization
    lower_bound_predicates.sort(
        key=lambda predicate: list(predicate.values())[0], reverse=True
    )
    upper_bound_predicates.sort(
        key=lambda predicate: list(predicate.values())[0], reverse=True
    )

    bounded_ineq_predicate_pairs = []

    # Repeat pairing until either predicate list is exhausted
    while lower_bound_predicates and upper_bound_predicates:
        lower_bound_predicate = lower_bound_predicates.pop()

        # Check each upper bound predicate starting from the smallest valued predicate
        # If the lower bound predicate is <= the upper bound predicate, a pair has been found
        closest_upper_bound_predicate = None
        for i in reversed(range(len(upper_bound_predicates))):
            if (
                list(lower_bound_predicate.values())[0]
                <= list(upper_bound_predicates[i].values())[0]
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
        # Filter out duplicate predicates
        filtered_predicates = _get_unique_predicates(predicates)

        # Get equality predicates
        eq_predicates = [
            predicate
            for predicate in filtered_predicates
            if predicate.get("$eq") is not None
        ]

        # Get bounded inequality predicate pairs
        bounded_ineq_predicate_pairs = _get_bounded_query_predicate_pairs(filtered_predicates)

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

        query_predicates["$and"].append(dict(inner_predicate))

    return dict(query_predicates)


async def get_documents(collection_name: str, filters: dict[str, list[dict]]) -> list[dict]:
    """Retrieves documents from a specified MongoDB collection, applies filters,
    and sorts.

    - For 'meetings', the earliest document is returned to reflect the start time of the
      first session.
    - For all other collections, the latest document is returned to ensure the most
      up-to-date information.
    """
    presort_direction = 1 if collection_name == "meetings" else -1

    collection = _get_mongo_db_async()[collection_name]
    pipeline = [
        # Apply user filters
        {"$match": _generate_query_predicate(filters)},
        {"$sort": {"_id": presort_direction}},
        # Group all versions of the same document and keep only the first one
        {"$group": {"_id": "$_key", "document": {"$first": "$$ROOT"}}},
        {"$replaceRoot": {"newRoot": "$document"}},
        # Sort
        {"$sort": {key: 1 for key in _SORT_KEYS}},
        # Remove fields starting with '_'
        {
            "$replaceWith": {
                "$arrayToObject": {
                    "$filter": {
                        "input": {"$objectToArray": "$$ROOT"},
                        "as": "field",
                        "cond": {"$ne": [{"$substrCP": ["$$field.k", 0, 1]}, "_"]},
                    }
                }
            }
        },
    ]
    cursor = collection.aggregate(pipeline)
    results = await cursor.to_list(length=None)

    # Add UTC timezone if not set
    for res in results:
        for key, val in res.items():
            if isinstance(val, datetime) and val.tzinfo is None:
                res[key] = res[key].replace(tzinfo=timezone.utc)

    return results


@timed_cache(60)  # Cache the output for 1 minute
def get_latest_session_info() -> dict:
    sessions = _get_mongo_db_sync()["sessions"]
    latest_session = sessions.find_one(sort=[("date_start", -1)])

    if latest_session:
        return latest_session
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
