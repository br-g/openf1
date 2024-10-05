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
class CarData(Document):
    meeting_key: int
    session_key: int
    driver_number: int
    date: datetime
    rpm: int | None
    speed: int | None
    n_gear: int | None
    throttle: int | None
    brake: int | None
    drs: int | None

    @property
    def unique_key(self) -> tuple:
        return (self.date, self.driver_number)


class CarDataCollection(Collection):
    name = "car_data"
    source_topics = {"CarData.z"}

    def process_message(self, message: Message) -> Iterator[CarData]:
        for entry in message.content["Entries"]:
            date = to_datetime(entry["Utc"])
            date = pytz.utc.localize(date)

            for driver_number, data in entry["Cars"].items():
                channels = data["Channels"]
                yield CarData(
                    meeting_key=self.meeting_key,
                    session_key=self.session_key,
                    driver_number=int(driver_number),
                    date=date,
                    rpm=channels.get("0"),
                    speed=channels.get("2"),
                    n_gear=channels.get("3"),
                    throttle=channels.get("4"),
                    brake=channels.get("5"),
                    drs=channels.get("45"),
                )
