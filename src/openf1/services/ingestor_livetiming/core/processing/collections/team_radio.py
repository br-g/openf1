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
    pending_messages: list[Message] = field(default_factory=list)

    def process_message(self, message: Message) -> Iterator[TeamRadio]:
        if message.topic == "SessionInfo":
            self.session_path = message.content["Path"]
            for pending in self.pending_messages:
                yield from self._process_team_radio(pending)
            self.pending_messages.clear()

        elif message.topic == "TeamRadio":
            if self.session_path is None:
                self.pending_messages.append(message)
                return

            yield from self._process_team_radio(message)

    def _process_team_radio(self, message: Message) -> Iterator[TeamRadio]:
        captures = message.content["Captures"]
        if isinstance(captures, dict):
            captures = captures.values()

        for capture in captures:
            try:
                driver_number = int(capture["RacingNumber"])
            except Exception:
                continue

            try:
                date = to_datetime(capture["Utc"])
                date = pytz.utc.localize(date)
            except Exception:
                date = None

            try:
                path = capture["Path"]
                assert isinstance(path, str)
            except Exception:
                continue

            yield TeamRadio(
                meeting_key=self.meeting_key,
                session_key=self.session_key,
                driver_number=driver_number,
                date=date,
                recording_url=BASE_URL + self.session_path + path,
            )
