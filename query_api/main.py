from typing import List, Dict, Union
import importlib
from functools import lru_cache
import re
import csv
import requests
import io
import traceback
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import PlainTextResponse, HTMLResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from logger import logger
from filters import parse_query_filters


app = FastAPI()

# CORS middleware settings
# There are pretty much no security risks here as the app is only reading from a public database.
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],  # Allows all origins
    allow_credentials=True,
    allow_methods=['*'],  # Allows all methods
    allow_headers=['*'],  # Allows all headers
)


@lru_cache(maxsize=1)
def fetch_favicon():
    favicon_url = 'https://storage.googleapis.com/openf1-public/images/favicon.png'
    response = requests.get(favicon_url)
    if response.status_code == 200:
        return response.content
    else:
        return None


def _results_to_csv(results: List[Dict], method: type, filename: str) -> PlainTextResponse:
    """Converts results to CSV"""
    output = io.StringIO()
    csv_writer = csv.DictWriter(output, fieldnames=sorted(list(method.attributes)))
    csv_writer.writeheader()

    for row in results:
        csv_writer.writerow(row)
    csv_data = output.getvalue()

    headers = {
        'Content-Disposition': f'attachment; filename={filename}',
    }
    return PlainTextResponse(content=csv_data, media_type='text/csv', headers=headers)


def _get_favicon() -> Response:
    image_content = fetch_favicon()
    if image_content:
        return Response(content=image_content, media_type='image/png')
    else:
        raise HTTPException(status_code=404, detail='Favicon not found')


def _process_api_query(request: Request, path: str) -> Union[List, Response]:
    # Log request
    logger.info(f'Path: {path} | Headers: {dict(request.headers)} | Query Parameters: {dict(request.query_params)}')

    # Parse filters from URL
    filters = []
    for key in request.query_params.keys():
        for value in request.query_params.getlist(key):
            if value:
                filters.append(f'{key}={value}')
            else:
                filters.append(key)

            # Handle the '+' character used to set timezone
            if 'date' in filters[-1] and re.search(r' \d{2}:\d{2}$', filters[-1]):
                filters[-1] = '+'.join(filters[-1].rsplit(' ', 1))
    filters = parse_query_filters(filters=filters)

    # Determine output format - JSON (default) or CSV
    if 'csv' in filters:
        assert len(filters['csv']) == 1
        assert filters['csv'][0]['op'] == '=', f'Invalid query parameter `{filters["csv"][0]}`'
        use_csv = filters['csv'][0]['right']
        del filters['csv']
    else:
        use_csv = False

    # Import method
    path_components = path.split('/')
    assert len(path_components) == 2, f'Invalid method URL: `{path}`'
    method_name = path_components[1].lower()
    module_name = f'methods.{path_components[0]}.{method_name}'
    try:
        module = importlib.import_module(module_name)
        method = getattr(module, 'Method')
    except:
        raise ModuleNotFoundError(f'Method `{path}` does not exist')
    
    # Check filters
    for att in filters:
        if method.attributes and att not in method.attributes:
            raise ValueError(f'Unknow attribute `{att}`')

    # Process query
    results = list(method.query_process_filter(filters))

    # Return results
    if not use_csv:
        return results
    else:
        return _results_to_csv(
            results,
            method=method,
            filename=f'{method_name}.csv'
        )


@app.api_route("/{path:path}", methods=['GET', 'POST'])
async def catch_all(request: Request, path: str):
    try:
        if path == 'favicon.ico':
            return _get_favicon()
        else:
            return _process_api_query(request, path)

    except Exception as e:
        stack_trace = traceback.format_exc()
        error_msg = f'<h1>An error occurred</h1><pre>{stack_trace}</pre>'
        stack_trace = str(stack_trace).replace('\n', ' - ')
        logger.error(f'Path: {path} | Headers: {dict(request.headers)} | Query Parameters: {dict(request.query_params)}'
                     f' | Stack trace: {stack_trace}')
        return HTMLResponse(content=error_msg, status_code=500)
