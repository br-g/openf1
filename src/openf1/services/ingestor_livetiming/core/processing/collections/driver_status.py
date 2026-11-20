from dataclasses import dataclass, field
from datetime import datetime
from typing import Iterator

from openf1.services.ingestor_livetiming.core.objects import (
    Collection,
    Document,
    Message,
)


@dataclass(eq=False)
class DriverStatus(Document):
    meeting_key: int
    session_key: int
    driver_number: int
    date: datetime
    retired: bool | None
    stopped: bool | None

    @property
    def unique_key(self) -> tuple:
        return (self.date, self.driver_number)


@dataclass
class DriverStatusCollection(Collection):
    name = "driver_status"
    source_topics = {"TimingData"}
    statuses: dict[int, dict[str, bool]] = field(default_factory=dict)

    def process_message(self, message: Message) -> Iterator[DriverStatus]:
        lines = message.content.get("Lines")
        if not isinstance(lines, dict):
            return

        for driver_number, data in lines.items():
            try:
                driver_number = int(driver_number)
            except (TypeError, ValueError):
                continue

            if not isinstance(data, dict):
                continue

            status = self.statuses.setdefault(driver_number, {})
            has_update = False
            for topic_field in ("Retired", "Stopped"):
                value = data.get(topic_field)
                if isinstance(value, bool):
                    status[topic_field] = value
                    has_update = True

            if not has_update:
                continue

            yield DriverStatus(
                meeting_key=self.meeting_key,
                session_key=self.session_key,
                driver_number=driver_number,
                date=message.timepoint,
                retired=status.get("Retired"),
                stopped=status.get("Stopped"),
            )
