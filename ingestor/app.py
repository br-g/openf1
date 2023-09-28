import os
from datetime import datetime, timedelta
import tempfile
import threading
import traceback
import pytz
import asyncio
from flask import Flask
from util import upload_blob, get_shedule
from logger import logger
from ingest_real_time import tail_and_ingest

FILEKEY_RAW = '%Y/%m/%d/%H:%M:%S.txt'
RAW_UPLOAD_FREQUENCY = 60  # in seconds
RECORDING_DURATION = 13 * 60  # in seconds


async def upload_raw_recordings(filepath: str, filekey_raw: str):
    """Uploads raw data to a GCS bucket, at regular intervals, as a backup"""
    while True:
        await asyncio.sleep(RAW_UPLOAD_FREQUENCY)

        loop = asyncio.get_running_loop()
        await loop.run_in_executor(
            None,
            upload_blob,
            os.environ.get('BUCKET_API_RAW'),
            filepath,
            filekey_raw,
        )


def is_session_possibly_in_progress(offset_before=timedelta(hours=2), offset_after=timedelta(hours=5)) -> bool:
    """Returns whether it is worth listening to data coming from the F1 server.
       Recording starts long before the session starts and ends long after, just in case...
    """
    time_ = datetime.now().astimezone(pytz.timezone('UTC'))

    for session in get_shedule(time_.year):
        if session['SessionDateUtc'] - offset_before <= time_ <= session['SessionDateUtc'] + offset_after:
            return True
    
    return False


async def record(filepath: str):
    """Records raw F1 data to a file, using the FastF1 live timing module
       (https://github.com/theOehrly/Fast-F1/tree/master/fastf1/livetiming)
    """
    start_time = datetime.now(pytz.utc)

    command = ['python', '-m', 'fastf1.livetiming', 'save', filepath, '--timeout', str(RECORDING_DURATION)]
    logger.info(f'Starting recording live data (command: `{" ".join(command)}`)')
    process_fastf1 = await asyncio.create_subprocess_exec(
        *command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )

    # Wait for the planned recording duration
    while datetime.now(pytz.utc) < start_time + timedelta(seconds=RECORDING_DURATION):
        await asyncio.sleep(5)
    
    logger.info(f'Timing out after {round(RECORDING_DURATION/60,2)} minutes.')

    # Stop recording
    process_fastf1.terminate()
    try:
        await asyncio.wait_for(process_fastf1.wait(), timeout=10)
    except asyncio.TimeoutError:
        logger.warning('Process did not terminate in time. Killing.')
        process_fastf1.kill()
    
    logger.info('Recording stopped.')


def _handle_exception(task: asyncio.Task):
    """Logs exceptions that occur in asynchronous jobs"""
    exception = task.exception()
    if exception is not None:
        # Skip exception that is raised at the end of the task
        if isinstance(exception, asyncio.exceptions.CancelledError):
            return
        tb_str = ''.join(traceback.format_exception(etype=type(exception), value=exception, tb=exception.__traceback__))
        logger.error(tb_str)


async def run():
    """Records session if one could be in progress"""
    if not is_session_possibly_in_progress():
        logger.info('No session in progress according to schedule. Skipping.')
        return

    filekey_raw = datetime.utcnow().strftime(FILEKEY_RAW)
    
    logger.info('A session could be in progress according to schedule. Recording.')
    with tempfile.NamedTemporaryFile(mode='w', delete=True) as temp:
        task1 = asyncio.create_task(upload_raw_recordings(temp.name, filekey_raw))
        task1.add_done_callback(_handle_exception)
        task2 = asyncio.create_task(tail_and_ingest(temp.name))
        task2.add_done_callback(_handle_exception)
        await record(temp.name)


def _start_async_loop():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(run())


app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def main():
    logger.info('Ingestor started')
    t = threading.Thread(target=_start_async_loop)
    t.start()
    t.join()
    return 'Completed', 200


if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=8080)
