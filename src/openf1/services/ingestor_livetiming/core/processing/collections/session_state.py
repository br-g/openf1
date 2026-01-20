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
    _state_number: int
    qualifying_phase: int | None = None
    race_lap: int | None = None
    date_start: datetime | None = None
    date_end: datetime | None = None

    @property
    def unique_key(self) -> tuple:
        return (
            self.session_key,
            self._state_number,
        )


@dataclass
class SessionStateCollection(Collection):
    name = "session_state"
    source_topics = {"SessionData"}

    current_state: SessionState | None = None
    has_been_updated: bool = False

    def _reset_state(self):
        if self.current_state and self.current_state.status == "Scheduled":
            return

        self.current_state = SessionState(
            meeting_key=self.meeting_key,
            session_key=self.session_key,
            status="Scheduled",
            _state_number=(
                0
                if self.current_state is None
                else self.current_state._state_number + 1
            ),
            qualifying_phase=(
                None
                if self.current_state is None
                or self.current_state.qualifying_phase is None
                else self.current_state.qualifying_phase
            ),
            race_lap=(
                None
                if self.current_state is None or self.current_state.race_lap is None
                else self.current_state.race_lap + 1
            ),
        )

    def _update_state(self, property: str, value: any):
        old_value = getattr(self.current_state, property)
        if value != old_value:
            setattr(self.current_state, property, value)

            if self.current_state.status != "Scheduled":
                self.has_been_updated = True

    def process_message(self, message: Message) -> Iterator[SessionState]:
        self.has_been_updated = False

        if self.current_state is None:
            self._reset_state()

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

                    if status == "Inactive":
                        continue
                    elif status == "Started" and (
                        self.current_state.date_start is None
                        or date > self.current_state.date_start
                    ):
                        self._reset_state()
                        self._update_state(property="date_start", value=date)
                    elif status in {"Finished", "Aborted"} and (
                        self.current_state.date_end is None
                        or date > self.current_state.date_end
                    ):
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
                    self._reset_state()
                    self._update_state(
                        property="qualifying_phase", value=qualifying_phase
                    )

                race_lap = item.get("Lap")
                if race_lap is not None and self.current_state != "Aborted":
                    self._update_state(property="race_lap", value=race_lap)

        if self.has_been_updated:
            yield deepcopy(self.current_state)
