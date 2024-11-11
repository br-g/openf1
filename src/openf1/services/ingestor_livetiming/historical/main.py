import json
import re
from datetime import datetime, timedelta
from functools import lru_cache

import pytz
import requests
import typer
from loguru import logger
from tqdm import tqdm

from openf1.services.ingestor_livetiming.core.decoding import decode
from openf1.services.ingestor_livetiming.core.objects import (
    Document,
    Message,
    get_collections,
    get_source_topics,
)
from openf1.services.ingestor_livetiming.core.processing.main import process_messages
from openf1.util.misc import join_url
from openf1.util.db import DbBatchIngestor
from openf1.util.misc import join_url, json_serializer, to_datetime, to_timedelta
from openf1.util.schedule import get_meeting_keys
from openf1.util.schedule import get_schedule as _get_schedule
from openf1.util.schedule import get_session_keys

cli = typer.Typer()

# Flag to determine if the script is being run from the command line
_is_called_from_cli = False


@cli.command()
def get_schedule(year: int) -> dict:
    schedule = _get_schedule(year)

    if _is_called_from_cli:
        schedule_json = json.dumps(schedule, indent=2, default=json_serializer)
        print(schedule_json)

    return schedule


@lru_cache()
def get_session_url(year: int, meeting_key: int, session_key: int) -> str:
    """Retrieves the URL for downloading raw data of a specific session"""
    BASE_URL = "https://livetiming.formula1.com/static"

    schedule = _get_schedule(year)

    session_url = None
    for meeting in schedule["Meetings"]:
        if meeting["Key"] == meeting_key:
            for session in meeting["Sessions"]:
                if session["Key"] == session_key:
                    path = session["Path"]
                    session_url = join_url(BASE_URL, path)

    if session_url is None:
        raise ValueError(
            f"Session not found (year: `{year}`, meeting_key: `{meeting_key}`, "
            f"session_key: `{session_key}`)"
        )

    return session_url


def _list_topics(session_url: str) -> list[str]:
    """Returns all the available raw data filenames for the session"""
    index_url = join_url(session_url, "Index.json")
    index_response = requests.get(index_url)
    index_content = json.loads(index_response.content)

    filenames = [v["StreamPath"] for v in index_content["Feeds"].values()]
    topics = [f[: -len(".jsonStream")] for f in filenames if f.endswith(".jsonStream")]
    topics = sorted(topics)

    return topics


@cli.command()
def list_topics(
    year: int,
    meeting_key: int,
    session_key: int,
) -> list[str]:
    session_url = get_session_url(
        year=year, meeting_key=meeting_key, session_key=session_key
    )
    topics = _list_topics(session_url)

    if _is_called_from_cli:
        print(topics)
    return topics


@lru_cache()
def _get_topic_content(session_url: str, topic: str) -> list[str]:
    topic_filename = f"{topic}.jsonStream"
    url_topic = join_url(session_url, topic_filename)
    topic_content = requests.get(url_topic).text.split("\r\n")
    return topic_content


@cli.command()
def get_topic_content(
    year: int, meeting_key: int, session_key: int, topic: str
) -> list[str]:
    session_url = get_session_url(
        year=year, meeting_key=meeting_key, session_key=session_key
    )
    content = _get_topic_content(session_url=session_url, topic=topic)

    if _is_called_from_cli:
        print("\n".join(content))
    return content


def _parse_line(line: str) -> tuple[timedelta | None, str | None]:
    """Parses a line to extract the duration since session start and raw data.

    The line is expected to be formatted as follows:
    (duration since session start, raw data)
    """
    pattern = r"(\d+:\d+:\d+\.\d+)(.*)"
    match = re.match(pattern, line)
    if match is None:
        return None, None
    session_time = to_timedelta(match.group(1))
    raw_data = match.group(2).strip("\r").strip('"')
    return session_time, raw_data


def _parse_and_decode_topic_content(
    topic: str,
    topic_raw_content: list[str],
    t0: datetime,
) -> list[Message]:
    messages = []
    for line in topic_raw_content:
        if len(line) == 0:
            continue
        session_time, content = _parse_line(line)

        if session_time is None:
            continue

        if isinstance(content, str):
            content = decode(content)

        messages.append(
            Message(
                topic=topic,
                content=content,
                timepoint=t0 + session_time,
            )
        )

    return messages


@lru_cache()
def _get_t0(session_url: str) -> datetime:
    """Calculates the most likely start time of a session (t0) based on
    Position and CarData messages.
    The calculation method comes from the FastF1 package (https://github.com/theOehrly/Fast-F1/blob/317bacf8c61038d7e8d0f48165330167702b349f/fastf1/core.py#L2208).
    """
    t_ref = datetime(1970, 1, 1)
    t0_candidates = []

    position_content = _get_topic_content(session_url=session_url, topic="Position.z")
    position_messages = _parse_and_decode_topic_content(
        topic="Position.z",
        topic_raw_content=position_content,
        t0=t_ref,
    )
    for message in position_messages:
        for record in message.content["Position"]:
            timepoint = to_datetime(record["Timestamp"])
            session_time = message.timepoint - t_ref
            t0_candidates.append(timepoint - session_time)

    cardata_content = _get_topic_content(session_url=session_url, topic="CarData.z")
    cardata_messages = _parse_and_decode_topic_content(
        topic="CarData.z",
        topic_raw_content=cardata_content,
        t0=t_ref,
    )
    for message in cardata_messages:
        for record in message.content["Entries"]:
            timepoint = to_datetime(record["Utc"])
            session_time = message.timepoint - t_ref
            t0_candidates.append(timepoint - session_time)

    t0_estimate = max(t0_candidates)
    t0_estimate = pytz.utc.localize(t0_estimate)

    return t0_estimate


@cli.command()
def get_t0(year: int, meeting_key: int, session_key: int) -> datetime:
    session_url = get_session_url(
        year=year, meeting_key=meeting_key, session_key=session_key
    )
    t0 = _get_t0(session_url)

    if _is_called_from_cli:
        print(t0)
    return t0


def _get_messages(session_url: str, topics: list[str], t0: datetime) -> list[Message]:
    messages = []
    for topic in topics:
        raw_content = _get_topic_content(
            session_url=session_url,
            topic=topic,
        )
        messages += _parse_and_decode_topic_content(
            topic=topic,
            topic_raw_content=raw_content,
            t0=t0,
        )
    messages = sorted(messages, key=lambda m: (m.timepoint, m.topic))
    return messages


@cli.command()
def get_messages(
    year: int,
    meeting_key: int,
    session_key: int,
    topics: list[str],
    verbose: bool = True,
) -> list[Message]:
    session_url = get_session_url(
        year=year, meeting_key=meeting_key, session_key=session_key
    )
    if verbose:
        logger.info(f"Session URL: {session_url}")

    t0 = _get_t0(session_url)
    if verbose:
        logger.info(f"t0: {t0}")

    messages = _get_messages(session_url=session_url, topics=topics, t0=t0)
    if verbose:
        logger.info(f"Fetched {len(messages)} messages")

    if _is_called_from_cli:
        messages_json = json.dumps(messages, indent=2, default=json_serializer)
        print(messages_json)

    return messages


def _get_processed_documents(
    year: int,
    meeting_key: int,
    session_key: int,
    collection_names: list[str],
    verbose: bool = True,
) -> dict[str, list[Document]]:
    session_url = get_session_url(
        year=year, meeting_key=meeting_key, session_key=session_key
    )
    if verbose:
        logger.info(f"Session URL: {session_url}")

    t0 = _get_t0(session_url)
    if verbose:
        logger.info(f"t0: {t0}")

    topics = set().union(*[get_source_topics(n) for n in collection_names])
    topics = sorted(list(topics))
    if verbose:
        logger.info(f"Topics used: {topics}")

    messages = _get_messages(session_url=session_url, topics=topics, t0=t0)
    if verbose:
        logger.info(f"Fetched {len(messages)} messages")

    if verbose:
        logger.info(f"Starting processing")

    docs_by_collection = process_messages(
        messages=messages, meeting_key=meeting_key, session_key=session_key
    )
    docs_by_collection = {
        col: docs_by_collection[col] if col in docs_by_collection else []
        for col in collection_names
    }

    if verbose:
        n_docs = sum(len(d) for d in docs_by_collection.values())
        logger.info(f"Processed {n_docs} documents")

    return docs_by_collection


@cli.command()
def get_processed_documents(
    year: int,
    meeting_key: int,
    session_key: int,
    collection_names: list[str],
    verbose: bool = True,
) -> dict[str, list[Document]]:
    docs_by_collection = _get_processed_documents(
        year=year,
        meeting_key=meeting_key,
        session_key=session_key,
        collection_names=collection_names,
        verbose=verbose,
    )

    if _is_called_from_cli:
        docs_by_collection = {
            k: [d.to_mongo_doc() for d in v] for k, v in docs_by_collection.items()
        }
        docs_by_collection_json = json.dumps(
            docs_by_collection, indent=2, default=json_serializer
        )
        print(docs_by_collection_json)

    return docs_by_collection


@cli.command()
def ingest_collections(
    year: int,
    meeting_key: int,
    session_key: int,
    collection_names: list[str],
    verbose: bool = True,
):
    docs_by_collection = _get_processed_documents(
        year=year,
        meeting_key=meeting_key,
        session_key=session_key,
        collection_names=collection_names,
        verbose=verbose,
    )

    if verbose:
        logger.info(f"Inserting documents to DB")
    for collection, docs in tqdm(list(docs_by_collection.items()), disable=not verbose):
        docs_mongo = [d.to_mongo_doc() for d in docs]
        DbBatchIngestor().add_and_flush(collection=collection, docs=docs_mongo)


@cli.command()
def ingest_session(year: int, meeting_key: int, session_key: int, verbose: bool = True):
    collections = get_collections(meeting_key=meeting_key, session_key=session_key)
    collection_names = sorted([c.__class__.name for c in collections])

    if verbose:
        logger.info(
            f"Ingesting {len(collection_names)} collections: {collection_names}"
        )

    ingest_collections(
        year=year,
        meeting_key=meeting_key,
        session_key=session_key,
        collection_names=collection_names,
        verbose=verbose,
    )


@cli.command()
def ingest_meeting(year: int, meeting_key: int, verbose: bool = True):
    session_keys = get_session_keys(year=year, meeting_key=meeting_key)
    if verbose:
        logger.info(f"{len(session_keys)} sessions found: {session_keys}")

    for session_key in session_keys:
        if verbose:
            logger.info(f"Ingesting session {session_key}")
        ingest_session(
            year=year, meeting_key=meeting_key, session_key=session_key, verbose=False
        )


@cli.command()
def ingest_season(year: int, verbose: bool = True):
    meeting_keys = get_meeting_keys(year)
    if verbose:
        logger.info(f"{len(meeting_keys)} meetings found: {meeting_keys}")

    for meeting_key in meeting_keys:
        if verbose:
            logger.info(f"Ingesting meeting {meeting_key}")
        ingest_meeting(year=year, meeting_key=meeting_key, verbose=False)


if __name__ == "__main__":
    _is_called_from_cli = True
    cli()
