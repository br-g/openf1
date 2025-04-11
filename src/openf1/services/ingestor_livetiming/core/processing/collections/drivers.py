from collections import defaultdict
from copy import deepcopy
from dataclasses import dataclass, field
from functools import cached_property
from typing import Iterator

from openf1.services.ingestor_livetiming.core.objects import (
    Collection,
    Document,
    Message,
)

# Renaming of keys, from topic to collection
KEY_MAPPING = {
    "BroadcastName": "broadcast_name",
    "CountryCode": "country_code",
    "FirstName": "first_name",
    "FullName": "full_name",
    "HeadshotUrl": "headshot_url",
    "LastName": "last_name",
    "TeamColour": "team_colour",
    "TeamName": "team_name",
    "Tla": "name_acronym",
}


@dataclass(eq=False)
class Driver(Document):
    meeting_key: int
    session_key: int
    driver_number: int | None = None
    broadcast_name: str | None = None
    full_name: str | None = None
    name_acronym: str | None = None
    team_name: str | None = None
    team_colour: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    headshot_url: str | None = None
    country_code: str | None = None

    @property
    def unique_key(self) -> tuple:
        return (self.session_key, self.driver_number)


@dataclass
class DriversCollection(Collection):
    name = "drivers"
    source_topics = {"DriverList"}

    updated_drivers: set = field(
        default_factory=set
    )  # drivers updated since last message

    @cached_property
    def drivers(self) -> defaultdict:
        return defaultdict(
            lambda: Driver(meeting_key=self.meeting_key, session_key=self.session_key)
        )

    def _update_driver(self, driver_number: int, property: str, value: any):
        driver = self.drivers[driver_number]
        old_value = getattr(driver, property)
        if value != old_value:
            setattr(driver, property, value)
            self.updated_drivers.add(driver)

    def process_message(self, message: Message) -> Iterator[Driver]:
        for driver_number, driver_content in message.content.items():
            try:
                driver_number = int(driver_number)
            except:
                continue

            if not isinstance(driver_content, dict):
                continue

            self._update_driver(
                driver_number=driver_number,
                property="driver_number",
                value=driver_number,
            )

            for topic_key, collection_key in KEY_MAPPING.items():
                if topic_key not in driver_content:
                    continue
                self._update_driver(
                    driver_number=driver_number,
                    property=collection_key,
                    value=driver_content[topic_key],
                )

        yield from deepcopy(self.updated_drivers)
        self.updated_drivers = set()
