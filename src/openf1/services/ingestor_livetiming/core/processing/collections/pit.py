from dataclasses import dataclass, field
from datetime import datetime
from typing import Iterator

import pytz

from openf1.services.ingestor_livetiming.core.objects import (
    Collection,
    Document,
    Message,
)
from openf1.util.misc import to_datetime


@dataclass(eq=False)
class Pit(Document):
    meeting_key: int
    session_key: int
    lap_number: int
    driver_number: int
    date: datetime | None
    pit_duration: float | None  # deprecated, same as 'lane_duration'
    lane_duration: float | None
    stop_duration: float | None

    @property
    def unique_key(self) -> tuple:
        return (self.session_key, self.lap_number, self.driver_number)


@dataclass
class PitCollection(Collection):
    name = "pit"
    source_topics = {"PitLaneTimeCollection", "PitStopSeries"}
    pits: dict = field(default_factory=dict)

    def process_message(self, message: Message) -> Iterator[Pit]:
        if message.topic == "PitStopSeries":
            for driver_number, data in message.content["PitTimes"].items():
                try:
                    driver_number = int(driver_number)
                except:
                    continue

                if isinstance(data, dict):
                    data = list(data.values())
                elif not isinstance(data, list):
                    continue

                for pit_info in data:
                    if not isinstance(pit_info, dict):
                        continue

                    if "PitStop" not in pit_info:
                        continue

                    try:
                        timestamp = pit_info["Timestamp"]
                        date = to_datetime(timestamp)
                        date = pytz.utc.localize(date)
                    except:
                        date = None

                    try:
                        lap_number = int(pit_info["PitStop"]["Lap"])
                    except:
                        continue

                    try:
                        lane_duration = float(pit_info["PitStop"]["PitLaneTime"])
                    except:
                        lane_duration = None

                    try:
                        stop_duration = float(pit_info["PitStop"]["PitStopTime"])
                    except:
                        stop_duration = None

                    pit = Pit(
                        meeting_key=self.meeting_key,
                        session_key=self.session_key,
                        driver_number=driver_number,
                        date=date,
                        pit_duration=lane_duration,
                        lane_duration=lane_duration,
                        stop_duration=stop_duration,
                        lap_number=lap_number,
                    )

                    self.pits[pit.unique_key] = pit
                    yield pit

        # Fallback: use collection "PitLaneTimeCollection" in case "PitStopSeries" is not available.
        # "PitLaneTimeCollection" has less details and is less accurate.
        elif message.topic == "PitLaneTimeCollection":
            for driver_number, data in message.content["PitTimes"].items():
                try:
                    driver_number = int(driver_number)
                except:
                    continue

                if not isinstance(data, dict):
                    continue

                try:
                    lane_duration = float(data["Duration"])
                except:
                    lane_duration = None

                try:
                    lap_number = int(data["Lap"])
                except:
                    continue

                pit = Pit(
                    meeting_key=self.meeting_key,
                    session_key=self.session_key,
                    driver_number=driver_number,
                    date=message.timepoint,
                    pit_duration=lane_duration,
                    lane_duration=lane_duration,
                    stop_duration=None,
                    lap_number=lap_number,
                )
                if pit.unique_key not in self.pits:
                    self.pits[pit.unique_key] = pit
                    yield pit
