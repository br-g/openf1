from dataclasses import dataclass
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
    date: datetime
    pit_duration: float | None  # deprecated, same as 'pit_lane_time'
    pit_lane_time: float | None
    pit_stop_time: float | None

    @property
    def unique_key(self) -> tuple:
        return (self.session_key, self.lap_number, self.driver_number)


@dataclass
class PitCollection(Collection):
    name = "pit"
    source_topics = {"PitLaneTimeCollection", "PitStopSeries"}
    pits: dict

    def process_message(self, message: Message) -> Iterator[Pit]:
        if message.topic == "PitStopSeries":
            for driver_number, data in message.content["PitTimes"].items():
                try:
                    driver_number = int(driver_number)
                except:
                    continue

                if not isinstance(data, list):
                    continue

                for pit_info in data:
                    if "PitStop" not in pit_info:
                        continue

                    try:
                        timestamp = pit_info["Timestamp"]
                        date = to_datetime(timestamp)
                        date = pytz.utc.localize(date)
                    except:
                        continue

                    try:
                        lap_number = int(pit_info["PitStop"]["Lap"])
                    except:
                        continue

                    try:
                        pit_lane_time = float(pit_info["PitStop"]["PitLaneTime"])
                    except:
                        pit_lane_time = None

                    try:
                        pit_stop_time = float(pit_info["PitStop"]["PitStopTime"])
                    except:
                        pit_stop_time = None

                    pit = Pit(
                        meeting_key=self.meeting_key,
                        session_key=self.session_key,
                        driver_number=driver_number,
                        date=date,
                        pit_duration=pit_lane_time,
                        pit_lane_time=pit_lane_time,
                        pit_stop_time=pit_stop_time,
                        lap_number=lap_number,
                    )

                    self.pits[pit.unique_key] = pit
                    yield pit

        # Fallback: use collection "PitLaneTimeCollection" in case "PitStopSeries" is not available.
        # "PitLaneTimeCollection" has less data and is less accurate.
        elif message.topic == "PitLaneTimeCollection":
            for driver_number, data in message.content["PitTimes"].items():
                try:
                    driver_number = int(driver_number)
                except:
                    continue

                if not isinstance(data, dict):
                    continue

                try:
                    pit_lane_time = float(data["Duration"])
                except:
                    pit_lane_time = None

                try:
                    lap_number = int(data["Lap"])
                except:
                    continue

                pit = Pit(
                    meeting_key=self.meeting_key,
                    session_key=self.session_key,
                    driver_number=driver_number,
                    date=message.timepoint,
                    pit_duration=pit_lane_time,
                    pit_lane_time=pit_lane_time,
                    pit_stop_time=None,
                    lap_number=lap_number,
                )
                if pit.unique_key not in self.pits:
                    self.pits[pit.unique_key] = pit
                    yield pit
