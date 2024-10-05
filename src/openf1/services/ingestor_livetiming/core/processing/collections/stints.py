from collections import defaultdict
from dataclasses import dataclass
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
    lap_start: int | None = None
    lap_end: int | None = None
    compound: str | None = None
    tyre_age_at_start: int | None = None

    @property
    def unique_key(self) -> tuple:
        return (self.session_key, self.stint_number, self.driver_number)


class StintsCollection(Collection):
    name = "stints"
    source_topics = {"TimingAppData", "TimingData"}

    stints = defaultdict(dict)
    updated_stints = set()  # stints that have been updated since the last message

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

    def _add_stint(self, driver_number: int, stint_number: int):
        last_stint = self._get_last_stint(driver_number)

        new_stint = Stint(
            meeting_key=self.meeting_key,
            session_key=self.session_key,
            driver_number=driver_number,
            stint_number=stint_number,
        )

        if last_stint is not None and last_stint.lap_end is not None:
            new_stint.lap_start = last_stint.lap_end + 1
            new_stint.lap_end = new_stint.lap_start

        self.stints[driver_number][stint_number] = new_stint

    def process_message(self, message: Message) -> Iterator[Stint]:
        if message.topic == "TimingAppData":
            for driver_number, data in message.content["Lines"].items():
                driver_number = int(driver_number)

                if "Stints" in data:
                    if isinstance(data["Stints"], list):
                        stints_data = data["Stints"]
                        stints_number = [0] * len(stints_data)
                    else:
                        stints_data = [
                            v for _, v in sorted(list(data["Stints"].items()))
                        ]
                        stints_number = sorted(list(data["Stints"].keys()))

                    for stint_number, stint_data in zip(stints_number, stints_data):
                        stint_number = int(stint_number) + 1

                        if stint_number not in self.stints[driver_number]:
                            self._add_stint(
                                driver_number=driver_number,
                                stint_number=stint_number,
                            )

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
            if "Lines" in message.content:
                for driver_number, data in message.content["Lines"].items():
                    driver_number = int(driver_number)

                    if len(self.stints[driver_number]) == 0:
                        self._add_stint(
                            driver_number=driver_number,
                            stint_number=1,
                        )

                    if "NumberOfLaps" in data:
                        stint = self._get_last_stint(driver_number)
                        if stint is not None:
                            if stint.lap_start is None:
                                self._update_stint(
                                    driver_number=driver_number,
                                    stint_number=stint.stint_number,
                                    property="lap_start",
                                    value=data["NumberOfLaps"],
                                )
                            self._update_stint(
                                driver_number=driver_number,
                                stint_number=stint.stint_number,
                                property="lap_end",
                                value=data["NumberOfLaps"],
                            )

        yield from self.updated_stints
        self.updated_stints = set()
