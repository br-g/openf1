from dataclasses import dataclass
from datetime import datetime
from typing import Iterator

from openf1.services.ingestor_livetiming.core.objects import (
    Collection,
    Document,
    Message,
)
from openf1.util.misc import add_timezone_info, to_datetime


@dataclass(eq=False)
class Meeting(Document):
    meeting_key: int
    circuit_key: int | None
    circuit_short_name: str | None
    meeting_code: str | None
    location: str | None
    country_key: int | None
    country_code: str | None
    country_name: str | None
    meeting_name: str | None
    meeting_official_name: str | None
    gmt_offset: str | None
    date_start: datetime | None
    year: int | None

    @property
    def unique_key(self) -> tuple:
        return (self.meeting_key,)


@dataclass
class MeetingsCollection(Collection):
    name = "meetings"
    source_topics = {"SessionInfo"}

    def process_message(self, message: Message) -> Iterator[Meeting]:
        data = message.content

        gmt_offset = data.get("GmtOffset")

        try:
            date_start = data["StartDate"]
            date_start = to_datetime(date_start)
            date_start = add_timezone_info(dt=date_start, gmt_offset=gmt_offset)
        except:
            date_start = None

        year = date_start.year if date_start else None

        yield Meeting(
            meeting_key=self.meeting_key,
            circuit_key=data.get("Meeting", {}).get("Circuit", {}).get("Key"),
            circuit_short_name=data.get("Meeting", {})
            .get("Circuit", {})
            .get("ShortName"),
            meeting_code=data.get("Meeting", {}).get("Country", {}).get("Code"),
            location=data.get("Meeting", {}).get("Location"),
            country_key=data.get("Meeting", {}).get("Country", {}).get("Key"),
            country_code=data.get("Meeting", {}).get("Country", {}).get("Code"),
            country_name=data.get("Meeting", {}).get("Country", {}).get("Name"),
            meeting_name=data.get("Meeting", {}).get("Name"),
            meeting_official_name=data.get("Meeting", {}).get("OfficialName"),
            gmt_offset=gmt_offset,
            date_start=date_start,
            year=year,
        )
