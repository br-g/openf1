import asyncio
import re
import traceback

import aiohttp
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, Response
from loguru import logger
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.middleware.base import BaseHTTPMiddleware

from openf1.services.query_api.cache import get_from_cache, save_to_cache
from openf1.services.query_api.csv import generate_csv_response
from openf1.services.query_api.query_params import (
    parse_query_params,
    query_params_to_mongo_filters,
)
from openf1.util.db import get_documents

rate_limiter = Limiter(key_func=get_remote_address)
app = FastAPI()

app.state.limiter = rate_limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

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
    if not path and not request.query_params:
        return Response(content="Welcome to OpenF1!", media_type="text/plain")

    query_params = parse_query_params(request.query_params)
    collection = _parse_path(path)
    use_csv = "csv" in query_params and query_params.pop("csv")[0].value

    results = get_from_cache(path=path, query_params=query_params)

    if results is None:
        mongodb_filter = query_params_to_mongo_filters(query_params)
        results = await get_documents(
            collection_name=collection, filters=mongodb_filter
        )
        save_to_cache(path=path, query_params=query_params, results=results)

    return (
        generate_csv_response(results, filename=f"{collection}.csv")
        if use_csv
        else results
    )


@app.api_route("/{path:path}", methods=["GET", "POST"])
@rate_limiter.limit("30/10seconds")  # 30 requests every 10 seconds per IP
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
