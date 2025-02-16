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
class Pit(Document):
    meeting_key: int
    session_key: int
    driver_number: int
    date: datetime
    pit_duration: int | None
    lap_number: int | None

    @property
    def unique_key(self) -> tuple:
        return (self.date, self.driver_number)


class PitCollection(Collection):
    name = "pit"
    source_topics = {"PitLaneTimeCollection"}

    def process_message(self, message: Message) -> Iterator[Pit]:
        for driver_number, data in message.content["PitTimes"].items():
            try:
                driver_number = int(driver_number)
            except Exception as e:
                logger.warning(e)
                continue

            if not isinstance(data, dict):
                continue

            try:
                pit_duration = float(data["Duration"])
            except Exception as e:
                logger.warning(e)
                pit_duration = None

            try:
                lap_number = int(data["Lap"])
            except Exception as e:
                logger.warning(e)
                lap_number = None

            yield Pit(
                meeting_key=self.meeting_key,
                session_key=self.session_key,
                driver_number=driver_number,
                date=message.timepoint,
                pit_duration=pit_duration,
                lap_number=lap_number,
            )
