from collections import defaultdict
from copy import deepcopy
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Iterator

from loguru import logger

from openf1.services.ingestor_livetiming.core.objects import (
    Collection,
    Document,
    Message,
)
from openf1.util.misc import to_timedelta


@dataclass(eq=False)
class Lap(Document):
    meeting_key: int
    session_key: int
    driver_number: int
    lap_number: int
    date_start: datetime | None = None
    duration_sector_1: float | None = None  # in seconds
    duration_sector_2: float | None = None  # in seconds
    duration_sector_3: float | None = None  # in seconds
    i1_speed: int | None = None  # in km/h
    i2_speed: int | None = None  # in km/h
    is_pit_out_lap: bool = False
    lap_duration: float | None = None  # in seconds
    segments_sector_1: list[int | None] | None = None
    segments_sector_2: list[int | None] | None = None
    segments_sector_3: list[int | None] | None = None
    st_speed: int | None = None  # in km/h

    @property
    def unique_key(self) -> tuple:
        return (self.session_key, self.lap_number, self.driver_number)


@dataclass
class LapsCollection(Collection):
    name = "laps"
    source_topics = {"TimingAppData", "TimingData"}

    is_session_started: bool = False
    laps: defaultdict = field(default_factory=lambda: defaultdict(list))
    updated_laps: set = field(default_factory=set)  # laps updated since last message

    def _add_lap(self, driver_number: int, lap_number: int):
        new_lap = Lap(
            meeting_key=self.meeting_key,
            session_key=self.session_key,
            driver_number=driver_number,
            lap_number=lap_number,
        )
        self.laps[driver_number].append(new_lap)

    def _get_latest_lap(self, driver_number: int) -> dict:
        if driver_number not in self.laps:
            self._add_lap(driver_number=driver_number, lap_number=1)
        laps = self.laps[driver_number]
        return laps[-1]

    def _infer_missing_lap_duration(self, lap: Lap):
        """Infers and updates missing lap duration when sectors duration are available"""
        if (
            not lap.lap_duration
            and lap.duration_sector_1
            and lap.duration_sector_2
            and lap.duration_sector_3
        ):
            lap.lap_duration = round(
                lap.duration_sector_1 + lap.duration_sector_2 + lap.duration_sector_3,
                3,
            )

    def _infer_missing_sector_duration(self, lap: Lap):
        """Infers and updates a single missing sector duration for a driver's lap"""
        if lap.lap_duration is None:
            return

        n_missing_sector_durations = 0
        missing_sector_number = None
        sector_durations_sum = 0

        for sector_number in {1, 2, 3}:
            sector_duration = getattr(lap, f"duration_sector_{sector_number}", None)
            if sector_duration is None:
                n_missing_sector_durations += 1
                missing_sector_number = sector_number
            else:
                sector_durations_sum += sector_duration

        if n_missing_sector_durations == 1:
            infered_duration = lap.lap_duration - sector_durations_sum
            if infered_duration > 0:
                setattr(
                    lap,
                    f"duration_sector_{missing_sector_number}",
                    round(infered_duration, 3),
                )

    def _update_lap(
        self,
        driver_number: int,
        property: str,
        value: any,
        is_end_of_lap: bool = False,
        timepoint: datetime | None = None,
    ):
        """Updates a property of the current lap of a driver"""
        lap = self._get_latest_lap(driver_number)

        # Handle case where data from sector 2 is received after the creation
        # of the next lap
        if (
            is_end_of_lap
            and lap.date_start is not None
            and timepoint - lap.date_start < timedelta(seconds=10)
        ):
            if len(self.laps[driver_number]) < 2:
                logger.error(
                    f"Can't update lap (driver_number: {driver_number}, "
                    f"property: {property}, is_end_of_lap: {is_end_of_lap})"
                )
                return
            lap = self.laps[driver_number][-2]

        old_value = getattr(lap, property)
        if value != old_value:
            setattr(lap, property, value)

            if property == "lap_duration":
                self._infer_missing_sector_duration(lap)

            if property.startswith("duration_sector_"):
                self._infer_missing_sector_duration(lap)
                self._infer_missing_lap_duration(lap)

            self.updated_laps.add(lap)

    def _add_segment_status(
        self,
        driver_number: int,
        sector_number: int,
        segment_number: int,
        segment_status: int,
        is_end_of_lap: bool,
        timepoint: datetime,
    ):
        lap = self._get_latest_lap(driver_number)

        # Get existing segment status
        property = f"segments_sector_{sector_number}"
        segments_status = getattr(lap, property)

        # Add new status
        if segments_status is None:
            segments_status = []
        while segment_number >= len(segments_status):
            segments_status.append(None)
        segments_status[segment_number] = segment_status
        self._update_lap(
            driver_number=driver_number,
            property=property,
            value=segments_status,
            is_end_of_lap=is_end_of_lap,
            timepoint=timepoint,
        )

    def process_message(self, message: Message) -> Iterator[Lap]:
        if "Lines" not in message.content:
            return

        for driver_number, data in message.content["Lines"].items():
            if message.topic == "TimingAppData" and data.get("Stints"):
                self.is_session_started = True

            elif self.is_session_started and message.topic == "TimingData":
                try:
                    driver_number = int(driver_number)
                except:
                    continue

                if driver_number != 10:
                    continue
                print(message.timepoint, data)

                if not isinstance(data, dict):
                    continue

                try:
                    lap_time = data.get("LastLapTime", {}).get("Value")
                    if isinstance(lap_time, str):
                        lap_time = to_timedelta(lap_time)
                except:
                    lap_time = None

                if isinstance(lap_time, timedelta):
                    self._update_lap(
                        driver_number=driver_number,
                        property="lap_duration",
                        value=lap_time.total_seconds(),
                        is_end_of_lap=True,
                        timepoint=message.timepoint,
                    )

                sectors = data.get("Sectors")
                if isinstance(sectors, dict):
                    for sector_number_s, sector_data in sectors.items():
                        try:
                            sector_number = int(sector_number_s) + 1
                        except:
                            continue

                        if not isinstance(sector_data, dict):
                            continue

                        if "Value" in sector_data:
                            try:
                                duration = float(sector_data["Value"])
                            except:
                                duration = None
                            if duration is not None:
                                self._update_lap(
                                    driver_number=driver_number,
                                    property=f"duration_sector_{sector_number}",
                                    value=duration,
                                    is_end_of_lap=sector_number == 3,
                                    timepoint=message.timepoint,
                                )

                        if "Segments" in sector_data:
                            segments_data = sector_data["Segments"]
                            if isinstance(segments_data, dict):
                                for (
                                    segment_number,
                                    segment_data,
                                ) in segments_data.items():
                                    try:
                                        segment_number = int(segment_number)
                                    except:
                                        continue
                                    if not isinstance(segment_data, dict):
                                        continue
                                    self._add_segment_status(
                                        driver_number=driver_number,
                                        sector_number=sector_number,
                                        segment_number=segment_number,
                                        segment_status=segment_data.get("Status"),
                                        is_end_of_lap=sector_number == 3,
                                        timepoint=message.timepoint,
                                    )

                speeds = data.get("Speeds")
                if isinstance(speeds, dict):
                    for label, speed_data in speeds.items():
                        if not isinstance(label, str):
                            continue
                        if not isinstance(speed_data, dict):
                            continue
                        if label == "ST" or label.startswith("I"):
                            try:
                                value = int(speed_data.get("Value"))
                            except:
                                continue
                            self._update_lap(
                                driver_number=driver_number,
                                property=f"{label.lower()}_speed",
                                value=value,
                            )

                if data.get("NumberOfLaps") is not None:
                    latest_lap = self._get_latest_lap(driver_number=driver_number)
                    if data["NumberOfLaps"] > latest_lap.lap_number:
                        self._add_lap(
                            driver_number=driver_number, lap_number=data["NumberOfLaps"]
                        )
                    self._update_lap(
                        driver_number=driver_number,
                        property="date_start",
                        value=message.timepoint,
                    )

                if data.get("PitOut") is not None:
                    self._update_lap(
                        driver_number=driver_number,
                        property="is_pit_out_lap",
                        value=True,
                    )

                yield from deepcopy(self.updated_laps)
                self.updated_laps = set()
