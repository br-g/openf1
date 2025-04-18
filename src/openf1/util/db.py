import os
from datetime import datetime, timezone
from functools import lru_cache

from loguru import logger
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import InsertOne, MongoClient
from pymongo.errors import BulkWriteError

from openf1.util.misc import timed_cache

_MONGO_CONNECTION_STRING = os.getenv("MONGO_CONNECTION_STRING")
_MONGO_DATABASE = os.getenv("OPENF1_DB_NAME", "openf1-livetiming")

_SORT_KEYS = [
    "date",
    "date_start",
    "meeting_key",
    "session_key",
    "lap_start",
    "lap_number",
    "lap_end",
    "date_end",
    "stint_number",
    "driver_number",
]


@lru_cache()
def _get_mongo_db_sync():
    client = MongoClient(_MONGO_CONNECTION_STRING)
    return client[_MONGO_DATABASE]


@lru_cache()
def _get_mongo_db_async():
    client = AsyncIOMotorClient(_MONGO_CONNECTION_STRING)
    return client[_MONGO_DATABASE]


async def get_documents(collection_name: str, filters: dict) -> list[dict]:
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
        {"$match": filters},
        {"$sort": {"_id": presort_direction}},
        # Group all versions of the same document and keep only the first one
        {"$group": {"_id": "$_key", "document": {"$first": "$$ROOT"}}},
        {"$replaceRoot": {"newRoot": "$document"}},
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
        # Sort
        {"$sort": {key: 1 for key in _SORT_KEYS}},
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
        except Exception as e:
            logger.error(f"Error during bulk write operation: {str(e)}")


async def insert_data_async(collection_name: str, docs: list[dict]):
    collection = _get_mongo_db_async()[collection_name]

    try:
        operations = [InsertOne(doc) for doc in docs]
        await collection.bulk_write(operations, ordered=False)
    except BulkWriteError as bwe:
        for error in bwe.details.get("writeErrors", []):
            logger.error(f"Error during bulk write operation: {error}")
    except Exception as e:
        logger.error(f"Error during bulk write operation: {str(e)}")
