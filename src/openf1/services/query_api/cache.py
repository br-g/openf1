import threading

from cachetools import TTLCache

from openf1.services.query_api.query_params import QueryParam

_lock = threading.Lock()
_cache = TTLCache(maxsize=1024, ttl=3)  # cache live data for 3 seconds


def _request_to_string(path: str, query_params: dict[str, QueryParam]) -> str:
    params_str = [str(param) for param in query_params.values()]
    return f"{path},{','.join(sorted(params_str))}"


def save_to_cache(path: str, query_params: list[str], results: list[dict]):
    request_key = _request_to_string(path, query_params)

    with _lock:
        _cache[request_key] = results


def get_from_cache(path: str, query_params: dict[str, QueryParam]) -> list[dict] | None:
    request_key = _request_to_string(path, query_params)
    with _lock:
        results = _cache.get(request_key)
    return results
