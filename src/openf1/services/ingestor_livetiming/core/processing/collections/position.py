from dataclasses import dataclass
from datetime import datetime
from typing import Iterator

from loguru import logger

from openf1.services.ingestor_livetiming.core.objects import (
    Collection,
    Document,
    Message,
)


@dataclass(eq=False)
class Position(Document):
    meeting_key: int
    session_key: int
    driver_number: int
    date: datetime
    position: int

    @property
    def unique_key(self) -> tuple:
        return (self.date, self.driver_number)


class PositionCollection(Collection):
    name = "position"
    source_topics = {"TimingAppData"}

    def process_message(self, message: Message) -> Iterator[Position]:
        for driver_number, data in message.content["Lines"].items():
            try:
                yield Position(
                    meeting_key=self.meeting_key,
                    session_key=self.session_key,
                    driver_number=int(driver_number),
                    date=message.timepoint,
                    position=data["Line"],
                )
            except:
                pass
