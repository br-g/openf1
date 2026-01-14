from concurrent.futures import ProcessPoolExecutor

from typing import Callable, Iterable, Iterator, TypeVar

_S = TypeVar('S')
_T = TypeVar('T')


def map_parallel(fn: Callable[..., _T], *iterables: Iterable[_S], max_workers: int | None = None, chunksize: int = 1) -> Iterator[_T]:
    """
    Returns an iterator equivalent to map(fn, iterables), processed in parallel by max_workers workers in tasks of size chunksize.
    """
    with ProcessPoolExecutor(max_workers=max_workers) as exec:
        for result in exec.map(fn=fn, iterables=iterables, chunksize=chunksize):
            yield result