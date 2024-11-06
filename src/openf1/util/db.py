import asyncio
import os
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from functools import lru_cache

import pymongo
from loguru import logger
from motor.motor_asyncio import AsyncIOMotorClient

from openf1.util.misc import SingletonMeta, timed_cache

_MONGO_CONNECTION_STRING = os.getenv("MONGO_CONNECTION_STRING")
_MONGO_DATABASE = "openf1-livetiming"


@lru_cache()
def _get_mongo_db_sync():
    client = pymongo.MongoClient(_MONGO_CONNECTION_STRING)
    db = client[_MONGO_DATABASE]
    return db


@lru_cache()
def _get_mongo_db_async():
    client = AsyncIOMotorClient(_MONGO_CONNECTION_STRING)
    db = client[_MONGO_DATABASE]
    return db


def query_db(collection_name: str, filters: dict) -> list[dict]:
    collection = _get_mongo_db_sync()[collection_name]
    results = collection.find(filters)
    return list(results)


@timed_cache(60)  # Cache the output for 1 minute
def get_latest_session_info() -> int:
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


async def insert_data_async(
    collection_name: str,
    docs: list[dict],
):
    """Asynchronously inserts or updates multiple documents in the specified
    MongoDB collection"""
    collection = _get_mongo_db_async()[collection_name]
    try:
        operations = [
            pymongo.UpdateOne(filter={"_id": doc["_id"]}, update={"$set": doc}, upsert=True)
            for doc in docs
        ]
        await collection.bulk_write(operations, ordered=False)
    except Exception as e:
        logger.error(f"Error during bulk write operation: {str(e)}")


@dataclass
class DbBatchIngestor(metaclass=SingletonMeta):
    """Provides an asynchronous interface for adding documents to collections,
    automatically batching inserts for improved performance. It uses a background task
    to periodically flush documents to the database based on time and batch size constraints.
    """

    max_delay: float = 2  # Max delay between addition and insertion into DB, in seconds
    max_batch_size: int = 100000
    docs_by_collection: defaultdict = field(default_factory=lambda: defaultdict(list))
    last_insertion_time: defaultdict = field(default_factory=lambda: defaultdict(float))
    insertion_task: asyncio.Task = None
    locks: defaultdict = field(default_factory=lambda: defaultdict(asyncio.Lock))

    async def start_insertion_task(self):
        """Starts the background insertion task if it's not already running"""
        if self.insertion_task is None:
            self.insertion_task = asyncio.create_task(self._insert_loop())

    async def add(self, collection: str, docs: list[dict]):
        """Adds documents to a collection for batch insertion"""
        await self.start_insertion_task()  # Ensure the insertion task is running
        async with self.locks[collection]:
            self.docs_by_collection[collection].extend(docs)

        # If we've exceeded the max batch size, insert immediately
        while len(self.docs_by_collection[collection]) >= self.max_batch_size:
            await self.flush(collection)

        # Set the last insertion time if this is the first batch
        if (
            self.docs_by_collection[collection]
            and self.last_insertion_time[collection] == 0
        ):
            self.last_insertion_time[collection] = time.time()

    async def _insert_loop(self):
        """Background task that periodically checks and inserts batches"""
        try:
            while True:
                current_time = time.time()
                for collection in self.docs_by_collection.keys():
                    # Insert if max delay has been reached
                    if self.docs_by_collection[collection] and (
                        current_time - self.last_insertion_time[collection]
                        >= self.max_delay
                    ):
                        await self.flush(collection)
                await asyncio.sleep(0.5)  # Sleep to avoid busy waiting
        except asyncio.CancelledError:
            pass

    async def _insert_batch(self, collection: str):
        """Inserts a batch of documents for a given collection"""
        async with self.locks[collection]:
            docs_to_insert = self.docs_by_collection[collection][: self.max_batch_size]
            self.docs_by_collection[collection] = self.docs_by_collection[collection][
                len(docs_to_insert) :
            ]
        await insert_data_async(collection_name=collection, docs=docs_to_insert)

        self.last_insertion_time[collection] = time.time()

    async def flush(self, collection: str = None):
        """Flushes all pending documents to the database"""
        if collection:
            collections = [collection]
        else:
            collections = list(self.docs_by_collection.keys())

        for col in collections:
            while self.docs_by_collection[col]:
                await self._insert_batch(col)

    def add_and_flush(self, collection: str, docs: list[dict]):
        """Synchronous method to add documents and immediately flush them to the database.
        Useful for contexts where asynchronous operations are not possible."""

        async def _():
            await self.start_insertion_task()
            await self.add(collection=collection, docs=docs)
            await self.flush(collection)

        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If we're in a running event loop (like in Jupyter), use an executor
                with ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, _())
                    future.result()  # Wait for the coroutine to complete
            else:
                # If there's no running event loop, use run_until_complete
                loop.run_until_complete(_())
        except RuntimeError:
            # If we can't get an event loop, create a new one and run the coroutine
            asyncio.run(_())

    async def close(self):
        """Closes the batch ingestor, cancelling the insertion task and flushing all documents"""
        if self.insertion_task:
            self.insertion_task.cancel()
            try:
                await self.insertion_task
            except asyncio.CancelledError:
                pass  # We expect this error, so we can ignore it

        await self.flush()
