from asyncio import get_running_loop, iscoroutinefunction, new_event_loop, run
from collections import defaultdict
from functools import wraps
from typing import Callable

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
                        try:
                            get_running_loop()
                        except RuntimeError:
                            return run(func(*_args, **_kwargs))
                        else:
                            loop = new_event_loop()
                            try:
                                return loop.run_until_complete(func(*args, **_kwargs))
                            finally:
                                loop.close()

                    return func(*_args, **_kwargs)
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
