from typing import List, Dict, Iterator
from collections import defaultdict
from base_method import staticproperty, BaseMethod
from db import query_mongo
from util import group_dicts_by, do_try


class Method(BaseMethod):
    @staticproperty
    def description(cls) -> str:
        return '''
            Provides information about individual stints.    
            A stint refers to a period of continuous driving by a driver during a session.
        '''

    @staticproperty
    def example_filters(cls) -> List[str]:
        return [
            'session_key=9165',
            'tyre_age_at_start>=3',
        ]
    
    @staticproperty
    def example_response(cls) -> List[Dict]:
        return [
            {
                'meeting_key': 1219,
                'session_key': 9165,
                'stint_number': 1,
                'driver_number': 16,
                'lap_start': 1,
                'lap_end': 20,
                'compound': 'SOFT',
                'tyre_age_at_start': 3
            },
            {
                'meeting_key': 1219,
                'session_key': 9165,
                'stint_number': 3,
                'driver_number': 20,
                'lap_start': 44,
                'lap_end': 62,
                'compound': 'SOFT',
                'tyre_age_at_start': 3
            }
        ]

    @staticmethod
    def _query(filters: Dict[str, List[Dict]]) -> List[Dict]:
        yield from query_mongo(
            collection='TimingAppData-Lines-Stints',
            mapping={
                'session_key': '_session_key',
                'meeting_key': '_meeting_key',
                'driver_number': '_val.__key_',
                'time': '_time',
                'tyre_age': '_val._val.TotalLaps',
                'compound': '_val._val.Compound',
                'stint_number': '_val._val._key',
            },
            filters_user={k: v for k, v in filters.items() if k in {'session_key', 'meeting_key', 'driver_number'}},
        )
        yield from query_mongo(
            collection='CurrentTyres-Tyres',
            mapping={
                'session_key': '_session_key',
                'meeting_key': '_meeting_key',
                'driver_number': '_val._key',
                'time': '_time',
                'compound': '_val.Compound',
            },
            filters_user={k: v for k, v in filters.items() if k in {'session_key', 'meeting_key', 'driver_number'}},
        )
        yield from query_mongo(
            collection='TimingData-Lines',
            mapping={
                'time': '_time',
                'meeting_key': '_meeting_key',
                'session_key': '_session_key',
                'driver_number': '_val._key',
                'lap_number': '_val.NumberOfLaps',
                'i1_speed': '_val.Speeds.I1.Value',
                'i2_speed': '_val.Speeds.I2.Value',
                'st_speed': '_val.Speeds.ST.Value',
            },
            filters_user={k: v for k, v in filters.items() if k in {'session_key', 'meeting_key', 'driver_number'}},
        )

    @staticmethod
    def _process(docs: List[Dict]) -> List[Dict]:
        docs = sorted(docs, key=lambda x: x['time'])

        stints = []
        for _docs in group_dicts_by(docs, ['session_key', 'driver_number']).values():
            stints += list(_process_stints(docs=_docs))
        
        return sorted(stints, key=lambda x: x['time'])


def _group_docs_by_stint(docs: List[Dict]) -> Iterator[List[Dict]]:
    buf = []
    cur_stint = 0
    for doc in docs:
        if 'stint_number' in doc and doc['stint_number'] > cur_stint:
            if buf:
                yield buf
            buf = []
            cur_stint = doc['stint_number']
        buf.append(doc)

    if buf:    
        yield buf


def _get_data_by_lap(docs: List[Dict]) -> Iterator[List[Dict]]:
    buf = defaultdict(list)
    for doc in docs:
        if doc.get('lap_number'):
            yield buf
            buf = defaultdict(list)
        for key, val in doc.items():
            if val == '':
                continue
            buf[key].append(val)
    yield buf


def _count_laps(docs: List[Dict], is_first_stint: bool, is_last_stint: bool) -> int:
    """Counts number of laps in a stint"""
    n_laps = 0
    data_by_lap = list(_get_data_by_lap(docs))

    # Prevent from counting the first/last lap of a stint twice
    if not is_last_stint:
        data_by_lap = data_by_lap[:-1]

    for lap_number, lap_data in enumerate(data_by_lap):

        # Skip first and last lap of the session if they "don't look good"
        ATTS = {
            'i1_speed',
            'i2_speed',
            'st_speed',
        }
        if (is_first_stint and lap_number == 0
            and all(not lap_data[att] for att in ATTS)):
            continue
        if (is_last_stint and lap_number == len(data_by_lap)-1
            and all(not lap_data[att] for att in ATTS)):
            continue

        n_laps += 1
    
    return n_laps


def _process_stints(docs: List[Dict]) -> Iterator[Dict]:
    """Processes stints for a single session and driver"""
    docs_by_stint = list(_group_docs_by_stint(docs))

    lap_start = [1]
    for stint_number, docs in enumerate(docs_by_stint):
        n_laps = _count_laps(
            docs=docs,
            is_first_stint=stint_number == 0,
            is_last_stint=stint_number == len(docs_by_stint)-1,
        )
        lap_start.append(lap_start[-1] + n_laps)

    for i, docs in enumerate(docs_by_stint):
        yield {
            'meeting_key': do_try(lambda: docs[0]['meeting_key']),
            'session_key': do_try(lambda: docs[0]['session_key']),
            'stint_number': i + 1,
            'driver_number': do_try(lambda: docs[0]['driver_number']),
            'lap_start': lap_start[i],
            'lap_end': lap_start[i+1] - 1,
            'compound': do_try(lambda: [d['compound'] for d in docs if 'compound' in d][-1]),
            'tyre_age_at_start': do_try(lambda: [e.get('tyre_age') for e in docs if e.get('tyre_age') is not None][0]),
            'time': do_try(lambda: docs[0]['time']),
        }
