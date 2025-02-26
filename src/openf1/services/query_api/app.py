import re
import traceback
from functools import lru_cache

import requests
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, Response
from loguru import logger

from openf1.services.query_api.csv import generate_csv_response
from openf1.services.query_api.query_params import (
    QueryParam,
    parse_query_params,
    query_params_to_mongo_filters,
)
from openf1.services.query_api.sort import sort_results
from openf1.services.query_api.tmp_fixes import apply_tmp_fixes
from openf1.util.db import query_db
from openf1.util.misc import deduplicate_dicts

app = FastAPI()

# CORS middleware settings
# There are pretty much no security risks here as the app read-only.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)


@lru_cache()
def _get_favicon() -> Response:
    favicon_url = "https://storage.googleapis.com/openf1-public/images/favicon.png"
    response = requests.get(favicon_url)
    if response.status_code == 200:
        return Response(content=response.content, media_type="image/png")
    else:
        raise HTTPException(status_code=404, detail="Favicon not found")


def _parse_path(path: str) -> str:
    """
    Extracts the MongoDB collection name from an API path.
    The path is expected to be in the format "v1/{collection}".
    """
    path = path.lower()

    pattern = r"^v1/(\w+)$"
    match = re.match(pattern, path)

    if match:
        collection = match.group(1)
        return collection
    else:
        raise ValueError("Invalid route")


def _deduplicate_meetings(results: list[dict]) -> list[dict]:
    """Keeps only the first occurrence of each meeting"""
    deduplicated = []
    meeting_keys_seen = set()

    for res in results:
        if res["meeting_key"] in meeting_keys_seen:
            continue
        deduplicated.append(res)
        meeting_keys_seen.add(res["meeting_key"])

    return deduplicated


def _postprocess_results(collection: str, results: list[str]) -> list[str]:
    results = [
        {k: v for k, v in res.items() if not k.startswith("_")} for res in results
    ]
    results = deduplicate_dicts(results)
    results = apply_tmp_fixes(collection=collection, results=results)
    results = sort_results(results)
    if collection == "meetings":
        results = _deduplicate_meetings(results)
    return results


def _is_output_format_csv(query_params: dict[str, QueryParam]) -> bool:
    if "csv" in query_params:
        if query_params["csv"][0].op != "=":
            raise ValueError(f'Invalid query parameter `{query_params["csv"][0]}`')

        is_csv = query_params["csv"][0].value
        if not isinstance(is_csv, bool):
            raise ValueError(
                f"Invalid value for parameter `csv` (`{is_csv}`). Expected `true` or `false`."
            )

        return is_csv
    else:
        return False


def _process_request(request: Request, path: str) -> list[dict] | Response:
    query_params = parse_query_params(request.query_params)
    collection = _parse_path(path)

    use_csv = _is_output_format_csv(query_params)
    if "csv" in query_params:
        del query_params["csv"]

    mongodb_filter = query_params_to_mongo_filters(query_params)
    results = query_db(collection_name=collection, filters=mongodb_filter)
    results = _postprocess_results(collection, results)

    if use_csv:
        return generate_csv_response(results, filename=f"{collection}.csv")
    else:
        return results


@app.api_route("/{path:path}", methods=["GET", "POST"])
async def endpoint(request: Request, path: str):
    try:
        if path == "favicon.ico":
            return _get_favicon()
        else:
            return _process_request(request, path)

    except Exception as e:
        stack_trace = traceback.format_exc()
        error_msg = f"<h1>An error occurred</h1><pre>{stack_trace}</pre>"
        logger.error(
            f"Path: {path} | Headers: {dict(request.headers)}"
            f" | Query Parameters: {dict(request.query_params)}"
            f" | Exception: {e}"
        )
        return HTMLResponse(content=error_msg, status_code=500)
