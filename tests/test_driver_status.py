from datetime import datetime, timezone

from openf1.services.ingestor_livetiming.core.objects import Message
from openf1.services.ingestor_livetiming.core.processing.collections.driver_status import (
    DriverStatusCollection,
)


def test_processes_retired_and_stopped_flags():
    date = datetime(2026, 7, 12, 14, 32, 10, tzinfo=timezone.utc)
    collection = DriverStatusCollection(meeting_key=1290, session_key=11300)
    message = Message(
        topic="TimingData",
        content={
            "Lines": {
                "1": {"Retired": False, "Stopped": False},
                "16": {"Retired": True, "Stopped": False},
            }
        },
        timepoint=date,
    )

    statuses = list(collection.process_message(message))

    assert [
        (status.driver_number, status.retired, status.stopped) for status in statuses
    ] == [(1, False, False), (16, True, False)]
    assert all(status.meeting_key == 1290 for status in statuses)
    assert all(status.session_key == 11300 for status in statuses)
    assert all(status.date == date for status in statuses)


def test_keeps_last_known_flag_when_timing_data_is_partial():
    collection = DriverStatusCollection(meeting_key=1290, session_key=11300)
    first_message = Message(
        topic="TimingData",
        content={"Lines": {"1": {"Retired": False, "Stopped": False}}},
        timepoint=datetime(2026, 7, 12, 14, 32, 10, tzinfo=timezone.utc),
    )
    second_message = Message(
        topic="TimingData",
        content={"Lines": {"1": {"Retired": True}}},
        timepoint=datetime(2026, 7, 12, 14, 33, 10, tzinfo=timezone.utc),
    )

    list(collection.process_message(first_message))
    status = list(collection.process_message(second_message))[0]

    assert status.retired is True
    assert status.stopped is False


def test_ignores_lines_without_boolean_status_updates():
    collection = DriverStatusCollection(meeting_key=1290, session_key=11300)
    message = Message(
        topic="TimingData",
        content={
            "Lines": {
                "not-a-driver": {"Retired": True, "Stopped": False},
                "1": {"Retired": "true", "Stopped": None},
                "2": None,
            }
        },
        timepoint=datetime(2026, 7, 12, 14, 32, 10, tzinfo=timezone.utc),
    )

    assert list(collection.process_message(message)) == []
