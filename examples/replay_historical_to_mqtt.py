import asyncio
import json

from openf1.services.ingestor_livetiming.historical import main as historical
from openf1.util.mqtt import publish_messages_to_mqtt
from openf1.util.misc import json_serializer

YEAR = 2025
MEETING_KEY = 1263
SESSION_KEY = 9963


async def main() -> None:
    topics = historical.list_topics(
        year=YEAR, meeting_key=MEETING_KEY, session_key=SESSION_KEY
    )
    print(f"Found {len(topics)} topics: {topics}")

    messages = historical.get_messages(
        year=YEAR,
        meeting_key=MEETING_KEY,
        session_key=SESSION_KEY,
        topics=topics,
        verbose=True,
    )
    print(f"Publishing {len(messages)} messages")
    prev = None
    for m in messages:
        if prev is not None:
            delta = (m.timepoint - prev).total_seconds()
            if delta > 0:
                await asyncio.sleep(delta)
        msg = json.dumps(
            {
                "topic": m.topic,
                "timepoint": m.timepoint,
                "content": m.content,
            },
            default=json_serializer,
        )
        await publish_messages_to_mqtt(topic=f"historical/{m.topic}", messages=[msg])
        prev = m.timepoint
    print("Replay completed")


if __name__ == "__main__":
    asyncio.run(main())
