import asyncio

from loguru import logger


async def record_to_file(filepath: str, topics: list[str], timeout: int):
    """Records raw F1 data to a file, using a slightly modified version of the FastF1
    live timing module (https://github.com/br-g/fastf1-livetiming)
    """
    command = (
        ["python", "-m", "fastf1_livetiming", "save", filepath]
        + sorted(list(topics))
        + ["--timeout", str(timeout)]
    )
    proc = await asyncio.create_subprocess_exec(
        *command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )

    stdout, stderr = await proc.communicate()

    logger.info(stdout.decode())
    logger.error(stderr.decode())
