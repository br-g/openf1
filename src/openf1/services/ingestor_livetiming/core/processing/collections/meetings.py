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
    circuit_key: int
    circuit_short_name: str
    meeting_code: str
    location: str
    country_key: int
    country_code: str
    country_name: str
    meeting_name: str
    meeting_official_name: str
    gmt_offset: str
    date_start: datetime
    year: int

    @property
    def unique_key(self) -> tuple:
        # Meetings are a bit tricky...
        # Duplicates are removed at query time
        return (self.date_start,)


class MeetingsCollection(Collection):
    name = "meetings"
    source_topics = {"SessionInfo"}

    def process_message(self, message: Message) -> Iterator[Meeting]:
        data = message.content

        gmt_offset = data["GmtOffset"]

        date_start = to_datetime(data["StartDate"])
        date_start = add_timezone_info(dt=date_start, gmt_offset=gmt_offset)

        yield Meeting(
            meeting_key=self.meeting_key,
            circuit_key=data["Meeting"]["Circuit"]["Key"],
            circuit_short_name=data["Meeting"]["Circuit"]["ShortName"],
            meeting_code=data["Meeting"]["Country"]["Code"],
            location=data["Meeting"]["Location"],
            country_key=data["Meeting"]["Country"]["Key"],
            country_code=data["Meeting"]["Country"]["Code"],
            country_name=data["Meeting"]["Country"]["Name"],
            meeting_name=data["Meeting"]["Name"],
            meeting_official_name=data["Meeting"]["OfficialName"],
            gmt_offset=data["GmtOffset"],
            date_start=date_start,
            year=date_start.year,
        )
