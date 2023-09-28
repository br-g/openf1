from typing import List, Dict, Iterator
from base_method import staticproperty, BaseMethod
from db import query_mongo
from util import group_dicts_by


class Method(BaseMethod):
    @staticproperty
    def description(cls) -> str:
        return 'Provides information about drivers for each session.'

    @staticproperty
    def example_filters(cls) -> List[str]:
        return [
            'driver_number=1',
            'session_key=9158',
        ]

    @staticproperty
    def example_response(cls) -> List[Dict]:
        return [
            {
                'driver_number': 1,
                'broadcast_name': 'M VERSTAPPEN',
                'full_name': 'Max VERSTAPPEN',
                'name_acronym': 'VER',
                'team_name': 'Red Bull Racing',
                'team_colour': '3671C6',
                'first_name': 'Max',
                'last_name': 'Verstappen',
                'headshot_url': 'https://www.formula1.com/content/dam/fom-website/drivers/M/MAXVER01_Max_Verstappen/maxver01.png.transform/1col/image.png',
                'country_code': 'NED',
                'session_key': 9158,
                'meeting_key': 1219
            }
        ]

    @staticmethod
    def _query(filters: Dict[str, List[Dict]]) -> Iterator[Dict]:
        MAPPING = {
            'session_key': '_session_key',
            'meeting_key': '_meeting_key',
            'broadcast_name': 'BroadcastName',
            'country_code': 'CountryCode',
            'first_name': 'FirstName',
            'full_name': 'FullName',
            'headshot_url': 'HeadshotUrl',
            'last_name': 'LastName',
            'driver_number': 'RacingNumber',
            'team_colour': 'TeamColour',
            'team_name': 'TeamName',
            'name_acronym': 'Tla',
        }
        return query_mongo(
            collection='DriverList',
            mapping=MAPPING,
            filters_user={k: v for k, v in filters.items()},
        )

    @staticmethod
    def _process(docs: List[Dict]) -> Iterator[Dict]:
        docs = [e for e in docs if 'driver_number' in e]
        if not docs:
            return

        # If there are multiple documents per driver, keep only the last one
        groups = group_dicts_by(docs, attributes=['meeting_key', 'session_key', 'driver_number'])
        for _, group in sorted(list(groups.items())):
            yield group[-1]
