import asyncio

from loguru import logger


async def record_to_file(filepath: str, topics: list[str], timeout: int):
    """Records raw F1 data to a file, using a slightly modified version of the FastF1
    live timing module (https://github.com/br-g/fastf1-livetiming)q
    """
    while True:
        try:
            logger.info(f"Starting recorder subprocess for file '{filepath}'")
            command = (
                ["python", "-m", "fastf1_livetiming", "save", filepath]
                + sorted(list(topics))
                + ["--timeout", str(timeout)]
            )
            proc = await asyncio.create_subprocess_exec(
                *command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await proc.communicate()

            # Check if the process exited cleanly with an exit code of 0.
            if proc.returncode == 0:
                logger.info(f"Stdout: {stdout.decode().strip()}")
                break
            else:
                logger.error(
                    f"Recorder subprocess failed with exit code {proc.returncode}."
                )
                logger.error(f"Stderr: {stderr.decode().strip()}")
        except Exception:
            logger.exception(
                "An unexpected exception occurred while trying to run "
                "the recorder subprocess."
            )

        logger.info("Waiting 15 seconds before restarting the recorder...")
        await asyncio.sleep(15)
