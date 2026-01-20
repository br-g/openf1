from copy import deepcopy
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
class SessionState(Document):
    meeting_key: int
    session_key: int
    status: str
    qualifying_phase: int | None = None
    race_lap: int | None = None
    date_start: datetime | None = None
    date_end: datetime | None = None

    @property
    def unique_key(self) -> tuple:
        return (
            self.session_key,
            self.qualifying_phase if self.qualifying_phase is not None else 1,
        )


@dataclass
class SessionStateCollection(Collection):
    name = "session_state"
    source_topics = {"SessionData"}

    current_state: SessionState | None = None
    has_been_updated: bool = False

    def _initialize_state(self):
        self.current_state = SessionState(
            meeting_key=self.meeting_key,
            session_key=self.session_key,
            status="Scheduled",
        )
        self.has_been_updated = True

    def _update_state(self, property: str, value: any):
        old_value = getattr(self.current_state, property)
        if value != old_value:
            setattr(self.current_state, property, value)
            self.has_been_updated = True

    def process_message(self, message: Message) -> Iterator[SessionState]:
        self.has_been_updated = False

        if self.current_state is None:
            self._initialize_state()

        status_series = message.content.get("StatusSeries")
        if status_series:
            if isinstance(status_series, dict):
                status_series = list(status_series.values())

            for item in status_series:
                status = item.get("SessionStatus")
                if status is not None:
                    date = to_datetime(item.get("Utc"))
                    if date is not None:
                        date = pytz.utc.localize(date)
                        date = date.replace(microsecond=0)

                    if status == "Started":
                        self._update_state(property="date_end", value=None)
                        if self.current_state.date_start is None:
                            self._update_state(property="date_start", value=date)
                    elif status in {"Finished", "Aborted"}:
                        self._update_state(property="date_end", value=date)

                    if status == "Started":
                        status = "Active"
                    if status in {"Finalised", "Ends"}:
                        status = "Finished"
                    self._update_state(property="status", value=status)

        series = message.content.get("Series")
        if series:
            if isinstance(series, dict):
                series = list(series.values())

            for item in series:
                qualifying_phase = item.get("QualifyingPart")
                if qualifying_phase is not None:
                    self._initialize_state()
                    self._update_state(
                        property="qualifying_phase", value=qualifying_phase
                    )

                race_lap = item.get("Lap")
                if race_lap is not None:
                    self._update_state(property="race_lap", value=race_lap)

        if self.has_been_updated:
            yield deepcopy(self.current_state)
