import asyncio
import re
import traceback

import aiohttp
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, Response
from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware

from openf1.services.query_api.csv import generate_csv_response
from openf1.services.query_api.query_params import (
    parse_query_params,
    query_params_to_mongo_filters,
)
from openf1.services.query_api.sort import sort_results
from openf1.services.query_api.tmp_fixes import apply_tmp_fixes
from openf1.util.db import get_documents
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


class TimeoutMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            return await asyncio.wait_for(call_next(request), timeout=20.0)
        except asyncio.TimeoutError:
            return JSONResponse(
                status_code=408,
                content={"detail": "Request timed out after 20 seconds"},
            )


app.add_middleware(TimeoutMiddleware)

_favicon = None


async def _get_favicon() -> Response:
    global _favicon

    if _favicon is not None:
        return Response(content=_favicon, media_type="image/png")

    favicon_url = "https://storage.googleapis.com/openf1-public/images/favicon.png"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(favicon_url) as resp:
                if resp.status == 200:
                    _favicon = await resp.read()
                    return Response(content=_favicon, media_type="image/png")
                raise HTTPException(status_code=404, detail="Favicon not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching favicon: {str(e)}")


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


async def _process_request(request: Request, path: str) -> list[dict] | Response:
    query_params = parse_query_params(request.query_params)
    collection = _parse_path(path)
    use_csv = "csv" in query_params and query_params.pop("csv")[0].value
    mongodb_filter = query_params_to_mongo_filters(query_params)
    results = await get_documents(collection_name=collection, filters=mongodb_filter)
    results = [
        {k: v for k, v in res.items() if not k.startswith("_")} for res in results
    ]
    results = deduplicate_dicts(results)
    results = apply_tmp_fixes(collection=collection, results=results)
    results = sort_results(results)

    return (
        generate_csv_response(results, filename=f"{collection}.csv")
        if use_csv
        else results
    )


@app.api_route("/{path:path}", methods=["GET", "POST"])
async def endpoint(request: Request, path: str):
    try:
        if path == "favicon.ico":
            return await _get_favicon()
        return await _process_request(request, path)
    except Exception as e:
        stack_trace = traceback.format_exc()
        error_msg = f"<h1>An error occurred</h1><pre>{stack_trace}</pre>"
        logger.error(
            f"Path: {path} | Headers: {dict(request.headers)}"
            f" | Query Parameters: {dict(request.query_params)}"
            f" | Exception: {e}"
        )
        return HTMLResponse(content=error_msg, status_code=500)
