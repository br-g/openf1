from typing import List, Dict, Tuple, Optional, Iterator, Iterable, Optional
import os
from copy import deepcopy
from datetime import datetime, timedelta
from pymongo import MongoClient
from filters import OPERATORS_MAP
from util import timed_cache

# Public and read only
client = MongoClient(os.getenv('MONGO_CONNECTION_STRING'))
db = client['raw']


def _filter_and_rename(docs: Iterable[Dict], mapping: Dict[str, str]) -> Iterator[Dict]:
    """Filters and renames attributes in retrieved MongoDB documents. Keeps only
       attributes present in `mapping`
    """
    mapping_rev = {v: k for k, v in mapping.items()}
    for doc in docs:
        res = {}
        for k, v in doc.items():
            if k in mapping_rev:
                res[mapping_rev[k]] = v
        yield res


def _flatten_doc(doc: Dict) -> Dict:
    """Flattens a nested dictionary structure by converting it into a single-level dictionary
       where keys from nested dictionaries are concatenated with a dot ('.') separator
    """
    res = {}
    for key, val in doc.items():
        if isinstance(val, dict):
            for _key, _val in _flatten_doc(val).items():
                res[f'{key}.{_key}'] = _val
        else:
            res[key] = val
    return res


def query_mongo(collection: str,
                mapping: Dict[str, Optional[str]],
                filters_user: Optional[Dict[str, List[Dict]]] = None,
                filters_other: Optional[Dict[str, List[Dict]]] = None,
                sort_by: Optional[List[Tuple[str, int]]] = None) -> List[Dict]:
    """Queries a MongoDB collection. Renames, filters and sorts"""
    # Rename using provided `mapping`
    filters_user = {mapping[k]: v for k, v in filters_user.items()} if filters_user else {}
    filters_other = {mapping[k] if k in mapping else k: v for k, v in filters_other.items()} \
                    if filters_other else {}
    sort_by = [(mapping[k] if k in mapping else k, v) for k, v in sort_by] \
              if sort_by else None
    
    # Turn `filters_user` into mongoDB filters
    filters_user_mongo = {}
    if filters_user:
        for key, vals in filters_user.items():
            filters_user_mongo[key] = {OPERATORS_MAP[e['op']]['mongo']: e['right'] for e in vals}
    
    # Combine filters
    filters_combined = deepcopy(filters_user_mongo)
    for left, vals in filters_other.items():
        if left not in filters_combined:
            filters_combined[left] = {}
        for op, right in vals.items():
            assert op not in filters_combined[left]
            filters_combined[left][op] = right

    # Query MongoDB
    docs = db[collection].find(filters_combined)

    # Sort
    if sort_by:
        docs = docs.sort(sort_by)

    # Postprocess
    docs = [_flatten_doc(e) for e in docs]
    docs = list(_filter_and_rename(docs, mapping=mapping))

    return docs


def date_to_session_key(date: datetime) -> Optional[int]:
    """If the date is during a session, returns the key of the session.
       Otherwise returns `None`
    """
    collection = db['TimingData-Lines']
    documents = list(collection.find({'_time': {
        '$gte': date - timedelta(minutes=5),
        '$lte': date + timedelta(minutes=5)
    }}).limit(1))

    if documents:
        return documents[0]['_session_key']
    else:
        return None


@timed_cache(60)  # Cache the output for 1 minute
def _get_latest_session_info() -> int:
    docs = list(db['SessionInfo'].find().sort('StartDate', -1).limit(1))
    if docs:
        return docs[0]
    else:
        raise SystemError('Could not determine the key of the latest meeting')

def get_latest_meeting_key() -> int:
    return _get_latest_session_info()['_meeting_key']

def get_latest_session_key() -> int:
    return _get_latest_session_info()['_session_key']
