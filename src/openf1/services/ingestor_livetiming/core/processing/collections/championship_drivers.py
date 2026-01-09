from dataclasses import dataclass, field
from typing import Iterator

from openf1.services.ingestor_livetiming.core.objects import (
    Collection,
    Document,
    Message,
)


@dataclass(eq=False)
class ChampionshipDriver(Document):
    meeting_key: int
    session_key: int
    driver_number: int
    position_start: int | None = None
    position_current: int | None = None
    points_start: float | None = None
    points_current: float | None = None

    @property
    def unique_key(self) -> tuple:
        return (self.session_key, self.driver_number)


@dataclass
class ChampionshipDriverCollection(Collection):
    name = "championship_drivers"
    source_topics = {"ChampionshipPrediction"}
    cache: dict = field(default_factory=dict)

    def process_message(self, message: Message) -> Iterator[ChampionshipDriver]:
        if "Drivers" not in message.content:
            return

        for driver_number, data in message.content["Drivers"].items():
            try:
                driver_number = int(driver_number)
            except:
                continue

            if not isinstance(data, dict):
                continue

            key = (self.session_key, driver_number)
            if key in self.cache:
                result = self.cache[key]
            else:
                result = ChampionshipDriver(
                    meeting_key=self.meeting_key,
                    session_key=self.session_key,
                    driver_number=driver_number,
                )

            if "CurrentPosition" in data and data["CurrentPosition"] > 0:
                result.position_start = data["CurrentPosition"]

            if "PredictedPosition" in data and data["PredictedPosition"] > 0:
                result.position_current = data["PredictedPosition"]

            if "CurrentPoints" in data:
                result.points_start = data["CurrentPoints"]

            if "PredictedPoints" in data:
                result.points_current = data["PredictedPoints"]

            yield result
            self.cache[key] = result
