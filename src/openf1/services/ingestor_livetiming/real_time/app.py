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
F1_TOKEN = os.getenv("F1_TOKEN")


async def main():
    with tempfile.TemporaryDirectory() as temp_dir:
        # Record raw data and save it to file
        topics = get_topics()
        logger.info(f"Starting live recording of the following topics: {topics}")

        tasks = []

        temp_file_signalr = os.path.join(temp_dir, "signalr.txt")
        logger.info(f"Recording raw signalr data to '{temp_file_signalr}'")
        task_recording_signalr = asyncio.create_task(
            record_to_file(filepath=temp_file_signalr, topics=topics, timeout=TIMEOUT)
        )
        tasks.append(task_recording_signalr)

        if F1_TOKEN:
            temp_file_signalrcore = os.path.join(temp_dir, "signalrcore.txt")
            logger.info(f"Recording raw signalrcore data to '{temp_file_signalrcore}'")
            task_recording_signalrcore = asyncio.create_task(
                record_to_file(
                    filepath=temp_file_signalrcore, topics=topics, timeout=TIMEOUT
                )
            )
            tasks.append(task_recording_signalrcore)

        # Save received raw data to GCS, for debugging
        if GCS_BUCKET:
            logger.info("Starting periodic GCS upload of raw data")
            gcs_filekey = datetime.now(timezone.utc).strftime(
                "%Y/%m/%d/signalr/%H:%M:%S.txt"
            )
            task_upload_raw_signalr = asyncio.create_task(
                upload_to_gcs_periodically(
                    filepath=temp_file_signalr,
                    bucket=GCS_BUCKET,
                    destination_key=gcs_filekey,
                    interval=timedelta(seconds=60),
                )
            )
            tasks.append(task_upload_raw_signalr)

            if F1_TOKEN:
                gcs_filekey = datetime.now(timezone.utc).strftime(
                    "%Y/%m/%d/signalrcore/%H:%M:%S.txt"
                )
                task_upload_raw_signalrcore = asyncio.create_task(
                    upload_to_gcs_periodically(
                        filepath=temp_file_signalrcore,
                        bucket=GCS_BUCKET,
                        destination_key=gcs_filekey,
                        interval=timedelta(seconds=60),
                        offset=timedelta(
                            seconds=30
                        ),  # ensure both file uploads don't occur simultaneously
                    )
                )
                tasks.append(task_upload_raw_signalrcore)

        # Ingest received data
        logger.info("Starting data ingestion")
        task_ingest_signalr = asyncio.create_task(ingest_file(temp_file_signalr))
        tasks.append(task_ingest_signalr)
        if F1_TOKEN:
            task_ingest_signalrcore = asyncio.create_task(
                ingest_file(temp_file_signalrcore)
            )
            tasks.append(task_ingest_signalrcore)

        # Wait for the recording task to stop
        await asyncio.wait(
            [task_recording_signalr], return_when=asyncio.FIRST_COMPLETED
        )
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
