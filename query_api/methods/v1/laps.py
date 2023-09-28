from typing import List, Dict, Iterator
from copy import deepcopy
from collections import defaultdict
from datetime import timedelta
from dateutil.tz import tzutc
from base_method import staticproperty, BaseMethod
from db import query_mongo, date_to_session_key
from util import do_try, to_timedelta, group_dicts_by


class Method(BaseMethod):
    @staticproperty
    def description(cls) -> str:
        return '''
            Provides detailed information about individual laps.
        '''
    
    @staticproperty
    def additional_info(cls) -> str:
        return '''
            Below is a table that correlates segment values to the colors displayed on TV broadcasts.    

            <table id="segment_mapping">
                <thead>
                    <tr>
                    <th>Value</th>
                    <th>Color</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                    <td>0</td>
                    <td>not available</td>
                    </tr>
                    <tr>
                    <td><span style="color: #fdde00;">2048</span></td>
                    <td><span style="color: #fdde00;">yellow</span></td>
                    </tr>
                    <tr>
                    <td><span style="color: #4bdd49;">2049</span></td>
                    <td><span style="color: #4bdd49;">green</span></td>
                    </tr>
                    <tr>
                    <td>2050</td>
                    <td>?</td>
                    </tr>
                    <tr>
                    <td><span style="color: #c92cd5;">2051</span></td>
                    <td><span style="color: #c92cd5;">purple</span></td>
                    </tr>
                    <tr>
                    <td>2052</td>
                    <td>?</td>
                    </tr>
                    <tr>
                    <td>2064</td>
                    <td>?</td>
                    </tr>
                    <tr>
                    <td>2068</td>
                    <td>?</td>
                    </tr>
                </tbody>
            </table>

            Segments are not available during races.
            Also, The segment values may not always align perfectly with the colors shown on TV, for unknown reasons.
        '''

    @staticproperty
    def example_filters(cls) -> List[str]:
        return [
            'session_key=9161',
            'driver_number=63',
            'lap_number=8',
        ]
    
    @staticproperty
    def example_response(cls) -> List[Dict]:
        return [
            {
                'meeting_key': 1219,
                'session_key': 9161,
                'driver_number': 63,
                'i1_speed': 307,
                'i2_speed': 277,
                'st_speed': 298,
                'date_start': '2023-09-16T13:59:07.606000+00:00',
                'lap_duration': 91.743,
                'is_pit_out_lap': False,
                'duration_sector_1': 26.966,
                'duration_sector_2': 38.657,
                'duration_sector_3': 26.12,
                'segments_sector_1': [2049, 2049, 2049, 2051, 2049, 2051, 2049, 2049],
                'segments_sector_2': [2049, 2049, 2049, 2049, 2049, 2049, 2049, 2049],
                'segments_sector_3': [2048, 2048, 2048, 2048, 2048, 2064, 2064, 2064],
                'lap_number': 8
            }
        ]

    @staticmethod
    def _query(filters: Dict[str, List[Dict]]) -> Iterator[Dict]:
        query_filters = _get_query_filters(filters)
        yield from _query_raw_lap_data(query_filters)
        yield from _query_raw_sector_data(query_filters)
        yield from _query_raw_segment_data(query_filters)

    @staticmethod
    def _process(docs: List[Dict]) -> List[Dict]:
        docs = sorted(docs, key=lambda x: x['date'])
        laps = list(_process_laps(docs))
        laps = sorted(laps, key=lambda x: x['_tmp_date_start'])
        return laps


def _query_raw_lap_data(filters: Dict[str, List[Dict]]) -> List[Dict]:
    ATT_MAPPING = {
        'date': '_time',
        'meeting_key': '_meeting_key',
        'session_key': '_session_key',
        'driver_number': '_val._key',
        'lap_duration': '_val.LastLapTime.Value',
        'lap_number': '_val.NumberOfLaps',
        'is_pit_out_lap': '_val.PitOut',
        'i1_speed': '_val.Speeds.I1.Value',
        'i2_speed': '_val.Speeds.I2.Value',
        'st_speed': '_val.Speeds.ST.Value',
    }
    docs = list(query_mongo(
        collection='TimingData-Lines',
        mapping=ATT_MAPPING,
        filters_user=filters,
    ))
    for doc in docs:
        doc['date'] = doc['date'].replace(tzinfo=tzutc())
        doc['lap_duration'] = do_try(lambda: to_timedelta(doc['lap_duration']).total_seconds())
    return docs


def _query_raw_sector_data(filters: Dict[str, List[Dict]]) -> List[Dict]:
    ATT_MAPPING = {
        'date': '_time',
        'meeting_key': '_meeting_key',
        'session_key': '_session_key',
        'driver_number': '_val.__key_',
        'sector_duration': '_val._val.Value',
        'sector_idx': '_val._val._key',
    }
    docs = list(query_mongo(
        collection='TimingData-Lines-Sectors',
        mapping=ATT_MAPPING,
        filters_user=filters,
    ))
    for doc in docs:
        doc['date'] = doc['date'].replace(tzinfo=tzutc())
        if 'sector_duration' in doc and 'sector_idx' in doc:
            doc[f'duration_sector_{doc["sector_idx"]+1}'] = doc['sector_duration']
    return docs


def _query_raw_segment_data(filters: Dict[str, List[Dict]]) -> List[Dict]:
    ATT_MAPPING = {
        'date': '_time',
        'meeting_key': '_meeting_key',
        'session_key': '_session_key',
        'driver_number': '_val.__key_',
        'sector_idx': '_val._val.__key_',
        'segment_idx': '_val._val._val._key',
        'segment_status': '_val._val._val.Status',
    }
    docs = list(query_mongo(
        collection='TimingData-Lines-Sectors-Segments',
        mapping=ATT_MAPPING,
        filters_user=filters,
    ))
    for doc in docs:
        doc['date'] = doc['date'].replace(tzinfo=tzutc())

        # Group segment information
        try:
            doc['segment'] = {
                'sector_idx': doc['sector_idx'],
                'idx': doc['segment_idx'],
                'status': doc['segment_status'],
            }
            del doc['sector_idx']
            del doc['segment_idx']
            del doc['segment_status']
        except KeyError:
            pass

    return docs


def _get_query_filters(filters: Dict) -> Dict:
    """We need to process full sessions for maintaining accuracy.
       Filters are adjusted to match this constraint."""
    filters = deepcopy(filters)

    if 'date_start' in filters:
        for filter_ in filters['date_start']:
            session_key = date_to_session_key(filter_['right'])
            if session_key:
                if 'session_key' not in filters:
                    filters['session_key'] = []
                filters['session_key'].append({
                    'op': filter_['op'] + ('=' if '=' not in filter_['op'] else ''),
                    'right': session_key,
                })
            else:
                if 'date' not in filters:
                    filters['date'] = []
                filters['date'].append(filter_)
            
            if filter_['op'] in {'=', '<', '<='}:
                filter_['right'] += timedelta(minutes=5)

        del filters['date_start']

    return {k: v for k, v in filters.items() if k in {
        'date',
        'meeting_key',
        'session_key',
        'driver_number',
    }}


def _group_docs_by_driver_session_lap(docs: List[Dict]) -> Iterator[List[Dict]]:
    """To make sense of data, it is necessary to group it by driver, session and lap."""
    docs_by_driver = group_dicts_by(docs, ['session_key', 'driver_number'])
    for docs in docs_by_driver.values():
        docs_by_lap = [defaultdict(list)]

        for doc in docs:
            if doc.get('lap_number'):
                docs_by_lap.append(defaultdict(list))
            for key, val in doc.items():
                if not val:
                    continue
                
                # If data expected at the end of a lap is received at the begining of a lap,
                # assign the data to the previous lap.
                is_lap_start = 'date' not in docs_by_lap[-1] or (doc['date'] - docs_by_lap[-1]['date'][0]).total_seconds() < 10
                if is_lap_start and key == 'lap_duration':
                    if len(docs_by_lap) >= 2:
                        docs_by_lap[-2][key].append(val)
                elif is_lap_start and key.startswith('duration_sector_'):
                    if len(docs_by_lap) >= 2:
                        docs_by_lap[-2][key].append(val)
                elif key == 'segment' and val['sector_idx'] == 2:
                    if len(docs_by_lap) >= 2:
                        docs_by_lap[-2][key].append(val)
                else:
                    docs_by_lap[-1][key].append(val)

        yield docs_by_lap


def _process_lap(docs_values: Dict[str, List]) -> Dict:
    """Determines lap information given all the raw data received for this lap"""
    lap = {
        'meeting_key': do_try(lambda: docs_values['meeting_key'][0]),
        'session_key': do_try(lambda: docs_values['session_key'][0]),
        'driver_number': do_try(lambda: docs_values['driver_number'][0]),
        'i1_speed': do_try(lambda: docs_values['i1_speed'][-1]),
        'i2_speed': do_try(lambda: docs_values['i2_speed'][-1]),
        'st_speed': do_try(lambda: docs_values['st_speed'][-1]),
        'date_start': do_try(lambda: docs_values['date'][0]),
        'lap_duration': do_try(lambda: docs_values['lap_duration'][-1]),
        'is_pit_out_lap': do_try(lambda: docs_values['is_pit_out_lap'][0]),
    }
    lap['is_pit_out_lap'] = True if lap['is_pit_out_lap'] else False

    for i in range(1, 4):
        lap[f'duration_sector_{i}'] = do_try(lambda: docs_values[f'duration_sector_{i}'][-1])
    
    # Fill in missing lap duration from sector duration, if possible
    sector_dur_sum = do_try(lambda: abs(sum(lap[f'duration_sector_{i}'] for i in range(1, 4))))
    if sector_dur_sum and not lap['lap_duration']:
        lap['lap_duration'] = round(sector_dur_sum, 3)
    
    # Fill in missing sector duration from lap duration, if possible
    for i in range(1, 4):
        if lap[f'duration_sector_{i}'] is None:
            lap[f'duration_sector_{i}'] = 0.
            other_sectors_sum = do_try(lambda: sum(lap[f'duration_sector_{i}'] for i in range(1, 4)))
            lap[f'duration_sector_{i}'] = do_try(lambda: round(lap['lap_duration'] - other_sectors_sum, 3))
    
    # Segments
    for i in range(1, 4):
        sector_segs = [e for e in docs_values['segment'] if e['sector_idx'] == i-1]
        indices = [e['idx'] for e in sector_segs if e['idx'] is not None]
        lap[f'segments_sector_{i}'] = [None] * (max(indices)+1) if indices else []
        for seg in sector_segs:
            if seg['idx'] is None:
                continue
            lap[f'segments_sector_{i}'][seg['idx']] = seg['status']

    return lap


def _process_laps(docs: List[Dict]) -> Iterator[Dict]:
    """Computes lap information from raw data."""
    for docs_group in _group_docs_by_driver_session_lap(docs):
        laps = [_process_lap(e) for e in docs_group]

        # Remove first and last lap if they don't look good
        ATTS = {
            'i1_speed',
            'i2_speed',
            'st_speed',
        }
        if laps and all(laps[0][e] is None for e in ATTS):
            laps = laps[1:]
        if laps and all(laps[-1][e] is None for e in ATTS):
            laps = laps[:-1]

        # Add lap number (this information in raw data is not reliable)
        for i, lap in enumerate(laps):
            lap['lap_number'] = i + 1
        
        # Remove the `start_date` value for the first lap if it looks incorrect
        for lap in laps:
            lap['_tmp_date_start'] = lap['date_start']
        if len(laps) >= 1:
            delta = do_try(lambda: laps[1]['date_start'] - laps[0]['date_start'])
            if delta is None or not timedelta(seconds=45) < delta < timedelta(minutes=20):
                laps[0]['date_start'] = None
        
        yield from laps
