from collections import defaultdict
from copy import deepcopy
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Iterator

from openf1.services.ingestor_livetiming.core.objects import (
    Collection,
    Document,
    Message,
)


@dataclass(eq=False)
class Stint(Document):
    meeting_key: int
    session_key: int
    stint_number: int
    driver_number: int
    lap_start: int
    lap_end: int
    compound: str | None = None
    tyre_age_at_start: int | None = None
    _date_start_last_lap: datetime | None = None

    @property
    def unique_key(self) -> tuple:
        return (self.session_key, self.stint_number, self.driver_number)


@dataclass
class StintsCollection(Collection):
    name = "stints"
    source_topics = {"TimingAppData", "TimingData"}

    stints: defaultdict = field(default_factory=lambda: defaultdict(dict))
    updated_stints: set = field(
        default_factory=set
    )  # stints updated since last message

    def _get_last_stint(self, driver_number: int) -> Stint | None:
        stint_numbers = self.stints[driver_number].keys()
        if len(stint_numbers) == 0:
            return None

        stint_numbers = [int(n) for n in stint_numbers]
        last_stint_number = max(stint_numbers)
        return self.stints[driver_number][last_stint_number]

    def _update_stint(
        self, driver_number: int, stint_number: int, property: str, value: any
    ):
        stint = self.stints[driver_number][stint_number]
        old_value = getattr(stint, property)
        if value != old_value:
            setattr(stint, property, value)
            self.updated_stints.add(stint)

    def _add_stint(self, driver_number: int, stint_number: int, timepoint: datetime):
        last_stint = self._get_last_stint(driver_number)

        # Sometimes, lap information arrives before stint information.
        # We detect this using time points and correct it.
        if (
            last_stint is not None
            and last_stint._date_start_last_lap is not None
            and timepoint - last_stint._date_start_last_lap < timedelta(seconds=10)
        ):
            self._update_stint(
                driver_number=driver_number,
                stint_number=last_stint.stint_number,
                property="lap_end",
                value=last_stint.lap_end - 1,
            )

        lap_start = last_stint.lap_end + 1 if last_stint is not None else 1
        new_stint = Stint(
            meeting_key=self.meeting_key,
            session_key=self.session_key,
            driver_number=driver_number,
            stint_number=stint_number,
            lap_start=lap_start,
            lap_end=lap_start,
        )
        self.stints[driver_number][stint_number] = new_stint

    def process_message(self, message: Message) -> Iterator[Stint]:
        if message.topic == "TimingAppData":
            for driver_number, data in message.content["Lines"].items():
                try:
                    driver_number = int(driver_number)
                except:
                    continue

                if not isinstance(data, dict):
                    continue

                stints_data = data.get("Stints")
                if stints_data:
                    if isinstance(stints_data, list):
                        stints_number = [0] * len(stints_data)
                    elif isinstance(stints_data, dict):
                        stints_number = sorted(list(stints_data.keys()))
                        stints_data = [v for _, v in sorted(list(stints_data.items()))]
                    else:
                        continue

                    for stint_number, stint_data in zip(stints_number, stints_data):
                        try:
                            stint_number = int(stint_number) + 1
                        except:
                            continue

                        if stint_number not in self.stints[driver_number]:
                            self._add_stint(
                                driver_number=driver_number,
                                stint_number=stint_number,
                                timepoint=message.timepoint,
                            )

                        if not isinstance(stint_data, dict):
                            continue

                        if "Compound" in stint_data:
                            self._update_stint(
                                driver_number=driver_number,
                                stint_number=stint_number,
                                property="compound",
                                value=stint_data["Compound"],
                            )
                        if "TotalLaps" in stint_data:
                            stint = self.stints[driver_number][stint_number]
                            if stint.tyre_age_at_start is None:
                                self._update_stint(
                                    driver_number=driver_number,
                                    stint_number=stint_number,
                                    property="tyre_age_at_start",
                                    value=stint_data["TotalLaps"],
                                )

        elif message.topic == "TimingData":
            if "Lines" not in message.content:
                return

            for driver_number, data in message.content["Lines"].items():
                try:
                    driver_number = int(driver_number)
                except:
                    continue

                if not isinstance(data, dict):
                    continue

                if len(self.stints[driver_number]) == 0:
                    self._add_stint(
                        driver_number=driver_number,
                        stint_number=1,
                        timepoint=message.timepoint,
                    )

                if "NumberOfLaps" in data:
                    stint = self._get_last_stint(driver_number)
                    if stint is not None:
                        if data["NumberOfLaps"] is not None:
                            self._update_stint(
                                driver_number=driver_number,
                                stint_number=stint.stint_number,
                                property="lap_end",
                                value=data["NumberOfLaps"],
                            )
                        self._update_stint(
                            driver_number=driver_number,
                            stint_number=stint.stint_number,
                            property="_date_start_last_lap",
                            value=message.timepoint,
                        )

        yield from deepcopy(self.updated_stints)
        self.updated_stints = set()
