import pytest
import time
from datetime import datetime, timedelta
from typing import Any, Callable
from pytz import timezone, utc

from openf1.util.misc import (join_url, timed_cache, json_serializer,
    deduplicate_dicts, SingletonMeta, to_datetime, to_timedelta,
    add_timezone_info)

def test_join_url():
    """Test join_url function."""
    url_base = "http://example.com"
    url_paths = [["path1"],
                 ["path1", "path2"],
                 ["path1", "path2", "path3"]]
    expected = ["http://example.com/path1",
                "http://example.com/path1/path2",
                "http://example.com/path1/path2/path3"]
    for url_path, exp in zip(url_paths, expected):
        assert join_url(url_base, *url_path) == exp

def test_timed_cache_decorator():
    """Test timed_cache decorator."""
    # Define a helper function to get the value of the test function and then
    # check if it was actually cached via time differences
    # NOTE: There is probaly a better way to test for this :)
    def time_function(func: Callable, expected_value: Any) -> float:
        start = time.time()
        assert func() == expected_value
        return time.time() - start
    # Test function with the decorator
    @timed_cache(1.0)
    def test_func():
        time.sleep(0.5) # needed for a measurable delay compared to the cache
        return 1
    # Get the first value (will not be cached)
    start = time.time()
    assert test_func() == 1
    expected_delay = time.time() - start - 0.01 # 0.01 is a fudge buffer
    # Get the second value (should be cached)
    delay = time_function(test_func, 1)
    assert delay < expected_delay
    # sleep to get rid of the cache
    time.sleep(1.1)
    # Get the third value (should not be cached)
    delay = time_function(test_func, 1)
    assert delay > expected_delay

def test_json_serializer():
    """Test json_serializer.

        We test a custom test class for this function. However, the integration
        tests under util/test_misc.py also test for custom class types used
        throughout the project."""
    class TestClass:
        def __init__(self, value):
            self.value = value
    tc = TestClass(1)
    assert json_serializer(tc) == {'value': 1}

def test_deduplicate_dicts():
    """Test deduplicate_dicts."""
    d1 = {"key1": "value1", "key2": "value2"}
    d2 = {"key2": "value2", "key3": "value3"}
    assert deduplicate_dicts([d1]) == [d1]
    assert deduplicate_dicts([d1, d2]) == [d1, d2]
    assert deduplicate_dicts([d1, d1, d2]) == [d1, d2]

def test_SingletonMeta():
    """Test SingletonMeta metaclass."""
    # Define a test class
    class TestClass(metaclass=SingletonMeta):
        def __init__(self, value):
            self.value = value
    # Test if the class is a singleton
    tc1 = TestClass(1)
    tc2 = TestClass(2)
    assert tc1 is tc2

def test_to_datetime():
    """Test to_datetime."""
    # Test with a string
    assert to_datetime("2020-01-01T00:00:00") == datetime(2020, 1, 1, 0, 0, 0)
    # Test with a datetime object
    assert to_datetime(datetime(2020, 1, 1, 0, 0, 0)) == datetime(2020, 1, 1, 0, 0, 0)
    # Test with an invalid object
    with pytest.raises(ValueError):
        to_datetime(1)

def test_to_timedelta():
    """Test to_timedelta."""
    # Test with a string
    assert to_timedelta("24.3564") == timedelta(seconds=24, microseconds=356400)
    assert to_timedelta("36:54") == timedelta(minutes=36, seconds=54)
    assert to_timedelta("8:45:46") == timedelta(hours=8, minutes=45, seconds=46)
    # Test with a timedelta object
    assert to_timedelta(timedelta(days=1)) == timedelta(days=1)
    # Test with an invalid object
    with pytest.raises(ValueError):
        to_timedelta(1)

def test_add_timezone_info():
    """Test add_timezone_info."""
    dt = datetime(2020, 3, 13, 0, 0, 0)
    # Test with UTC timezone
    assert add_timezone_info(dt, "00:00:00") == datetime(2020, 3, 13, 0, 0, 0,
                                                         tzinfo=utc)
    # Test with positive timezone
    assert add_timezone_info(dt, "+01:00:00") == datetime(2020, 3, 12, 23, 0, 0,
                                                          tzinfo=utc)
    # Test with negative timezone
    assert add_timezone_info(dt, "-05:00:00") == datetime(2020, 3, 13, 5, 0, 0,
                                                          tzinfo=utc)
    # Test with an invalid object
    with pytest.raises(ValueError):
        add_timezone_info(1, "00:00:00")


