from typing import Union, Optional, Dict, Iterator
import datetime
import json
import os
import pytz
from google.oauth2.service_account import Credentials
from google.cloud import storage
import fastf1

# Disable FastF1 caching
fastf1.Cache.set_disabled() 

storage_client = storage.Client(
    credentials=Credentials.from_service_account_info(json.loads(os.environ['GOOGLE_CREDENTIALS']))
)


def upload_blob(bucket_name: str, source_file_name: str, destination_blob_name: str):
    """Uploads a file to a GCS bucket."""
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)
    blob.upload_from_filename(source_file_name)


def to_datetime(x: Union[str, datetime.datetime]) -> Optional[datetime.datetime]:
    """This function is taken from FastF1: https://github.com/theOehrly/Fast-F1/blob/317bacf8c61038d7e8d0f48165330167702b349f/fastf1/utils.py#L178
    
    Fast datetime object creation from a date string.

    Permissible string formats:

        For example '2020-12-13T13:27:15.320000Z' with:

            - optional milliseconds and microseconds with
              arbitrary precision (1 to 6 digits)
            - with optional trailing letter 'Z'

        Examples of valid formats:

            - `2020-12-13T13:27:15.320000`
            - `2020-12-13T13:27:15.32Z`
            - `2020-12-13T13:27:15`

    Args:
        x: timestamp
    """
    if isinstance(x, str):
        try:
            date, time = x.strip('Z').split('T')
            year, month, day = date.split('-')
            hours, minutes, seconds = time.split(':')
            if '.' in seconds:
                seconds, msus = seconds.split('.')
                if len(msus) < 6:
                    msus = msus + '0' * (6 - len(msus))
                elif len(msus) > 6:
                    msus = msus[0:6]
            else:
                msus = 0

            return datetime.datetime(
                int(year), int(month), int(day), int(hours),
                int(minutes), int(seconds), int(msus)
            )

        except Exception as exc:
            #logger.debug(f"Failed to parse datetime string '{x}'")
            return None

    elif isinstance(x, datetime.datetime):
        return x

    else:
        return None


def to_timedelta(x: Union[str, datetime.timedelta]) -> Optional[datetime.timedelta]:
    """This function is taken from FastF1: https://github.com/theOehrly/Fast-F1/blob/317bacf8c61038d7e8d0f48165330167702b349f/fastf1/utils.py#L120
    
    Fast timedelta object creation from a time string

    Permissible string formats:

        For example: `13:24:46.320215` with:

            - optional hours and minutes
            - optional microseconds and milliseconds with
              arbitrary precision (1 to 6 digits)

        Examples of valid formats:

            - `24.3564` (seconds + milli/microseconds)
            - `36:54` (minutes + seconds)
            - `8:45:46` (hours, minutes, seconds)

    Args:
        x: timestamp
    """
    # this is faster than using pd.timedelta on a string
    if isinstance(x, str) and len(x):
        try:
            hours, minutes = 0, 0
            hms = x.split(':')
            if len(hms) == 3:
                hours, minutes, seconds = hms
            elif len(hms) == 2:
                minutes, seconds = hms
            else:
                seconds = hms[0]

            if '.' in seconds:
                seconds, msus = seconds.split('.')
                if len(msus) < 6:
                    msus = msus + '0' * (6 - len(msus))
                elif len(msus) > 6:
                    msus = msus[0:6]
            else:
                msus = 0

            return datetime.timedelta(
                hours=int(hours), minutes=int(minutes),
                seconds=int(seconds), microseconds=int(msus)
            )

        except Exception as exc:
            print(f"Failed to parse timedelta string '{x}'",
                          exc_info=exc)
            return None

    elif isinstance(x, datetime.timedelta):
        return x

    else:
        return None


def get_shedule(year: int) -> Iterator[Dict]:
    """Yields the schedule for the year (past and upcoming events), using FastF1"""
    for _, row in fastf1.get_event_schedule(year).iterrows():
        for i in range(1, 10):
            if f'Session{i}' not in row or row[f'Session{i}'] is None:
                continue

            yield {
                'RoundNumber': row['RoundNumber'],
                'Country': row['Country'],
                'Location': row['Location'],
                'OfficialEventName': row['OfficialEventName'],
                'Session': row[f'Session{i}'],
                'SessionDateUtc': row[f'Session{i}DateUtc'].to_pydatetime().replace(tzinfo=pytz.UTC),
            }
