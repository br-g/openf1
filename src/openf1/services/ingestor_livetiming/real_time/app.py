import asyncio
import os
import tempfile
from datetime import datetime, timedelta, timezone

from loguru import logger

from openf1.services.ingestor_livetiming.core.objects import get_topics
from openf1.services.ingestor_livetiming.real_time.processing import ingest_file
from openf1.services.ingestor_livetiming.real_time.recording import record_to_file
from openf1.util.gcs import upload_to_gcs_periodically

TIMEOUT = 10800  # Terminate job if no data received for 3 hours (in seconds)
GCS_BUCKET = os.getenv("OPENF1_INGESTOR_LIVETIMING_GCS_BUCKET_RAW")


async def main():
    with tempfile.NamedTemporaryFile(mode="w", delete=True) as temp:
        logger.info(f"Recording raw data to '{temp.name}'")
        tasks = []

        # Record raw data and save it to file
        topics = get_topics()
        logger.info(f"Starting live recording of the following topics: {topics}")
        task_recording = asyncio.create_task(
            record_to_file(
                filepath=temp.name,
                topics=topics,
                timeout=TIMEOUT,
            )
        )
        tasks.append(task_recording)

        if GCS_BUCKET:
            # Save received raw data to GCS, for debugging
            logger.info("Starting periodic GCS upload of raw data")
            gcs_filekey = datetime.now(timezone.utc).strftime("%Y/%m/%d/%H:%M:%S.txt")
            task_upload_raw = asyncio.create_task(
                upload_to_gcs_periodically(
                    filepath=temp.name,
                    bucket=GCS_BUCKET,
                    destination_key=gcs_filekey,
                    interval=timedelta(seconds=60),
                )
            )
            tasks.append(task_upload_raw)

        # Ingest received data
        logger.info("Starting data ingestion")
        task_ingest = asyncio.create_task(ingest_file(temp.name))
        tasks.append(task_ingest)

        # Wait for the recording task to stop
        await asyncio.wait([task_recording], return_when=asyncio.FIRST_COMPLETED)
        logger.info("Recording stopped")

        # Cancel all the tasks
        logger.info("Stopping tasks")
        for task in tasks:
            task.cancel()

        # Wait for all tasks to complete
        await asyncio.gather(*tasks, return_exceptions=True)

        logger.info("Job completed")


if __name__ == "__main__":
    asyncio.run(main())
