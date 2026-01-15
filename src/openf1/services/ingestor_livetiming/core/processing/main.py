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
    meeting_key: int, session_key: int, message: Message
) -> dict[str, list[Document]]:
    """Processes a message from a given topic and returns processed documents grouped
    by collection"""
    # Select collections which could use this message
    selected_collections = get_topics_to_collections_mapping(
        meeting_key=meeting_key, session_key=session_key
    ).get(message.topic)
    if selected_collections is None:
        return {}

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
    parallel: bool = False,
    max_workers: int | None = None,
    batch_size: int | None = None,
) -> dict[str, list[Document]]:
    """Processes messages and returns the generated documents by collection"""
    docs_buf = defaultdict(dict)

    processed = (
        map_parallel(
            functools.partial(process_message, meeting_key, session_key),
            messages,
            max_workers=max_workers,
            batch_size=batch_size,
        )
        if parallel
        else (
            process_message(
                meeting_key=meeting_key, session_key=session_key, message=message
            )
            for message in messages
        )
    )

    # Avoid synchronization with sequential memory writes
    for p in processed:
        for collection, docs in p.items():
            for doc in docs:
                # Replace previous version of the same doc if it exists
                docs_buf[collection][doc] = doc

    docs_by_collection = {col: sorted(list(docs_buf[col].values())) for col in docs_buf}
    return docs_by_collection
