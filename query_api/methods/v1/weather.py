from typing import List, Dict, Iterator
from dateutil.tz import tzutc
from base_method import staticproperty, BaseMethod
from db import query_mongo
from util import do_try


class Method(BaseMethod):
    @staticproperty
    def description(cls) -> str:
        return 'The weather over the track, updated every minute.'

    @staticproperty
    def example_filters(cls) -> List[str]:
        return [
            'meeting_key=1208',
            'wind_direction>=130',
            'track_temperature>=52',
        ]

    @staticproperty
    def example_response(cls) -> List[Dict]:
        return [
            {
                'air_temperature': 27.8,
                'humidity': 58,
                'pressure': 1018.7,
                'rainfall': 0,
                'track_temperature': 52.5,
                'wind_direction': 136,
                'wind_speed': 2.4,
                'date': '2023-05-07T18:42:25.233000+00:00',
                'session_key': 9078,
                'meeting_key': 1208
            }
        ]

    @staticmethod
    def _query(filters: Dict[str, List[Dict]]) -> Iterator[Dict]:
        MAPPING = {
            'meeting_key': '_meeting_key',
            'session_key': '_session_key',
            'date': '_time',
            'air_temperature': 'AirTemp',
            'humidity': 'Humidity',
            'pressure': 'Pressure',
            'rainfall': 'Rainfall',
            'track_temperature': 'TrackTemp',
            'wind_direction': 'WindDirection',
            'wind_speed': 'WindSpeed',
        }
        docs = list(query_mongo(
            collection='WeatherData',
            mapping=MAPPING,
            filters_user={k: v for k, v in filters.items()},
            sort_by=[('date', 1)],
        ))
        for doc in docs:
            doc['date'] = do_try(lambda: doc['date'].replace(tzinfo=tzutc()))

        return docs
