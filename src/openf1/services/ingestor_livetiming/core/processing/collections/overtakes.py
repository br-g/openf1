from dataclasses import dataclass
from datetime import datetime
from typing import Iterator

from openf1.services.ingestor_livetiming.core.objects import (
    Collection,
    Document,
    Message,
)


@dataclass(eq=False)
class Overtake(Document):
    meeting_key: int
    session_key: int
    overtaking_driver_number: int
    overtaken_driver_number: int
    date: datetime
    position: int

    @property
    def unique_key(self) -> tuple:
        return (self.date, self.overtaking_driver_number, self.overtaken_driver_number)
    

@dataclass
class OvertakesCollection(Collection):
    name = "overtakes"
    source_topics = {"DriverRaceInfo"}

    def process_message(self, message: Message) -> Iterator[Overtake]:
        # Overtaking driver has OvertakeState equal to 2, overtaken drivers may or may not have OvertakeState
        try:
            overtaking_driver_number = next(
                (int(driver_number) for driver_number, data in message.content.items()
                    if isinstance(data, dict) and data.get("OvertakeState") == 2
                ),
                None
            )
        except:
            overtaking_driver_number = None

        if overtaking_driver_number is None:
            # Not an overtake message
            return

        try:
            overtaken_driver_data = [
                (int(driver_number), int(data.get("Position"))) for driver_number, data in message.content.items()
                    if isinstance(data, dict) and data.get("OvertakeState") != 2 and data.get("Position") is not None
            ]
        except:
            overtaken_driver_data = []

        if len(overtaken_driver_data) == 0:
            # Need at least two drivers to have an overtake
            return
        
        for overtaken_driver_number, position in overtaken_driver_data:
            # position is the overtaken driver's position after being overtaken, adjust position to account for this
            overtake_position = position - 1 

            yield Overtake(
                meeting_key=self.meeting_key,
                session_key=self.session_key,
                overtaking_driver_number=overtaking_driver_number,
                overtaken_driver_number=overtaken_driver_number,
                date=message.timepoint,
                position=overtake_position
            )