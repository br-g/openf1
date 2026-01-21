from asyncio import iscoroutinefunction, run
from collections import defaultdict
from functools import wraps
import traceback
from typing import Callable, TypeVar

import typer

ON_START = "on_start"
ON_EXIT = "on_exit"


class Typer(typer.Typer):
    """
    Wrapper class for typer.Typer to allow for decorating async functions.
    Adapted from https://github.com/byunjuneseok/async-typer.
    """

    event_handlers: defaultdict[str, list[Callable]] = defaultdict(list)


    def command(self, *args, **kwargs):
        def decorator(func: Callable):
            @wraps(func)
            def _func(*_args, **_kwargs):
                self.run_event_handlers(ON_START)
                try:
                    if iscoroutinefunction(func):
                        return run(func(*_args, **_kwargs))
                    return func(*_args, **_kwargs)
                except Exception:
                    pass
                finally:
                    self.run_event_handlers(ON_EXIT)

            super(Typer, self).command(*args, **kwargs)(_func)

            return func

        return decorator


    def add_event_handler(self, event_type: str, func: Callable) -> None:
        self.event_handlers[event_type].append(func)


    def run_event_handlers(self, event_type: str):
        for event in self.event_handlers[event_type]:
            if iscoroutinefunction(event):
                run(event())
            else:
                event()
