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
class RaceControl(Document):
    meeting_key: int
    session_key: int
    date: datetime | None
    driver_number: int | None
    lap_number: int | None
    category: str | None
    flag: str | None
    scope: str | None
    sector: int | None
    message: str | None

    @property
    def unique_key(self) -> tuple:
        return (
            self.date,
            self.driver_number,
            self.lap_number,
            self.category,
            self.flag,
            self.scope,
            self.sector,
        )


class RaceControlCollection(Collection):
    name = "race_control"
    source_topics = {"RaceControlMessages"}

    def process_message(self, message: Message) -> Iterator[RaceControl]:
        inner_messages = message.content["Messages"]
        if isinstance(inner_messages, dict):
            inner_messages = inner_messages.values()

        for data in inner_messages:
            if not isinstance(data, dict):
                continue

            try:
                date = to_datetime(data["Utc"])
                date = pytz.utc.localize(date)
            except Exception as e:
                logger.warning(e)
                date = None

            try:
                driver_number = int(data.get("RacingNumber"))
            except Exception as e:
                logger.warning(e)
                driver_number = None

            yield RaceControl(
                meeting_key=self.meeting_key,
                session_key=self.session_key,
                date=date,
                driver_number=driver_number,
                lap_number=data.get("Lap"),
                category=data.get("Category"),
                flag=data.get("Flag"),
                scope=data.get("Scope"),
                sector=data.get("Sector"),
                message=data.get("Message"),
            )
