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

BASE_URL = "https://livetiming.formula1.com/static/"


@dataclass(eq=False)
class TeamRadio(Document):
    meeting_key: int
    session_key: int
    driver_number: int
    date: datetime | None
    recording_url: str

    @property
    def unique_key(self) -> tuple:
        return (self.date, self.driver_number)


@dataclass
class TeamRadioCollection(Collection):
    name = "team_radio"
    source_topics = {"SessionInfo", "TeamRadio"}

    session_path: str = field(default=None)

    def process_message(self, message: Message) -> Iterator[TeamRadio]:
        if message.topic == "SessionInfo":
            self.session_path = message.content["Path"]

        elif message.topic == "TeamRadio":
            if self.session_path is None:
                return

            captures = message.content["Captures"]
            if isinstance(captures, dict):
                captures = captures.values()

            for capture in captures:
                try:
                    driver_number = int(capture["RacingNumber"])
                except:
                    continue

                try:
                    date = to_datetime(capture["Utc"])
                    date = pytz.utc.localize(date)
                except:
                    date = None

                try:
                    path = capture["Path"]
                    assert isinstance(path, str)
                except:
                    continue

                yield TeamRadio(
                    meeting_key=self.meeting_key,
                    session_key=self.session_key,
                    driver_number=driver_number,
                    date=date,
                    recording_url=BASE_URL + self.session_path + path,
                )
