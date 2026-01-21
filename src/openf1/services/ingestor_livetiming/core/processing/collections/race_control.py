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
class RaceControl(Document):
    meeting_key: int
    session_key: int
    date: datetime | None
    driver_number: int | None
    lap_number: int | None
    category: str | None
    flag: str | None
    scope: str | None
    sector: int | None
    qualifying_phase: int | None
    message: str | None

    @property
    def unique_key(self) -> tuple:
        return (
            self.date,
            self.driver_number,
            self.lap_number,
            self.category,
            self.flag,
            self.scope,
            self.sector,
        )


@dataclass
class RaceControlCollection(Collection):
    name = "race_control"
    source_topics = {"RaceControlMessages", "SessionData"}

    race_lap: int | None = None
    qualifying_phase: int | None = None

    def process_message(self, message: Message) -> Iterator[RaceControl]:
        if message.topic == "RaceControlMessages":
            inner_messages = message.content["Messages"]
            if isinstance(inner_messages, dict):
                inner_messages = inner_messages.values()

            for data in inner_messages:
                if not isinstance(data, dict):
                    continue

                try:
                    date = to_datetime(data["Utc"])
                    date = pytz.utc.localize(date)
                except:
                    date = None

                try:
                    driver_number = int(data.get("RacingNumber"))
                except:
                    driver_number = None

                yield RaceControl(
                    meeting_key=self.meeting_key,
                    session_key=self.session_key,
                    date=date,
                    driver_number=driver_number,
                    lap_number=data.get("Lap"),
                    category=data.get("Category"),
                    flag=data.get("Flag"),
                    scope=data.get("Scope"),
                    sector=data.get("Sector"),
                    qualifying_phase=(
                        self.qualifying_phase
                        if data.get("Category") in {"Flag", "CarEvent", "SafetyCar"}
                        else None
                    ),
                    message=data.get("Message"),
                )

        elif message.topic == "SessionData":
            status_series = message.content.get("StatusSeries")
            if status_series:
                if isinstance(status_series, dict):
                    status_series = list(status_series.values())

                for item in status_series:
                    status = item.get("SessionStatus")
                    if status is not None and status not in {
                        "Inactive",
                        "Finalised",
                        "Ends",
                    }:
                        date = to_datetime(item.get("Utc"))
                        if date is not None:
                            date = pytz.utc.localize(date)

                        yield RaceControl(
                            meeting_key=self.meeting_key,
                            session_key=self.session_key,
                            date=date,
                            driver_number=None,
                            lap_number=self.race_lap,
                            category="SessionStatus",
                            flag=None,
                            scope=None,
                            sector=None,
                            qualifying_phase=self.qualifying_phase,
                            message=f"SESSION {status.upper()}",
                        )

            series = message.content.get("Series")
            if series:
                if isinstance(series, dict):
                    series = list(series.values())

                for item in series:
                    qualifying_phase = item.get("QualifyingPart")
                    if qualifying_phase is not None:
                        self.qualifying_phase = qualifying_phase

                    race_lap = item.get("Lap")
                    if race_lap is not None:
                        self.race_lap = race_lap
