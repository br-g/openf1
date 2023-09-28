from typing import List, Dict, Iterator, Optional
from base_method import staticproperty, BaseMethod
from db import db, query_mongo
from util import timed_cache


class Method(BaseMethod):
    @staticproperty
    def description(cls) -> str:
        return '''
            Provides a collection of radio exchanges between Formula 1 drivers and their respective teams during sessions.    
            Please note that only a limited selection of communications are included, not the complete record of radio interactions.
        '''

    @staticproperty
    def example_filters(cls) -> List[str]:
        return [
            'session_key=9158',
            'driver_number=11',
        ]

    @staticproperty
    def example_response(cls) -> List[Dict]:
        return [
            {
                'date': '2023-09-15T09:40:43.005000',
                'driver_number': 11,
                'session_key': 9158,
                'meeting_key': 1219,
                'recording_url': 'https://livetiming.formula1.com/static/2023/2023-09-17_Singapore_Grand_Prix/2023-09-15_Practice_1/TeamRadio/SERPER01_11_20230915_104008.mp3'
            },
            {
                'date': '2023-09-15T10:32:47.325000',
                'driver_number': 11,
                'session_key': 9158,
                'meeting_key': 1219,
                'recording_url': 'https://livetiming.formula1.com/static/2023/2023-09-17_Singapore_Grand_Prix/2023-09-15_Practice_1/TeamRadio/SERPER01_11_20230915_113201.mp3'
            }
        ]

    @staticmethod
    def _query(filters: Dict[str, List[Dict]]) -> Iterator[Dict]:
        MAPPING = {
            'session_key': '_session_key',
            'meeting_key': '_meeting_key',
            'driver_number': '_val.RacingNumber',
            'date': '_val.Utc',
            '_path': '_val.Path',
        }
        return query_mongo(
            collection='TeamRadio-Captures',
            mapping=MAPPING,
            filters_user={k: v for k, v in filters.items()},
            sort_by=[('date', 1)],
        )

    @staticmethod
    def _process(docs: List[Dict]) -> List[Dict]:
        for doc in docs:
            session_url = _get_session_url(doc['session_key'])
            if session_url:
                doc['recording_url'] = session_url + doc['_path']
        
        return [e for e in docs if 'recording_url' in e]


@timed_cache(300)  # Cache the output for 5 minutes
def _get_session_url(session_key: int) -> Optional[str]:
    """Returns the base URL of a specific session"""
    docs = list(db['SessionInfo'].find({'_session_key': {'$eq': session_key}}))
    if not docs:
        return None
    return 'https://livetiming.formula1.com/static/' + docs[-1]['Path']
