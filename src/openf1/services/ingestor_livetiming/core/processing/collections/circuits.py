from dataclasses import dataclass
from datetime import timedelta
from typing import Iterator
from openf1.util.db import query_db

from openf1.services.ingestor_livetiming.core.objects import (
    Collection,
    Document,
    Message,
)
from openf1.util.misc import add_timezone_info, to_datetime


@dataclass(eq=False)
class Circuits(Document):
    circuit_key: int
    circuit_short_name: str
    country_code: str
    country_name: str
    country_key: int
    location: str
    track_coordinates: list[dict[str, float]]  # Example: [ {"x": 0.0, "y": 0.0, "z": 0.0}, ... ]
    sector_2_start: dict[str, float]  # Example: {"x": 0.0, "y": 0.0, "z": 0.0}
    sector_3_start: dict[str, float]  # Example: {"x": 0.0, "y": 0.0, "z": 0.0}

    @property
    def unique_key(self) -> tuple:
        return (self.circuit_key,)


class CircuitsCollection(Collection):
    name = "circuits"
    source_topics = {"SessionInfo"}

    def process_message(self, message: Message) -> Iterator[Circuits]:
        data = message.content
        print(data["Type"])
        if data["Type"] != "Qualifying":
            print("Not a qualifying session")
            return
        else:
            print("Qualifying session")

        # Query for laps in the session
        results = query_db(collection_name="laps", filters={"session_key": data["Key"]})
        valid_laps = [lap for lap in results if lap["lap_duration"] is not None]

        # Find the fastest lap
        fastest_lap = min(valid_laps, key=lambda x: x["lap_duration"])

        # Calculate the lap start and end time
        lap_start_time = fastest_lap["date_start"]
        lap_duration_seconds = fastest_lap["lap_duration"]
        lap_end_time = lap_start_time + timedelta(seconds=lap_duration_seconds)

        print(f"Lap Start Time: {lap_start_time}")
        print(f"Lap End Time: {lap_end_time}")

        # Calculate sector split times
        sector_1_end_time = lap_start_time + timedelta(seconds=fastest_lap["duration_sector_1"])
        sector_2_end_time = sector_1_end_time + timedelta(seconds=fastest_lap["duration_sector_2"])

        # Query for location data within the lap duration
        lap_data = query_db(
            collection_name="location", 
            filters={
                "date": {"$gte": lap_start_time, "$lte": lap_end_time},
                "driver_number": fastest_lap["driver_number"],
            }
        )

        # Extract track coordinates
        track_coordinates = [
            {"x": item["x"], "y": item["y"], "z": item["z"], "date": item["date"]}
            for item in lap_data
        ]

        # Filter track coordinates for sector start points
        sector_2_start = next((point for point in track_coordinates if point["date"] >= sector_1_end_time), {"x": 0.0, "y": 0.0, "z": 0.0})
        sector_3_start = next((point for point in track_coordinates if point["date"] >= sector_2_end_time), {"x": 0.0, "y": 0.0, "z": 0.0})

        print(f"Sector 2 Start: {sector_2_start}")
        print(f"Sector 3 Start: {sector_3_start}")

    

        yield Circuits(
            location=data["Meeting"]["Location"],
            country_key=data["Meeting"]["Country"]["Key"],
            country_code=data["Meeting"]["Country"]["Code"],
            country_name=data["Meeting"]["Country"]["Name"],
            circuit_key=data["Meeting"]["Circuit"]["Key"],
            circuit_short_name=data["Meeting"]["Circuit"]["ShortName"],
            track_coordinates=track_coordinates,
            sector_2_start={"x": sector_2_start["x"], "y": sector_2_start["y"], "z": sector_2_start["z"]},
            sector_3_start={"x": sector_3_start["x"], "y": sector_3_start["y"], "z": sector_3_start["z"]},
        )
