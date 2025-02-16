from dataclasses import dataclass
from datetime import datetime
from typing import Iterator

from loguru import logger

from openf1.services.ingestor_livetiming.core.objects import (
    Collection,
    Document,
    Message,
)


def _parse_time_delta(time_delta: str | float | None) -> str | float | None:
    if time_delta is None:
        return None

    # Handle leader
    if str(time_delta).upper().startswith("LAP"):
        return 0.0

    if str(time_delta).startswith("+"):
        # Handle cases like '+1 LAP'
        if "LAP" in time_delta:
            return time_delta

        # Handle cases like '+1:09.473'
        elif ":" in time_delta:
            minutes, seconds = map(float, time_delta[1:].split(":"))
            return minutes * 60 + seconds

        # Handle cases like '+6.924'
        else:
            return float(time_delta[1:])

    return time_delta


@dataclass(eq=False)
class Interval(Document):
    meeting_key: int
    session_key: int
    driver_number: int
    gap_to_leader: float | None
    interval: float | None
    date: datetime

    @property
    def unique_key(self) -> tuple:
        return (self.date, self.driver_number)


class IntervalsCollection(Collection):
    name = "intervals"
    source_topics = {"DriverRaceInfo"}

    def process_message(self, message: Message) -> Iterator[Interval]:
        for driver_number, data in message.content.items():
            try:
                driver_number = int(driver_number)
            except:
                continue

            if not isinstance(data, dict):
                continue

            if data.get("Gap") is None and data.get("Interval") is None:
                continue

            gap_to_leader = _parse_time_delta(data.get("Gap"))
            interval = _parse_time_delta(data.get("Interval"))

            yield Interval(
                meeting_key=self.meeting_key,
                session_key=self.session_key,
                driver_number=driver_number,
                gap_to_leader=gap_to_leader,
                interval=interval,
                date=message.timepoint,
            )
