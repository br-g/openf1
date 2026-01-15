from asyncio import get_running_loop, iscoroutinefunction, run
from functools import wraps
from typing import Callable

import typer

class Typer(typer.Typer):
    """
    Wrapper class for typer.Typer to allow for decorating async functions.
    Adapted from https://github.com/byunjuneseok/async-typer.
    """

    def command(self, *args, **kwargs):
        def decorator(func: Callable):
            @wraps(func)
            def _func(*_args, **_kwargs):
                if iscoroutinefunction(func):
                    # Use current event loop if already running
                    loop = None
                    try:
                        loop = get_running_loop()
                    except RuntimeError:
                        pass

                    if loop is not None:
                        return loop.run_until_complete(func(*_args, **_kwargs))
                    else:
                        return run(func(*_args, **_kwargs))

                return func(*_args, **_kwargs)

            super(Typer, self).command(*args, **kwargs)(_func)

            return func

        return decorator
