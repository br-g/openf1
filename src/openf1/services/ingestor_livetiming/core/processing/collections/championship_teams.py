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
    team_colour: str | None = None
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
    source_topics = {"ChampionshipPrediction", "DriverList"}
    cache: dict = field(default_factory=dict)
    team_colour_by_name: dict = field(default_factory=dict)

    def process_message(self, message: Message) -> Iterator[ChampionshipTeam]:
        if message.topic == "DriverList":
            for driver_data in message.content.values():
                if not isinstance(driver_data, dict):
                    continue
                team_name = driver_data.get("TeamName")
                team_colour = driver_data.get("TeamColour")
                if team_name and team_colour:
                    self.team_colour_by_name[team_name] = team_colour
            # Back-fill teams already cached before DriverList arrived
            for result in self.cache.values():
                if result.team_colour is None and result.team_name in self.team_colour_by_name:
                    result.team_colour = self.team_colour_by_name[result.team_name]
                    yield result
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

            if team_name and team_name in self.team_colour_by_name:
                result.team_colour = self.team_colour_by_name[team_name]

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
