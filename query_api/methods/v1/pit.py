from typing import List, Dict, Iterator, Union, Optional
from dateutil.tz import tzutc
from base_method import staticproperty, BaseMethod
from db import query_mongo
from util import do_try


class Method(BaseMethod):
    @staticproperty
    def description(cls) -> str:
        return '''
            Provides information about cars going through the pit lane.
        '''

    @staticproperty
    def example_filters(cls) -> List[str]:
        return [
            'session_key=9158',
            'pit_duration<31',
        ]

    @staticproperty
    def example_response(cls) -> List[Dict]:
        return [
            {
                'pit_duration': 24.5,
                'lap_number': 5,
                'driver_number': 63,
                'date': '2023-09-15T09:38:23.038000+00:00',
                'session_key': 9158,
                'meeting_key': 1219
            },
            {
                'pit_duration': 30.8,
                'lap_number': 13,
                'driver_number': 81,
                'date': '2023-09-15T10:05:01.229000+00:00',
                'session_key': 9158,
                'meeting_key': 1219
            }
        ]

    @staticmethod
    def _query(filters: Dict[str, List[Dict]]) -> Iterator[Dict]:
        MAPPING = {
            'session_key': '_session_key',
            'meeting_key': '_meeting_key',
            'date': '_time',
            'driver_number': '_val._key',
            'pit_duration': '_val.Duration',
            'lap_number': '_val.Lap',
        }
        docs = list(query_mongo(
            collection='PitLaneTimeCollection-PitTimes',
            mapping=MAPPING,
            filters_user={k: v for k, v in filters.items()},
            sort_by=[('date', 1)],
        ))
        docs = [e for e in docs if e.get('pit_duration')]
        for doc in docs:
            doc['date'] = do_try(lambda: doc['date'].replace(tzinfo=tzutc()))
        return docs
