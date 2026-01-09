from dataclasses import dataclass, field
from typing import Iterator

from openf1.services.ingestor_livetiming.core.objects import (
    Collection,
    Document,
    Message,
)


@dataclass(eq=False)
class ChampionshipTeam(Document):
    meeting_key: int
    session_key: int
    team_name: int
    position_start: int | None = None
    position_current: int | None = None
    points_start: float | None = None
    points_current: float | None = None

    @property
    def unique_key(self) -> tuple:
        return (self.session_key, self.team_name)


@dataclass
class ChampionshipTeamCollection(Collection):
    name = "championship_teams"
    source_topics = {"ChampionshipPrediction"}
    cache: dict = field(default_factory=dict)

    def process_message(self, message: Message) -> Iterator[ChampionshipTeam]:
        for _, data in message.content["Teams"].items():
            if not isinstance(data, dict):
                continue

            key = (self.session_key, data["TeamName"])
            if key in self.cache:
                result = self.cache[key]
            else:
                result = ChampionshipTeam(
                    meeting_key=self.meeting_key,
                    session_key=self.session_key,
                    team_name=data["TeamName"],
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
