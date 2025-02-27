import multiprocessing
import os

from loguru import logger

if __name__ == "__main__":
    cpu_count = multiprocessing.cpu_count() or 1
    workers = cpu_count
    threads = cpu_count * 2
    backlog = 4096
    logger.info(f"Starting Gunicorn with {workers} workers, {threads} threads")
    os.system(
        f"gunicorn -w {workers} --threads {threads} "
        f"-k uvicorn.workers.UvicornWorker --timeout 20 "
        f"--keep-alive 5 --backlog {backlog} --preload "
        f"--max-requests 1000 --max-requests-jitter 100 "
        f"--bind 0.0.0.0:8000 "
        f"openf1.services.query_api.app:app"
    )
