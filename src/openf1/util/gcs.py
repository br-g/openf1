import asyncio
import json
import os
from datetime import timedelta
from functools import lru_cache
from pathlib import Path

from google.auth import default
from google.cloud import storage
from google.oauth2.service_account import Credentials


@lru_cache()
def _storage_client() -> storage.Client:
    credentials, project_id = default()
    client = storage.Client(credentials=credentials, project=project_id)

    # creds_filepath = os.environ["GOOGLE_APPLICATION_CREDENTIALS"]
    # with open(creds_filepath, "r") as file:
    #    creds = json.load(file)
    # client = storage.Client(credentials=Credentials.from_service_account_info(creds))
    return client


def upload_to_gcs(filepath: Path, bucket: str, destination_key: str):
    bucket = _storage_client().bucket(bucket)
    blob = bucket.blob(destination_key)
    blob.upload_from_filename(filepath)


async def upload_to_gcs_periodically(
    filepath: Path, bucket: str, destination_key: Path, interval: timedelta
):
    """Periodically uploads a file to Google Cloud Storage (GCS) at specified intervals"""
    loop = asyncio.get_running_loop()

    while True:
        # Wait for the specified interval
        await asyncio.sleep(interval.total_seconds())

        # Upload the file to GCS using a separate thread to avoid blocking the event loop
        await loop.run_in_executor(
            None,
            upload_to_gcs,
            filepath,
            bucket,
            str(destination_key),
        )
