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
    team_name: str
    _team_key: str
    position_start: int | None = None
    position_current: int | None = None
    points_start: float | None = None
    points_current: float | None = None

    @property
    def unique_key(self) -> tuple:
        return (self.session_key, self._team_key)


@dataclass
class ChampionshipTeamCollection(Collection):
    name = "championship_teams"
    source_topics = {
        "ChampionshipPrediction",
        "SessionInfo",
    }
    cache: dict = field(default_factory=dict)
    is_session_a_race: bool | None = None

    def process_message(self, message: Message) -> Iterator[ChampionshipTeam]:
        if message.topic == "SessionInfo":
            self.is_session_a_race = message.content["Type"].lower() == "race"
            return

        # Sometimes, wrong championship data is sent during practice or qualifying
        # sessions (example: qualifying at Mexico 2026), which needs to be discarded.
        if self.is_session_a_race is False:
            return

        if "Teams" not in message.content:
            return

        for team_key, data in message.content["Teams"].items():
            if not isinstance(data, dict):
                continue

            team_name = data.get("TeamName")

            key = (self.session_key, team_key)
            if key in self.cache:
                result = self.cache[key]
                if team_name:
                    result.team_name = team_name
            else:
                result = ChampionshipTeam(
                    meeting_key=self.meeting_key,
                    session_key=self.session_key,
                    team_name=team_name,
                    _team_key=team_key,
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
