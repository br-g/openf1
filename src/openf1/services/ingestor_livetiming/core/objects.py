"""This module provides a framework for processing messages from various topics into
structured documents and organizing them into collections.

cf. https://github.com/br-g/openf1/blob/main/src/openf1/services/ingestor_livetiming/README.md
"""

import asyncio
import importlib
import inspect
import sys
import time
from abc import ABC, abstractmethod
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import Iterator

_id_lock = asyncio.Lock()
_last_id = 0


def _generate_mongo_id_sync() -> int:
    """Generates a unique, monotonically increasing ID based on time"""
    global _last_id
    time_ms = time.time_ns() // 1_000_000
    if time_ms <= _last_id:
        time_ms = _last_id + 1
    _last_id = time_ms
    return time_ms


async def _generate_mongo_id_async() -> int:
    """Generates a unique, monotonically increasing ID based on time"""
    global _last_id
    time_ms = time.time_ns() // 1_000_000
    async with _id_lock:
        if time_ms <= _last_id:
            time_ms = _last_id + 1
        _last_id = time_ms
    return time_ms


@dataclass
class Message:
    topic: str
    content: dict
    timepoint: datetime


@dataclass
class Document(ABC):
    """An element of a collection, computed from topic messages"""

    @property
    @abstractmethod
    def unique_key(self) -> tuple:
        """Returns a key generated from content, used for detecting duplicates"""
        pass

    def _get_key_str(self) -> str:
        """Generates a string ID, used for detecting duplicates"""
        # Convert key component to strings
        unique_key_str = [
            str(int(k.timestamp() * 1000)) if isinstance(k, datetime) else str(k)
            for k in self.unique_key
        ]
        id_ = "_".join(unique_key_str)
        return id_

    def to_mongo_doc_sync(self) -> dict:
        """Converts the Document instance to a dictionary, adding '_key' and
        '_id' properties to help retrieving the right documents are query time"""
        mongo_doc = self.__dict__
        mongo_doc["_key"] = self._get_key_str()
        mongo_doc["_id"] = _generate_mongo_id_sync()
        return mongo_doc

    async def to_mongo_doc_async(self) -> dict:
        """Converts the Document instance to a dictionary, adding '_key' and
        '_id' properties to help retrieving the right documents are query time"""
        mongo_doc = self.__dict__
        mongo_doc["_key"] = self._get_key_str()
        mongo_doc["_id"] = await _generate_mongo_id_async()
        return mongo_doc

    def __eq__(self, other):
        if (
            isinstance(other, Document)
            and self.__class__.__name__ == other.__class__.__name__
        ):
            return self.unique_key == other.unique_key
        return False

    def __lt__(self, other):
        for e_self, e_other in zip(self.unique_key, other.unique_key):
            try:
                return e_self < e_other
            except (
                TypeError
            ):  # elements can't be compared (because of a None for example)
                continue
        return False

    def __hash__(self):
        return hash((self.__class__.__name__, self.unique_key))


@dataclass
class Collection(ABC):
    """Represents a collection of documents"""

    meeting_key: int
    session_key: int
    name: str | None = None
    source_topics: set[str] | None = None

    @abstractmethod
    def process_message(
        self, topic: str, timepoint: datetime, message: dict
    ) -> Iterator[Document]:
        """Processes a message from a given topic into collection documents"""
        pass

    def __hash__(self):
        return hash(self.__class__.__name__)


@lru_cache()
def _get_collections_cls_by_name() -> dict[str, type[Collection]]:
    """Collects collection classes from the 'processing/collections' directory"""
    collections_dir = Path(__file__).parent / "processing/collections"
    package_name = f"{sys.modules[__name__].__package__}.processing.collections"

    collections_cls = {}
    for file_path in collections_dir.glob("*.py"):
        module_name = f"{package_name}.{file_path.stem}"
        module = importlib.import_module(module_name, package=__package__)
        for _, cls in inspect.getmembers(module):
            if (
                inspect.isclass(cls)
                and issubclass(cls, Collection)
                and cls != Collection
            ):
                collections_cls[cls.name] = cls

    return collections_cls


@lru_cache()
def get_collections(meeting_key: int, session_key: int) -> list[Collection]:
    """Returns the instances of all available collections for a given session"""
    collections = [
        cls(meeting_key=meeting_key, session_key=session_key, name=cls.name, source_topics=cls.source_topics)
        for cls in _get_collections_cls_by_name().values()
    ]
    collections = sorted(collections, key=lambda c: c.__class__.name)
    return collections


def get_source_topics(collection_name: str) -> set[str]:
    """Returns the topics needed for computing a collection"""
    collection_cls = _get_collections_cls_by_name()[collection_name]
    return collection_cls.source_topics


@lru_cache()
def get_topics_to_collections_mapping(
    meeting_key: int, session_key: int
) -> dict[str, list[Collection]]:
    """Creates and caches a mapping between topics and collections generated from
    this topic"""
    res = defaultdict(list)

    collections = get_collections(meeting_key, session_key)
    for collection in collections:
        for topic in collection.__class__.source_topics:
            res[topic].append(collection)

    return dict(res)


def get_topics() -> set[str]:
    """Returns the set of topics which are used to process collections"""
    topics = set()
    for cls in _get_collections_cls_by_name().values():
        topics.update(cls.source_topics)
    topics.add("SessionInfo")
    return topics
