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
from openf1.util.db import query_db
from openf1.util.misc import deduplicate_dicts

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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


async def _get_favicon() -> Response:
    favicon_url = "https://storage.googleapis.com/openf1-public/images/favicon.png"
    async with aiohttp.ClientSession() as session:
        async with session.get(favicon_url) as resp:
            if resp.status == 200:
                return Response(content=await resp.read(), media_type="image/png")
            raise HTTPException(status_code=404, detail="Favicon not found")


def _parse_path(path: str) -> str:
    match = re.match(r"^v1/(\w+)$", path.lower())
    if match:
        return match.group(1)
    raise ValueError("Invalid route")


def _deduplicate_meetings(results: list[dict]) -> list[dict]:
    deduplicated = []
    meeting_keys_seen = set()
    for res in results:
        if res["meeting_key"] in meeting_keys_seen:
            continue
        deduplicated.append(res)
        meeting_keys_seen.add(res["meeting_key"])
    return deduplicated


async def _process_request(request: Request, path: str) -> list[dict] | Response:
    query_params = parse_query_params(request.query_params)
    collection = _parse_path(path)
    use_csv = "csv" in query_params and query_params.pop("csv")[0].value
    mongodb_filter = query_params_to_mongo_filters(query_params)
    results = await query_db(collection_name=collection, filters=mongodb_filter)
    results = [
        {k: v for k, v in res.items() if not k.startswith("_")} for res in results
    ]
    results = deduplicate_dicts(results)
    results = apply_tmp_fixes(collection=collection, results=results)
    results = sort_results(results)
    if collection == "meetings":
        results = _deduplicate_meetings(results)

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
        logger.error(f"Path: {path} | Exception: {e}")
        return HTMLResponse(
            content=f"<h1>Error</h1><pre>{traceback.format_exc()}</pre>",
            status_code=500,
        )
