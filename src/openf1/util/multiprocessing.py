from concurrent.futures import ProcessPoolExecutor

from typing import Callable, Iterable, Iterator, TypeVar

_S = TypeVar('S')
_T = TypeVar('T')


def map_parallel(fn: Callable[..., _T], *iterables: Iterable[_S], max_workers: int | None = None, batch_size: int | None = None) -> Iterator[_T]:
    """
    Returns an iterator equivalent to map(fn, iterables), processed in parallel by max_workers workers in tasks of size batch_size.
    max_workers defaults to the number of CPU cores on the machine, and batch_size defaults to 1.
    """
    chunksize = batch_size if batch_size is not None else 1
    with ProcessPoolExecutor(max_workers=max_workers) as exec:
        for result in exec.map(fn, *iterables, chunksize=chunksize):
            yield result