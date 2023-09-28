from typing import List, Dict, Iterator
from dateutil.tz import tzutc
from base_method import staticproperty, BaseMethod
from db import query_mongo
from util import do_try


class Method(BaseMethod):
    @staticproperty
    def description(cls) -> str:
        return '''
            Provides information about race control (racing incidents, flags, safety car, ...).
        '''
    
    @staticproperty
    def example_filters(cls) -> List[str]:
        return [
            'flag=BLACK AND WHITE',
            'driver_number=1',
            'date>=2023-01-01',
            'date<2023-09-01',
        ]

    @staticproperty
    def example_response(cls) -> List[Dict]:
        return [
            {
                'date': '2023-06-04T14:21:01+00:00',
                'lap_number': 59,
                'category': 'Flag',
                'flag': 'BLACK AND WHITE',
                'scope': 'Driver',
                'driver_number': 1,
                'message': 'BLACK AND WHITE FLAG FOR CAR 1 (VER) - TRACK LIMITS',
                'session_key': 9102,
                'meeting_key': 1211,
                'sector': None,
            }
        ]

    @staticmethod
    def _query(filters: Dict[str, List[Dict]]) -> Iterator[Dict]:
        MAPPING = {
            'session_key': '_session_key',
            'meeting_key': '_meeting_key',
            'date': '_val.Utc',
            'category': '_val.Category',
            'flag': '_val.Flag',
            'lap_number': '_val.Lap',
            'message': '_val.Message',
            'driver_number': '_val.RacingNumber',
            'scope': '_val.Scope',
            'sector': '_val.Sector',
        }
        docs = list(query_mongo(
            collection='RaceControlMessages-Messages',
            mapping=MAPPING,
            filters_user={k: v for k, v in filters.items()},
            sort_by=[('date', 1)],
        ))
        for doc in docs:
            doc['date'] = do_try(lambda: doc['date'].replace(tzinfo=tzutc()))
        return docs
