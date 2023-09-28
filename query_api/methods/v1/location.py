from typing import List, Dict, Iterator
from dateutil.tz import tzutc
from base_method import staticproperty, BaseMethod
from db import query_mongo
from util import do_try


class Method(BaseMethod):
    @staticproperty
    def description(cls) -> str:
        return '''
            The approximate location of the cars on the circuit, at a sample rate of about 3.7 Hz.    
            Useful for gauging their progress along the track, but lacks details about lateral placement — i.e. whether
            the car is on the left or right side of the track. The origin point (0, 0, 0) appears to be arbitrary
            and not tied to any specific location on the track.
        '''

    @staticproperty
    def example_filters(cls) -> List[str]:
        return [
            'session_key=9161',
            'driver_number=81',
            'date>2023-09-16T13:03:35.200',
            'date<2023-09-16T13:03:35.800',
        ]

    @staticproperty
    def example_response(cls) -> List[Dict]:
        return [
            {
                'x': 567,
                'y': 3195,
                'z': 187,
                'driver_number': 81,
                'date': '2023-09-16T13:03:35.292000+00:00',
                'session_key': 9161,
                'meeting_key': 1219
            },
            {
                'x': 489,
                'y': 3403,
                'z': 186,
                'driver_number': 81,
                'date': '2023-09-16T13:03:35.752000+00:00',
                'session_key': 9161,
                'meeting_key': 1219
            }
        ]

    @staticmethod
    def _query(filters: Dict[str, List[Dict]]) -> Iterator[Dict]:
        MAPPING = {
            'meeting_key': '_meeting_key',
            'session_key': '_session_key',
            'driver_number': '_val._val._key',
            'date': '_val._Timestamp_',
            'x': '_val._val.X',
            'y': '_val._val.Y',
            'z': '_val._val.Z',
        }
        docs = list(query_mongo(
            collection='Position.z-Position-Entries',
            mapping=MAPPING,
            filters_user={k: v for k, v in filters.items()},
            sort_by=[('date', 1)],
        ))
        for doc in docs:
            doc['date'] = do_try(lambda: doc['date'].replace(tzinfo=tzutc()))

        return docs
