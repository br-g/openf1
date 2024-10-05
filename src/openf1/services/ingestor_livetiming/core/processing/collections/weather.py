from dataclasses import dataclass
from datetime import datetime
from typing import Iterator

from openf1.services.ingestor_livetiming.core.objects import (
    Collection,
    Document,
    Message,
)


@dataclass(eq=False)
class Weather(Document):
    meeting_key: int
    session_key: int
    date: datetime
    air_temperature: float
    humidity: float
    pressure: float
    rainfall: int
    track_temperature: float
    wind_direction: int
    wind_speed: float

    @property
    def unique_key(self) -> tuple:
        return (self.date,)


class WeatherCollection(Collection):
    name = "weather"
    source_topics = {"WeatherData"}

    def process_message(self, message: Message) -> Iterator[Weather]:
        yield Weather(
            meeting_key=self.meeting_key,
            session_key=self.session_key,
            date=message.timepoint,
            air_temperature=float(message.content["AirTemp"]),
            humidity=float(message.content["Humidity"]),
            pressure=float(message.content["Pressure"]),
            rainfall=int(message.content["Rainfall"]),
            track_temperature=float(message.content["TrackTemp"]),
            wind_direction=int(message.content["WindDirection"]),
            wind_speed=float(message.content["WindSpeed"]),
        )
