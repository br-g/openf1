import asyncio

from loguru import logger


async def record_to_file(
    filepath: str, topics: list[str], timeout: int, is_authenticated: bool
):
    """Records raw F1 data to a file, using a slightly modified version of the FastF1
    live timing module (https://github.com/br-g/fastf1-livetiming)
    """
    while True:
        try:
            command = (
                ["python", "-m", "fastf1_livetiming", "save", filepath]
                + sorted(list(topics))
                + (["--auth"] if is_authenticated else [])
                + ["--timeout", str(timeout)]
            )
            proc = await asyncio.create_subprocess_exec(*command)

            # Wait for the process to complete
            await proc.wait()

            # Check if the process exited cleanly with an exit code of 0.
            if proc.returncode == 0:
                logger.info("Recorder subprocess completed successfully.")
                break
            else:
                logger.error(
                    f"Recorder subprocess failed with exit code {proc.returncode}."
                )
        except Exception:
            logger.exception(
                "An unexpected exception occurred while trying to run "
                "the recorder subprocess."
            )

        logger.info("Waiting 15 seconds before restarting the recorder...")
        await asyncio.sleep(15)
