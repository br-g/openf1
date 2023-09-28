"""Base class for API methods."""

from typing import List, Set, Dict, Iterable, Optional
from abc import ABC, abstractmethod
from filters import filter_results


class staticproperty(object):
    def __init__(self, getter):
        self.getter = getter

    def __get__(self, instance, owner):
        return self.getter(owner)


class BaseMethod(ABC):
    @staticproperty
    @abstractmethod
    def description(cls) -> str:
        pass

    @staticproperty
    def additional_info(cls) -> str:
        return ''

    @staticproperty
    @abstractmethod
    def example_filters(cls) -> List[str]:
        pass

    @staticproperty
    @abstractmethod
    def example_response(cls) -> List[Dict]:
        pass

    @staticproperty
    def attributes(cls) -> Optional[Set[str]]:
        return set(cls.example_response[0].keys()) if cls.example_response else None

    @classmethod
    @abstractmethod
    def _query(cls, filters: Dict[str, List[Dict]]) -> Iterable[Dict]:
        pass

    @classmethod
    def _process(cls, docs: Iterable[Dict]) -> Iterable[Dict]:
        return docs

    @classmethod
    def query_process_filter(cls, filters: Dict[str, List[Dict]]) -> List[Dict]:
        res = list(cls._process(list(cls._query(filters))))
        res = filter_results(res, filters=filters)

        attributes = cls.attributes
        if attributes:
            # Remove unwanted attributes
            res = [{k: v for k, v in e.items() if k in attributes} for e in res]
            
            # Add missing attributes
            add_missing_attributes(res, attributes=attributes)

        return res


def add_missing_attributes(docs: List[Dict], attributes: List[str]):
    """Fills missing attributes with `None`"""
    for doc in docs:
        for att in attributes:
            if att not in doc:
                doc[att] = None
