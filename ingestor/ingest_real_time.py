"""Helper functions for parsing and saving raw F1 data to database, in real-time."""

from typing import List
from collections import defaultdict
from datetime import datetime, timedelta
import asyncio
import pytz
from tqdm import tqdm
from parsing import parse_line
from motor.motor_asyncio import AsyncIOMotorClient
from db import get_mongo_db, insert_data_async
from util import to_datetime

_start_time = None  # Date at which data starts being ingested
_ingestion_queue = []  # Data waiting to be ingested. Data is not ingested right away
                       # because we might be waiting for session information first.

# The `session_key` and `meeting_key` can be determined in 2 ways:
# - By receiving a SessionInfo message which contain these information. There is usually
#   such a message at the beginning of sessions.
# - By querying some data recently added to the database that contain these information.
_session_key = None
_meeting_key = None


async def _try_set_session_info(mongo_db: AsyncIOMotorClient):
    """Tries setting `session_key` and `meeting_key` by copying these values
       from documents added recently to the database
    """
    global _session_key
    global _meeting_key

    # Retrieve some documents that have been written recently
    docs = []
    for collection in {'WeatherData', 'Heartbeat', 'Position.z-Position-Entries'}:
        cursor = mongo_db[collection].find({'_time': {
            '$gte': datetime.now().astimezone(pytz.UTC) - timedelta(minutes=30)
        }}).limit(1000)
        docs = await cursor.to_list(length=1000)
        if docs:
            break

    if docs:
        _session_keys = {e['_session_key'] for e in docs if e['_session_key']}
        _meeting_keys = {e['_meeting_key'] for e in docs if e['_meeting_key']}

        if len(_session_keys) == 1:
            _session_key = list(_session_keys)[0]
        if len(_meeting_keys) == 1:
            _meeting_key = list(_meeting_keys)[0]


def _add_line(line: str):
    """Adds a line to the queue to be later parsed and saved"""
    global _session_key
    global _meeting_key
    global _ingestion_queue

    line = line.strip()
    if not line:
        return
    line_data = eval(line)
    _ingestion_queue.append(line_data)
    
    if line_data[0] == 'SessionInfo':
        _session_key = line_data[1]['Key']
        _meeting_key = line_data[1]['Meeting']['Key']


async def _ingest(mongo_db: AsyncIOMotorClient, force: bool = False) -> List:
    """Parses and saves data from the queue, unless we are still waiting for the
       `session_key` and `meeting_key` variables to be set.
       If `force` is True, data is parsed and saved anyway.
    """
    global _start_time
    global _session_key
    global _meeting_key
    global _ingestion_queue

    if not _ingestion_queue:
        return []

    if _start_time is None:
        _start_time = datetime.now()
    
    if not force and _session_key is None and datetime.now()-_start_time < timedelta(minutes=1):
        return []

    # Parse
    parsed = defaultdict(list)
    while _ingestion_queue:
        data = _ingestion_queue.pop(0)
        _parsed = parse_line(
            topic=data[0],
            content=data[1],
            session_key=_session_key,
            meeting_key=_meeting_key,
            time=to_datetime(data[2]),
        )
        # Group data by collection for faster addition to the database
        for collection, vals in _parsed.items():
            parsed[collection] += vals

    # Save to database
    tasks = []
    for collection_name, docs in parsed.items():
        tasks.append(
            asyncio.create_task(insert_data_async(collection_name=collection_name,
                                                  docs=docs, mongo_db=mongo_db))
        )
    return tasks


async def tail_and_ingest(filepath: str):
    """Ingests every new line that is appended to the file"""
    mongo_db = get_mongo_db()
    await _try_set_session_info(mongo_db)

    if _session_key is None or _meeting_key is None:
        await asyncio.sleep(60)
        await _try_set_session_info(mongo_db)

    with open(filepath, 'r') as file:
        # Move to the end of the file
        file.seek(0, 2)
        while True:
            line = file.readline()
            if not line:
                await asyncio.sleep(0.1)  # Sleep a bit before trying again
                continue
            _add_line(line)
            await _ingest(mongo_db=mongo_db)
    
    await _ingest(mongo_db=mongo_db, force=True)


async def read_and_ingest(filepath: str):
    """Ingests the content of the file, line by line"""
    mongo_db = get_mongo_db()
    await _try_set_session_info(mongo_db)

    with open(filepath, 'r') as file:
        tasks = []
        for line in tqdm(list(file)):
            _add_line(line)
            tasks += await _ingest(mongo_db=mongo_db)
            await asyncio.sleep(0.02)  # Don't go to fast!
    
    tasks += await _ingest(mongo_db=mongo_db, force=True)
    if tasks:
        await asyncio.gather(*tasks)
