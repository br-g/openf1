import functools
import traceback
from collections import defaultdict

from openf1.services.ingestor_livetiming.core.objects import (
    Document,
    Message,
    get_topics_to_collections_mapping,
)
from openf1.util.multiprocessing import map_parallel


def process_message(
    meeting_key: int, session_key: int, collection_names: list[str] | None, message: Message
) -> dict[str, list[Document]]:
    """Processes a message from a given topic and returns processed documents grouped
    by collection. If at least one collection name is given, only those collections are used."""
    # Select collections which could use this message
    selected_collections = get_topics_to_collections_mapping(
        meeting_key=meeting_key, session_key=session_key
    ).get(message.topic)
    if selected_collections is None:
        return {}
    
    if collection_names is not None and len(collection_names) > 0:
        selected_collections = [collection for collection in selected_collections if collection.name in collection_names]

    # Process message with each select collection
    results = {}
    for collection in selected_collections:
        try:
            documents = list(collection.process_message(message))
            if len(documents) > 0:
                results[collection.__class__.name] = documents
        except Exception:
            traceback.print_exc()

    return results


def process_messages(
    meeting_key: int,
    session_key: int,
    messages: list[Message],
    collection_names: list[str],
    parallel: bool = False,
    max_workers: int | None = None,
    batch_size: int | None = None,
) -> dict[str, list[Document]]:
    """Processes messages and returns the generated documents by collection"""
    docs_buf = defaultdict(dict)

    if parallel:
        # Collections that should be processed sequentially (don't have many messages or maintain state)
        sequential_collections = ["championship_drivers", "championship_teams", "drivers", "laps", "pit", "race_control", "stints", "team_radio", "weather"]
        sequential_processed = (
            process_message(
                meeting_key=meeting_key,
                session_key=session_key,
                collection_names=[collection for collection in collection_names if collection in sequential_collections],
                message=message
            )
            for message in messages
        )

        for p in sequential_processed:
            for collection, docs in p.items():
                for doc in docs:
                    # Replace previous version of the same doc if it exists
                    docs_buf[collection][doc] = doc

        # Collections that can be parallelized (do not maintain state)
        parallel_collections = ["car_data", "intervals", "location", "overtakes", "position"]
        parallel_processed = (
            map_parallel(
                functools.partial(
                    process_message,
                    meeting_key,
                    session_key,
                    [collection for collection in collection_names if collection in parallel_collections]
                ),
                messages,
                max_workers=max_workers,
                batch_size=batch_size,
            )
        )

        # Avoid synchronization with sequential memory writes
        for p in parallel_processed:
            for collection, docs in p.items():
                for doc in docs:
                    # Replace previous version of the same doc if it exists
                    docs_buf[collection][doc] = doc
    else:
        processed = (
            process_message(
                meeting_key=meeting_key,
                session_key=session_key,
                collection_names=None,
                message=message
            )
            for message in messages
        )

        for p in processed:
            for collection, docs in p.items():
                for doc in docs:
                    # Replace previous version of the same doc if it exists
                    docs_buf[collection][doc] = doc

    docs_by_collection = {col: sorted(list(docs_buf[col].values())) for col in docs_buf}
    return docs_by_collection
