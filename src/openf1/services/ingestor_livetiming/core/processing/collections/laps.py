from collections import defaultdict
from copy import deepcopy
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Iterator

import pytz

from openf1.services.ingestor_livetiming.core.objects import (
    Collection,
    Document,
    Message,
)
from openf1.util.misc import to_datetime, to_timedelta


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
    source_topics = {
        "SessionInfo",
        "RaceControlMessages",
        "TimingAppData",
        "TimingData",
        "SessionData",
    }

    is_session_started: bool = False
    is_session_a_race: bool | None = None
    chequered_flag_date: datetime | None = None
    laps: defaultdict = field(default_factory=lambda: defaultdict(list))
    updated_laps: set = field(default_factory=set)  # laps updated since last message

    def _add_lap(self, driver_number: int, lap_number: int) -> Lap:
        new_lap = Lap(
            meeting_key=self.meeting_key,
            session_key=self.session_key,
            driver_number=driver_number,
            lap_number=lap_number,
        )
        self.laps[driver_number].append(new_lap)
        return new_lap

    def _get_current_lap(
        self,
        driver_number: int,
        timepoint: datetime,
        is_end_of_lap: bool = False,
    ) -> Lap | None:
        """
        Retrieves the current lap for a given driver.

        This method handles the creation of the first lap if it doesn't exist and
        correctly identifies the target lap for updates, even when data arrives
        out of order (e.g., sector data for a previous lap arriving after a new
        lap has already started).

        Args:
            driver_number (int): The number of the driver.
            timepoint (datetime): The timestamp of the current message being processed.
            is_end_of_lap (bool): Flag indicating if the data relates to the end of a lap.

        Returns:
            Lap | None: The current Lap object for the driver, or None if it should be skipped.
        """
        if driver_number not in self.laps:
            self._add_lap(driver_number=driver_number, lap_number=1)
        laps = self.laps[driver_number]
        current_lap = laps[-1]

        # Handle case where data from sector 2 is received after the creation
        # of the next lap
        if (
            is_end_of_lap
            and current_lap.date_start is not None
            and timepoint - current_lap.date_start < timedelta(seconds=10)
        ):
            # Sometimes, some extra data is sent at the beginning of a session. Skip it.
            if len(laps) < 2:
                return None
            current_lap = laps[-2]

        return current_lap

    def _infer_missing_lap_duration(self, lap: Lap):
        """
        Infers and updates missing lap duration if all three sector durations are
        available.
        """
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

    def _update_lap(
        self,
        driver_number: int,
        property: str,
        value: any,
        is_end_of_lap: bool = False,
        timepoint: datetime | None = None,
    ):
        """Updates a specific property of a driver's current lap."""
        lap = self._get_current_lap(
            driver_number, is_end_of_lap=is_end_of_lap, timepoint=timepoint
        )
        if lap is None:
            return

        old_value = getattr(lap, property)
        if value != old_value:
            setattr(lap, property, value)

            if property.startswith("duration_sector_"):
                self._infer_missing_lap_duration(lap)

            # During a race, discard laps that start after the checkered flag
            if (
                self.is_session_a_race
                and self.chequered_flag_date is not None
                and lap.date_start is not None
                and self.chequered_flag_date < lap.date_start
            ):
                return

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
        """Adds the status of a track segment to the current lap."""
        lap = self._get_current_lap(
            driver_number, is_end_of_lap=is_end_of_lap, timepoint=timepoint
        )
        if lap is None:
            return

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
        if message.topic == "SessionInfo":
            self.is_session_a_race = message.content["Type"].lower() == "race"
            return

        if message.topic == "SessionData" and self.is_session_a_race:
            status_series = message.content.get("StatusSeries")
            if not status_series:
                return
            if isinstance(status_series, dict):
                status_series = list(status_series.values())

            for item in status_series:
                date = to_datetime(item.get("Utc"))
                if date is not None:
                    date = pytz.utc.localize(date)
                status = item.get("SessionStatus")

                if date is not None and status == "Started":
                    for driver_number, laps in self.laps.items():
                        if laps and len(laps) == 1 and laps[0].lap_number == 1:
                            laps[0].date_start = date
                            self.updated_laps.add(laps[0])

        if message.topic == "RaceControlMessages":
            inner_messages = message.content["Messages"]
            if isinstance(inner_messages, dict):
                inner_messages = inner_messages.values()
            for data in inner_messages:
                if data["Message"].upper() == "CHEQUERED FLAG":
                    self.chequered_flag_date = message.timepoint
            return

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
                                    is_end_of_lap=sector_number > 1,
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
                                        is_end_of_lap=sector_number > 1,
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
                    lap_number = data["NumberOfLaps"]
                    if not isinstance(lap_number, int):
                        continue

                    # During a race, the first lap is not recorded as such
                    if self.is_session_a_race:
                        lap_number += 1

                    current_lap = self._get_current_lap(
                        driver_number=driver_number, timepoint=message.timepoint
                    )

                    if lap_number > current_lap.lap_number:
                        current_lap = self._add_lap(
                            driver_number=driver_number,
                            lap_number=lap_number,
                        )
                    if current_lap.date_start is None:
                        self._update_lap(
                            driver_number=driver_number,
                            property="date_start",
                            value=message.timepoint,
                        )

                        # Infer duration of first lap and first sector during a race
                        if self.is_session_a_race and current_lap.lap_number == 2:
                            first_lap = self.laps[driver_number][0]
                            if first_lap.lap_number == 1:
                                if (
                                    not first_lap.lap_duration
                                    and first_lap.date_start is not None
                                ):
                                    first_lap.lap_duration = round(
                                        (
                                            current_lap.date_start
                                            - first_lap.date_start
                                        ).total_seconds(),
                                        3,
                                    )
                                if (
                                    first_lap.lap_duration
                                    and not first_lap.duration_sector_1
                                    and first_lap.duration_sector_2
                                    and first_lap.duration_sector_3
                                ):
                                    first_lap.duration_sector_1 = round(
                                        first_lap.lap_duration
                                        - first_lap.duration_sector_2
                                        - first_lap.duration_sector_3,
                                        3,
                                    )

                if data.get("PitOut") is not None:
                    self._update_lap(
                        driver_number=driver_number,
                        property="is_pit_out_lap",
                        value=True,
                    )

                yield from deepcopy(self.updated_laps)
                self.updated_laps = set()
