from typing import List, Dict, Iterator
from collections import defaultdict
from datetime import datetime
import pytz
from base_method import staticproperty, BaseMethod
from db import query_mongo
from util import add_timezone_info, do_try, group_dicts_by


class Method(BaseMethod):
    @staticproperty
    def description(cls) -> str:
        return '''
            Provides information about meetings.    
            A meeting refers to a Grand Prix or testing weekend and usually includes multiple sessions (practice, qualifying, race, ...).
        '''

    @staticproperty
    def example_filters(cls) -> List[str]:
        return [
            'year=2023',
            'country_name=Singapore',
        ]
    
    @staticproperty
    def example_response(cls) -> List[Dict]:
        return [
            {
                'meeting_name': 'Singapore Grand Prix',
                'meeting_official_name': 'FORMULA 1 SINGAPORE AIRLINES SINGAPORE GRAND PRIX 2023',
                'location': 'Marina Bay',
                'country_key': 157,
                'country_code': 'SGP',
                'country_name': 'Singapore',
                'circuit_key': 61,
                'circuit_short_name': 'Singapore',
                'date_start': '2023-09-15T09:30:00+00:00',
                'gmt_offset': '08:00:00',
                'meeting_key': 1219,
                'year': 2023
            }
        ]

    @staticmethod
    def _query(filters: Dict[str, List[Dict]]) -> Iterator[Dict]:
        filters = _replace_year_filter(filters)
        MAPPING = {
            'circuit_key': 'Meeting.Circuit.Key',
            'circuit_short_name': 'Meeting.Circuit.ShortName',
            'meeting_key': '_meeting_key',
            'meeting_code': 'Meeting.Country.Code',
            'location': 'Meeting.Location',
            'country_key': 'Meeting.Country.Key',
            'country_code': 'Meeting.Country.Code',
            'country_name': 'Meeting.Country.Name',
            'meeting_name': 'Meeting.Name',
            'meeting_official_name': 'Meeting.OfficialName',
            'gmt_offset': 'GmtOffset',
            'date_start': 'StartDate',
            '_session_name': 'Name',
        }
        return query_mongo(
            collection='SessionInfo',
            mapping=MAPPING,
            filters_user={k: v for k, v in filters.items()},
            sort_by=[('date_start', 1)],
        )
        
    @staticmethod
    def _process(docs: List[Dict]) -> List[Dict]:
        docs = [docs[0] for docs in group_dicts_by(docs, attributes=['meeting_key']).values()]

        # Handle case where the `date_start` user filter is in the middle of a GP
        if docs and docs[0]['_session_name'].lower() != 'practice 1':
            docs = docs[1:]
        
        for doc in docs:
            doc['date_start'] = do_try(lambda: add_timezone_info(dt=doc['date_start'], gmt_offset=doc['gmt_offset']))
            doc['year'] = do_try(lambda: doc['date_start'].year)
            doc['meeting_official_name'] = doc['meeting_official_name'].strip(' ')
        return sorted(docs, key=lambda x: x['date_start'])


def _replace_year_filter(filters: Dict) -> Dict:
    """Replaces the `year` filter with a `date_start` equivalent (`year` doesn't
       exist in raw data)"""
    if 'year' in filters:
        filters = defaultdict(list, filters)
        for filter in filters['year']:
            if filter['op'] in {'>=', '>', '='}:
                filters['date_start'].append({
                    'op': '>=' if filter['op'] == '=' else filter['op'],
                    'right': datetime(filter['right'], 1, 1).replace(tzinfo=pytz.utc),
                })
            if filter['op'] in {'<=', '<', '='}:
                filters['date_start'].append({
                    'op': '<' if filter['op'] == '=' else filter['op'],
                    'right': datetime(filter['right']+1, 1, 1).replace(tzinfo=pytz.utc),
                })
        del filters['year']
    return filters
