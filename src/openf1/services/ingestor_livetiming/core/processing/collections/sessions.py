from dataclasses import dataclass
from datetime import datetime
from typing import Iterator

from loguru import logger

from openf1.services.ingestor_livetiming.core.objects import (
    Collection,
    Document,
    Message,
)
from openf1.util.misc import add_timezone_info, to_datetime


@dataclass(eq=False)
class Session(Document):
    meeting_key: int
    session_key: int
    location: str | None
    date_start: datetime | None
    date_end: datetime | None
    session_type: str | None
    session_name: str | None
    country_key: int | None
    country_code: str | None
    country_name: str | None
    circuit_key: int | None
    circuit_short_name: str | None
    gmt_offset: str | None
    year: int | None

    @property
    def unique_key(self) -> tuple:
        return (self.session_key,)


class SessionsCollection(Collection):
    name = "sessions"
    source_topics = {"SessionInfo"}

    def process_message(self, message: Message) -> Iterator[Session]:
        data = message.content

        gmt_offset = data.get("GmtOffset")

        try:
            date_start = to_datetime(data["StartDate"])
            date_start = add_timezone_info(dt=date_start, gmt_offset=gmt_offset)
        except Exception as e:
            logger.warning(e)
            date_start = None

        try:
            date_end = to_datetime(data["EndDate"])
            date_end = add_timezone_info(dt=date_end, gmt_offset=gmt_offset)
        except Exception as e:
            logger.warning(e)
            date_end = None

        year = date_start.year if date_start else None

        yield Session(
            meeting_key=self.meeting_key,
            session_key=self.session_key,
            location=data.get("Meeting", {}).get("Location"),
            date_start=date_start,
            date_end=date_end,
            session_type=data.get("Type"),
            session_name=data.get("Name"),
            country_key=data.get("Meeting", {}).get("Country", {}).get("Key"),
            country_code=data.get("Meeting", {}).get("Country", {}).get("Code"),
            country_name=data.get("Meeting", {}).get("Country", {}).get("Name"),
            circuit_key=data.get("Meeting", {}).get("Circuit", {}).get("Key"),
            circuit_short_name=data.get("Meeting", {})
            .get("Circuit", {})
            .get("ShortName"),
            gmt_offset=gmt_offset,
            year=year,
        )
