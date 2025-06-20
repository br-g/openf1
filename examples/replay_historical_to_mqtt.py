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
    grouped: dict[str, list[str]] = {}
    for m in messages:
        grouped.setdefault(m.topic, []).append(
            json.dumps(
                {
                    "topic": m.topic,
                    "timepoint": m.timepoint,
                    "content": m.content,
                },
                default=json_serializer,
            )
        )

    for topic, msgs in grouped.items():
        await publish_messages_to_mqtt(topic=f"historical/{topic}", messages=msgs)
    print("Publishing completed")


if __name__ == "__main__":
    asyncio.run(main())
