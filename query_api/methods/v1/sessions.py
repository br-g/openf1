from typing import List, Dict, Iterator
from collections import defaultdict
from datetime import datetime
import pytz
from base_method import staticproperty, BaseMethod
from db import query_mongo
from util import add_timezone_info, do_try, deduplicate_dicts


class Method(BaseMethod):
    @staticproperty
    def description(cls) -> str:
        return '''
            Provides information about sessions.    
            A session refers to a distinct period of track activity during a Grand Prix or testing weekend (practice, qualifying, sprint, race, ...).
        '''

    @staticproperty
    def example_filters(cls) -> List[str]:
        return [
            'country_name=Belgium',
            'session_name=Sprint',
            'year=2023',
        ]

    @staticproperty
    def example_response(cls) -> List[Dict]:
        return [
            {
                'location': 'Spa-Francorchamps',
                'country_key': 16,
                'country_code': 'BEL',
                'country_name': 'Belgium',
                'circuit_key': 7,
                'circuit_short_name': 'Spa-Francorchamps',
                'session_type': 'Race',
                'session_name': 'Sprint',
                'date_start': '2023-07-29T15:05:00+00:00',
                'date_end': '2023-07-29T15:35:00+00:00',
                'gmt_offset': '02:00:00',
                'session_key': 9140,
                'meeting_key': 1216,
                'year': 2023
            }
        ]

    @staticmethod
    def _query(filters: Dict[str, List[Dict]]) -> Iterator[Dict]:
        filters = _replace_year_filter(filters)
        MAPPING = {
            'session_key': '_session_key',
            'session_name': 'Name',
            'date_start': 'StartDate',
            'date_end': 'EndDate',
            'gmt_offset': 'GmtOffset',
            'session_type': 'Type',
            'meeting_key': '_meeting_key',
            'location': 'Meeting.Location',
            'country_key': 'Meeting.Country.Key',
            'country_code': 'Meeting.Country.Code',
            'country_name': 'Meeting.Country.Name',
            'circuit_key': 'Meeting.Circuit.Key',
            'circuit_short_name': 'Meeting.Circuit.ShortName',
        }
        return query_mongo(
            collection='SessionInfo',
            mapping=MAPPING,
            filters_user={k: v for k, v in filters.items()},
            sort_by=[('date_start', 1)],
        )
        
    @staticmethod
    def _process(docs: List[Dict]) -> List[Dict]:
        for doc in docs:
            doc['date_start'] = do_try(lambda: add_timezone_info(dt=doc['date_start'], gmt_offset=doc['gmt_offset']))
            doc['date_end'] = do_try(lambda: add_timezone_info(dt=doc['date_end'], gmt_offset=doc['gmt_offset']))
            doc['year'] = do_try(lambda: doc['date_start'].year)
        docs = deduplicate_dicts(docs)
        return docs


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
                filters['date_end'].append({
                    'op': '<' if filter['op'] == '=' else filter['op'],
                    'right': datetime(filter['right']+1, 1, 1).replace(tzinfo=pytz.utc),
                })
        del filters['year']
    return filters
