from typing import List, Dict, Iterator
from dateutil.tz import tzutc
from base_method import staticproperty, BaseMethod
from db import query_mongo
from util import do_try


class Method(BaseMethod):
    @staticproperty
    def description(cls) -> str:
        return '''
            Provides driver positions throughout a session, including initial
            placement and subsequent changes.
        '''

    @staticproperty
    def example_filters(cls) -> List[str]:
        return [
            'meeting_key=1217',
            'driver_number=40',
            'position<=3',
        ]

    @staticproperty
    def example_response(cls) -> List[Dict]:
        return [
            {
                'position': 2,
                'driver_number': 40,
                'date': '2023-08-26T09:30:47.199000+00:00',
                'session_key': 9144,
                'meeting_key': 1217
            },
            {
                'position': 3,
                'driver_number': 40,
                'date': '2023-08-26T09:35:51.477000+00:00',
                'session_key': 9144,
                'meeting_key': 1217
            }
        ]

    @staticmethod
    def _query(filters: Dict[str, List[Dict]]) -> Iterator[Dict]:
        MAPPING = {
            'session_key': '_session_key',
            'meeting_key': '_meeting_key',
            'driver_number': '_val._key',
            'date': '_time',
            'position': '_val.Line',
        }
        docs = list(query_mongo(
            collection='TimingAppData-Lines',
            mapping=MAPPING,
            filters_user={k: v for k, v in filters.items()},
            sort_by=[('date', 1)],
        ))
        docs = [e for e in docs if 'position' in e]
        for doc in docs:
            doc['date'] = do_try(lambda: doc['date'].replace(tzinfo=tzutc()))
        return docs
