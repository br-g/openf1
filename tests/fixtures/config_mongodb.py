import json
from os import listdir
from os.path import join, dirname, abspath

import mongomock
import pytest

from pymongo import MongoClient
from motor.motor_asyncio import AsyncIOMotorClient

@pytest.fixture
def mock_mongodb(mocker):
    """Create a mock MongoDB database with sample data
    Data is based on the json file in tests/fixtures/data.json."""
    mock_client = mongomock.MongoClient()
    mocker.patch('pymongo.MongoClient', return_value=mock_client)

    # insert sample data into mocked database
    db = mock_client['openf1-livetiming']
    # load sample data from json files in the tests/fixtures/data/mongodb
    # directory
    files = listdir(join(dirname(abspath(__file__)), '../data/mongodb'))
    for file in files:
        with open(join(dirname(abspath(__file__)), '../data/mongodb', file)) as f:
            data = json.load(f)
            collection = db[file.split('.')[0]]
            collection.insert_many(data)

    return mock_client


