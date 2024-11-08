import json
from os.path import dirname
from pathlib import Path

import pytest
from bson import ObjectId

from openf1.util.db import (query_db, get_latest_session_info,
                            session_key_to_path, insert_data_async)

# Data is stored in tests/data/mongodb
DATA_DIR = Path(dirname(__file__)).parent.parent.joinpath("data", "mongodb")

def test_query_db(mock_mongodb):
    # import the expected data from the test data files
    with open(DATA_DIR.joinpath("sessions.json"), "r") as f:
        expected_result = json.load(f)
    # remove the _id field from all objects in the expected result
    expected_result = [{k: v for k, v in item.items() if k != "_id"} for item in
                                 expected_result]
    fetched = query_db("sessions", {})
    # strip the _id field from all objects in the result
    fetched = [{k: v for k, v in item.items() if k != "_id"} for item in
                                 fetched]
    assert fetched == expected_result

def test_get_latest_session_info(mock_mongodb):
    with open(DATA_DIR.joinpath("sessions.json"), "r") as f:
        expected_result = json.load(f)[-1]
    expected_result = {k: v for k, v in expected_result.items() if k != "_id"}
    fetched = get_latest_session_info()
    # strip the _id field from all objects in the result
    fetched = {k: v for k, v in fetched.items() if k != "_id"}
    assert fetched == expected_result

def test_session_key_to_path(mock_mongodb):
    assert session_key_to_path(9532) == "sessions/1"

@pytest.mark.asyncio
async def test_insert_data_async(mock_mongodb):
    await insert_data_async("sessions", [
        {"name": "test"}
    ])


