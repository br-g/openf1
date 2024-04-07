"""Script for parsing and saving raw historical F1 data to database."""

from typing import Tuple, Dict, Optional, List, Iterator
import os
import re
import json
from collections import defaultdict
import requests
from datetime import datetime, timedelta
import asyncio
import click
from tqdm import tqdm
from parsing import parse_line
from db import insert_data_async, get_mongo_db
from logger import logger
from util import to_timedelta

BASE_API_URL = 'https://livetiming.formula1.com/static'


def _download_topic(session_path: str, filename: str) -> str:
    """Downloads raw data for a specific topic"""
    url = os.path.join(BASE_API_URL, session_path, filename)
    return requests.get(url).text


def _get_schedule(year: int) -> Dict:
    """Returns data about all the past sessions for a specific year"""
    url = os.path.join(BASE_API_URL, f'{year}/Index.json')
    return json.loads(requests.get(url).content)


def _get_session_keys(year: int, meeting_key: int) -> List[int]:
    """Returns the keys of the sessions for a specific meeting"""
    for meeting in _get_schedule(year)['Meetings']:
        if meeting['Key'] == meeting_key:
            return [e['Key'] for e in meeting['Sessions']]
            
    raise SystemError(f'Meeting not found (year: `{year}`, meeting_key: `{meeting_key}`).')


def _parse(line: str) -> Tuple[timedelta, str]:
    """Parses a line to extract the duration since session start and raw data.

    The line is expected to be formatted as follows:
    (duration since session start, raw data)
    """
    pattern = r'(\d+:\d+:\d+\.\d+)(.*)'
    match = re.match(pattern, line)
    return to_timedelta(match.group(1)), match.group(2).strip('\r').strip('"')


def parse_topic(session_path: str, topic_filename: str, session_key: Optional[int] = None,
                meeting_key: Optional[int] = None, t0: Optional[datetime] = None) -> Dict[str, List[Dict]]:
    """Parses a topic file for a specified session and returns the parsed data as a dictionary.
       `t0` is the start time of the session when data begins to stream.
    """
    res = defaultdict(list)

    raw = _download_topic(session_path=session_path, filename=topic_filename)
    if '<Error><Code>NoSuchKey</Code>' in raw:
        raise SystemError(f'Topic not found at `{session_path}{topic_filename}`.')

    for line in raw.split('\n'):
        if not line:
            continue
        session_time, content = _parse(line)
        parsed = parse_line(
            topic=os.path.splitext(topic_filename)[0],
            content=content,
            session_key=session_key,
            meeting_key=meeting_key,
            time=t0 + session_time if t0 else None,
            session_time=session_time.total_seconds(),
        )
        # Group data by collection for faster addition to the database
        for collection, vals in parsed.items():
            res[collection] += vals

    return dict(res)


def get_session_path(year: int, meeting_key: int, session_key: int) -> str:
    """Retrieves the session path from the F1 "Index.json" data"""
    for meeting in _get_schedule(year)['Meetings']:
        if meeting['Key'] == meeting_key:
            for session in meeting['Sessions']:
                if session['Key'] == session_key:
                    return session['Path']
            
    raise SystemError(f'Session not found (year: `{year}`, meeting_key: `{meeting_key}`, ' \
                      f'session_key: `{session_key}`).')


def estimate_t0(session_path: str) -> datetime:
    """Estimates `t0`, the start time of the session when data begins to stream.
       The calculation method comes from the FastF1 package (https://github.com/theOehrly/Fast-F1/blob/317bacf8c61038d7e8d0f48165330167702b349f/fastf1/core.py#L2208).
    """
    position_z = parse_topic(
        session_path=session_path,
        topic_filename='Position.z.jsonStream',
    )
    t0_position_z = max([e['_val']['Timestamp'] - timedelta(seconds=e['_session_time'])
                         for e in position_z['Position.z-Position']])

    car_data = parse_topic(
        session_path=session_path,
        topic_filename='CarData.z.jsonStream',
    )
    t0_car_data = max([e['_val']['Utc'] - timedelta(seconds=e['_session_time'])
                       for e in car_data['CarData.z-Entries']])
    
    return max(t0_position_z, t0_car_data)


def _get_topic_api_filenames(session_path: str) -> Iterator[str]:
    """Yields all the available raw data files for the session"""
    url = os.path.join(BASE_API_URL, session_path, 'Index.json')
    content = json.loads(requests.get(url).content)
    for vals in content['Feeds'].values():
        yield vals['StreamPath']


def parse_all_topics(session_path: str, *args, **kwargs) -> Dict[str, List[Dict]]:
    """Parses all the topics for a specified session and returns the parsed data as a dictionary."""
    topic_api_filenames = list(_get_topic_api_filenames(session_path))

    res = defaultdict(list)
    for api_filename in tqdm(topic_api_filenames):
        parsed = parse_topic(
            session_path=session_path,
            topic_filename=api_filename,
            *args, **kwargs
        )
        # Group data by collection for faster addition to the database
        for collection, vals in parsed.items():
            res[collection] += vals
    
    return dict(res)


@click.group()
def cli():
    pass


async def _ingest_session(year: int, meeting_key: int, session_key: int):
    logger.info('Retrieving session path')
    session_path = get_session_path(year=year, meeting_key=meeting_key, session_key=session_key)

    logger.info('Estimating t0')
    t0 = estimate_t0(session_path)

    logger.info('Parsing topics')
    content = parse_all_topics(
        session_path=session_path,
        session_key=session_key,
        meeting_key=meeting_key,
        t0=t0,
    )

    logger.info('Writing to DB')
    mongo_db = get_mongo_db()
    for collection_name, docs in tqdm(list(content.items())):
        await insert_data_async(collection_name=collection_name, docs=docs, mongo_db=mongo_db)


@cli.command()
@click.argument('year', type=int)
@click.argument('meeting_key', type=int)
@click.argument('session_key', type=int)
def ingest_session(*args, **kwargs):
    """Parses and saves raw F1 data to database for a specific session.
       Example usage: `python ingest_history.py ingest-session 2023 1141 7953`

       The session and meeting keys for 2023, for example, could be found here: https://livetiming.formula1.com/static/2023/Index.json
    """
    asyncio.run(_ingest_session(*args, **kwargs))


@cli.command()
@click.argument('year', type=int)
@click.argument('meeting_key', type=int)
def ingest_meeting(year: int, meeting_key: int):
    """Parses and saves raw F1 data to database for a specific meeting.
       Example usage: `python ingest_history.py ingest-meeting 2023 1141`

       The meeting keys for 2023, for example, could be found here: https://livetiming.formula1.com/static/2023/Index.json
    """
    for session_key in _get_session_keys(year=year, meeting_key=meeting_key):
        logger.info(f'----- Ingesting session `{session_key}` -----')
        asyncio.run(_ingest_session(year=year, meeting_key=meeting_key, session_key=session_key))


if __name__ == '__main__':
    cli()
