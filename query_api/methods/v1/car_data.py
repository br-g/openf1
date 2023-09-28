from typing import List, Dict, Iterator
from dateutil.tz import tzutc
from base_method import staticproperty, BaseMethod
from db import query_mongo
from util import do_try


class Method(BaseMethod):
    @staticproperty
    def description(cls) -> str:
        return 'Some data about each car, at a sample rate of about 3.7 Hz.'
    
    @staticproperty
    def additional_info(cls) -> str:
        return '''
            Below is a table that correlates DRS values to its supposed interpretation
            (from <a href="https://github.com/theOehrly/Fast-F1/blob/317bacf8c61038d7e8d0f48165330167702b349f/fastf1/_api.py#L863" target="_blank">FastF1</a>). 

            <table id="drs_values">
                <thead>
                    <tr>
                    <th>DRS value</th>
                    <th>Interpretation</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                    <td>0</td>
                    <td>DRS off</td>
                    </tr>
                    <tr>
                    <td>1</td>
                    <td>DRS off</td>
                    </tr>
                    <tr>
                    <td>2</td>
                    <td>?</td>
                    </tr>
                    <tr>
                    <td>3</td>
                    <td>?</td>
                    </tr>
                    <tr>
                    <td>8</td>
                    <td>Detected, eligible once in activation zone</td>
                    </tr>
                    <tr>
                    <td>9</td>
                    <td>?</td>
                    </tr>
                    <tr>
                    <td>10</td>
                    <td>DRS on</td>
                    </tr>
                    <tr>
                    <td>12</td>
                    <td>DRS on</td>
                    </tr>
                    <tr>
                    <td>14</td>
                    <td>DRS on</td>
                    </tr>
                </tbody>
            </table>
        '''

    @staticproperty
    def example_filters(cls) -> List[str]:
        return [
            'driver_number=55',
            'session_key=9159',
            'speed>=315',
        ]

    @staticproperty
    def example_response(cls) -> List[Dict]:
        return [
            {
                'driver_number': 55,
                'rpm': 11141,
                'speed': 315,
                'n_gear': 8,
                'throttle': 99,
                'brake': 0,
                'drs': 12,
                'date': '2023-09-15T13:08:19.923000+00:00',
                'session_key': 9159,
                'meeting_key': 1219
            },
            {
                'driver_number': 55,
                'rpm': 11023,
                'speed': 315,
                'n_gear': 8,
                'throttle': 57,
                'brake': 100,
                'drs': 8,
                'date': '2023-09-15T13:35:41.808000+00:00',
                'session_key': 9159,
                'meeting_key': 1219
            }
        ]

    @staticmethod
    def _query(filters: Dict[str, List[Dict]]) -> Iterator[Dict]:
        MAPPING = {
            'meeting_key': '_meeting_key',
            'session_key': '_session_key',
            'driver_number': '_val._val._key',
            'date': '_val._Utc_',
            'rpm': '_val._val.ch_0',
            'speed': '_val._val.ch_2',
            'n_gear': '_val._val.ch_3',
            'throttle': '_val._val.ch_4',
            'drs': '_val._val.ch_45',
            'brake': '_val._val.ch_5',
        }
        docs = list(query_mongo(
            collection='CarData.z-Entries-Cars',
            mapping=MAPPING,
            filters_user={k: v for k, v in filters.items()},
            sort_by=[('date', 1)],
        ))
        for doc in docs:
            doc['date'] = do_try(lambda: doc['date'].replace(tzinfo=tzutc()))

        return docs
