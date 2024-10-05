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
class Session(Document):
    meeting_key: int
    session_key: int
    location: str
    date_start: datetime
    date_end: datetime
    session_type: str
    session_name: str
    country_key: int
    country_code: str
    country_name: str
    circuit_key: int
    circuit_short_name: str
    gmt_offset: str
    year: int

    @property
    def unique_key(self) -> tuple:
        return (self.session_key,)


class SessionsCollection(Collection):
    name = "sessions"
    source_topics = {"SessionInfo"}

    def process_message(self, message: Message) -> Iterator[Session]:
        data = message.content

        gmt_offset = data["GmtOffset"]

        date_start = to_datetime(data["StartDate"])
        date_start = add_timezone_info(dt=date_start, gmt_offset=gmt_offset)

        date_end = to_datetime(data["EndDate"])
        date_end = add_timezone_info(dt=date_end, gmt_offset=gmt_offset)

        yield Session(
            meeting_key=self.meeting_key,
            session_key=self.session_key,
            location=data["Meeting"]["Location"],
            date_start=date_start,
            date_end=date_end,
            session_type=data["Type"],
            session_name=data["Name"],
            country_key=data["Meeting"]["Country"]["Key"],
            country_code=data["Meeting"]["Country"]["Code"],
            country_name=data["Meeting"]["Country"]["Name"],
            circuit_key=data["Meeting"]["Circuit"]["Key"],
            circuit_short_name=data["Meeting"]["Circuit"]["ShortName"],
            gmt_offset=gmt_offset,
            year=date_start.year,
        )
