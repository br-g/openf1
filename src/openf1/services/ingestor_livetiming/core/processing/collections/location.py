from dataclasses import dataclass
from datetime import datetime
from typing import Iterator

import pytz
from loguru import logger

from openf1.services.ingestor_livetiming.core.objects import (
    Collection,
    Document,
    Message,
)
from openf1.util.misc import to_datetime


@dataclass(eq=False)
class CarData(Document):
    meeting_key: int
    session_key: int
    driver_number: int
    date: datetime
    x: int | None
    y: int | None
    z: int | None

    @property
    def unique_key(self) -> tuple:
        return (self.date, self.driver_number)


class LocationCollection(Collection):
    name = "location"
    source_topics = {"Position.z"}

    def process_message(self, message: Message) -> Iterator[CarData]:
        for content in message.content["Position"]:
            if not isinstance(content, dict):
                continue

            try:
                timestamp = content["Timestamp"]
                date = to_datetime(timestamp)
                date = pytz.utc.localize(date)
            except:
                continue

            entries = content.get("Entries")
            if not isinstance(entries, dict):
                continue

            for driver_number, data in entries.items():
                try:
                    driver_number = int(driver_number)
                except:
                    continue

                if not isinstance(data, dict):
                    continue

                yield CarData(
                    meeting_key=self.meeting_key,
                    session_key=self.session_key,
                    driver_number=driver_number,
                    date=date,
                    x=data.get("X"),
                    y=data.get("Y"),
                    z=data.get("Z"),
                )
