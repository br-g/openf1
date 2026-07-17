import asyncio
import os
from datetime import timedelta
from functools import lru_cache
from pathlib import Path

import boto3
from loguru import logger


@lru_cache()
def _s3_client():
    """
    Client for any S3-compatible object storage.

    Configured entirely through environment variables so the same code runs
    against AWS S3, Scaleway, Backblaze B2, MinIO, Cloudflare R2, etc.

      S3_ENDPOINT_URL  Endpoint of the provider. Leave unset for AWS S3.
      S3_REGION        Region name (e.g. fr-par, us-east-1). Optional for some
                       providers; safe to set to match your bucket.
      S3_ACCESS_KEY    Access key id.
      S3_SECRET_KEY    Secret access key.
    """
    return boto3.client(
        "s3",
        endpoint_url=os.environ.get("S3_ENDPOINT_URL") or None,
        region_name=os.environ.get("S3_REGION") or None,
        aws_access_key_id=os.environ["S3_ACCESS_KEY"],
        aws_secret_access_key=os.environ["S3_SECRET_KEY"],
    )


def upload_to_object_storage(filepath: Path, bucket: str, destination_key: str):
    _s3_client().upload_file(str(filepath), bucket, destination_key)


async def upload_to_object_storage_periodically(
    filepath: Path,
    bucket: str,
    destination_key: Path,
    interval: timedelta,
):
    """Periodically uploads a file to S3-compatible object storage at specified intervals"""
    loop = asyncio.get_running_loop()

    while True:
        try:
            # Wait for the specified interval
            await asyncio.sleep(interval.total_seconds())

            # Upload in a separate thread to avoid blocking the event loop
            await loop.run_in_executor(
                None,
                upload_to_object_storage,
                filepath,
                bucket,
                str(destination_key),
            )
        except Exception:
            logger.exception(
                "An unexpected error occurred while uploading to object storage"
            )
