import asyncio
import json
import os

from loguru import logger

from openf1.services.ingestor_livetiming.core.decoding import decode
from openf1.services.ingestor_livetiming.core.objects import Document, Message
from openf1.services.ingestor_livetiming.core.processing.main import process_message
from openf1.util.db import insert_data_async
from openf1.util.misc import json_serializer, to_datetime

if "OPENF1_MQTT_URL" in os.environ:
    from openf1.util.mqtt import publish_messages_to_mqtt

# Store keys values found in data
_meeting_key = None
_session_key = None


def _parse_message(line: str) -> Message:
    topic, content, timepoint = eval(line)

    if isinstance(content, str):
        content = decode(content)

    timepoint = to_datetime(timepoint)

    return Message(
        topic=topic,
        content=content,
        timepoint=timepoint,
    )


def _process_message(message: Message) -> dict[str, list[Document]] | None:
    """Processes a Message object and returns Documents organized by Collection"""
    global _meeting_key
    global _session_key

    if message.topic == "SessionInfo":
        _meeting_key = message.content["Meeting"]["Key"]
        _session_key = message.content["Key"]
        logger.info(f"meeting key: {_meeting_key}, session key: {_session_key}")

    if _meeting_key is None and _session_key is None:
        logger.warning(
            "meeting_key and session_key not yet received. "
            f"Can't process message of topic '{message.topic}'."
        )
        return None

    docs_by_collection = process_message(
        meeting_key=_meeting_key,
        session_key=_session_key,
        message=message,
    )
    return docs_by_collection


async def ingest_line(line: str):
    """Asynchronously ingests a single line of raw data"""
    if (
        "SessionInfo" not in line
        and "RaceControlMessages" not in line
        and "TimingAppData" not in line
        and "TimingData" not in line
        and "DriverList" not in line
    ):
        return

    message = _parse_message(line)
    docs_by_collection = _process_message(message)
    if docs_by_collection is None:
        return
    for collection, docs in docs_by_collection.items():
        docs_mongo = [await d.to_mongo_doc_async() for d in docs]
        if "OPENF1_MQTT_URL" in os.environ:
            docs_mongo_json = [
                json.dumps(d, default=json_serializer) for d in docs_mongo
            ]
            await publish_messages_to_mqtt(
                topic=f"v1/{collection}", messages=docs_mongo_json
            )
        await insert_data_async(collection_name=collection, docs=docs_mongo)


async def ingest_file(filepath: str):
    """Ingests data from the specified file.

    This function first reads and processes all existing lines in the file.
    After processing existing content, it continuously watches for new lines
    appended to the file and processes them in real-time.
    """

    with open(filepath, "r") as file:
        # Read and ingest existing lines
        lines = file.readlines()
        for line in lines:
            await ingest_line(line)

        # Move to the end of the file
        file.seek(0, 2)

        # Watch for new lines
        while True:
            line = file.readline()
            if not line:
                await asyncio.sleep(0.1)  # Sleep a bit before trying again
                continue
            await ingest_line(line)
