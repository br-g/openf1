from typing import List, Dict, Iterator, Optional
import os
import json
import hashlib
import asyncio
from datetime import datetime
import pymongo
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorCollection
from logger import logger

BATCH_SIZE = 1000  # Maximum number of JSON docs to be uploaded at once to MongoDB


def get_mongo_db() -> AsyncIOMotorClient:
    """Returns an asynchronous MongoDB client.
       The client could not be a global variable because it is not thread safe.
    """
    return AsyncIOMotorClient(os.getenv('MONGO_CONNECTION_STRING'))['raw']


collection_names = set()
async def _collection_exists(name: str, mongo_db: Optional[AsyncIOMotorClient] = None) -> bool:
    """Returns whether a collection exists in the MongoDB database"""
    if mongo_db is None:
        mongo_db = get_mongo_db()

    global collection_names
    if name in collection_names:
        return True
    else:
        collection_names = set(await mongo_db.list_collection_names())
        return name in collection_names


def _time_to_str(dct: Dict) -> Dict:
    """Turns datetime objects into ISO strings"""
    res = {}
    for key, value in dct.items():
        if isinstance(value, dict):
            res[key] = _time_to_str(value)
        elif isinstance(value, datetime):
            res[key] = value.isoformat()
        else:
            res[key] = value
    return res


def _hash_dict(dct: Dict) -> str:
    """Hashes dict content"""
    dct_str = json.dumps(_time_to_str(dct), sort_keys=True)
    return hashlib.sha256(dct_str.encode()).hexdigest()


async def _insert(collection: AsyncIOMotorCollection, docs: List[Dict]):
    """Inserts documents to a MongoDB collection and skips duplicates"""
    # Create an ID to check for duplicates
    for doc in docs:
        doc['_id'] = doc['_time'].strftime('%y%m%d%H%M%S') + _hash_dict(doc)[:4]  # limit ID length to reduce storage footprint

    try:
        await collection.insert_many(docs, ordered=False)
    except pymongo.errors.BulkWriteError as e:
        # Handle the duplicate key errors (and possibly other errors)
        # Duplicates are expected as there are multiple ingestor instances working
        # simultaneously (to increase resilience).
        for error in e.details.get('writeErrors'):
            if error.get('code') == 11000:  # Duplicate key error code
                pass
            else:
                logger.error(error)


def _get_batches(docs: List[Dict]) -> Iterator[List[Dict]]:
    """Yields batches of maximum size `BATCH_SIZE`"""
    for i in range(0, len(docs), BATCH_SIZE):
        yield docs[i:i+BATCH_SIZE]


async def insert_data_async(collection_name: str, docs: List[Dict],
                            mongo_db: Optional[AsyncIOMotorClient] = None):
    """Inserts documents to a MongoDB collection, in batches, and skips duplicates."""
    if mongo_db is None:
        mongo_db = get_mongo_db()

    collection = mongo_db[collection_name]
    tasks = [_insert(collection=collection, docs=batch) for batch in _get_batches(docs)]
    await asyncio.gather(*tasks)
