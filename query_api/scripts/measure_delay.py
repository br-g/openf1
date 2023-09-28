"""Measure delay in real-time during a session."""

from datetime import datetime
import sys
sys.path.append('..')
from db import db


def measure():
    time_start = datetime.utcnow()
    docs = list(db['Position.z-Position-Entries'].find().sort('_time', -1).limit(1))
    assert docs
    time_end = datetime.utcnow()
    print(f'delay: {time_start - docs[0]["_time"]}')


while True:
    measure()
