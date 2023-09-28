from typing import List, Dict, Iterator, Union, Optional
from dateutil.tz import tzutc
from base_method import staticproperty, BaseMethod
from db import query_mongo
from util import do_try


class Method(BaseMethod):
    @staticproperty
    def description(cls) -> str:
        return '''
            Fetches real-time interval data between drivers and their gap to the race leader.    
            Available during races only, with updates approximately every 4 seconds.
        '''

    @staticproperty
    def example_filters(cls) -> List[str]:
        return [
            'session_key=9165',
            'interval<0.005',
        ]
    
    @staticproperty
    def example_response(cls) -> List[Dict]:
        return [
            {
                'gap_to_leader': 41.019,
                'interval': 0.003,
                'driver_number': 1,
                'date': '2023-09-17T13:31:02.395000+00:00',
                'session_key': 9165,
                'meeting_key': 1219
            }
        ]

    @staticmethod
    def _query(filters: Dict[str, List[Dict]]) -> Iterator[Dict]:
        MAPPING = {
            'session_key': '_session_key',
            'meeting_key': '_meeting_key',
            'date': '_time',
            'driver_number': '_key',
            'gap_to_leader': 'Gap',
            'interval': 'Interval',
        }
        docs = list(query_mongo(
            collection='DriverRaceInfo',
            mapping=MAPPING,
            filters_user={k: v for k, v in filters.items()},
            sort_by=[('date', 1)],
        ))
        docs = [e for e in docs if e.get('interval') or e.get('gap_to_leader')]
        for doc in docs:
            doc['date'] = do_try(lambda: doc['date'].replace(tzinfo=tzutc()))
        return docs

    @staticmethod
    def _process(docs: List[Dict]) -> List[Dict]:
        for doc in docs:
            doc['gap_to_leader'] = _parse_time_delta(doc.get('gap_to_leader'))
            doc['interval'] = _parse_time_delta(doc.get('interval'))
        return docs


def _parse_time_delta(time_delta: Optional[Union[str, float]]) -> Optional[float]:
    if not time_delta:
        return None

    # Handle leader
    if str(time_delta).upper().startswith('LAP'):
        return 0.
    
    # Handle case where `time_delta` >= 60 seconds
    if str(time_delta).startswith('+'):
        minutes, seconds = map(float, time_delta.split(':'))
        return minutes * 60 + seconds
    
    else:
        assert isinstance(time_delta, float), \
            f'Expected float type. Found {type(time_delta)} (value: `{time_delta}`)'
        return time_delta
