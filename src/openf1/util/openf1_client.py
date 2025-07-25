"""A Python client for the OpenF1 REST API"""

import os
import time
from urllib.parse import urljoin

import requests

BASE_URL = "https://api.openf1.org/"
client_id = None
client_secret = None
access_token = None
token_expiry_time = 0  # Unix timestamp when the token expires
_authentication_enabled = (
    False  # Default to false, will be set true if credentials found
)
_initialized = False


def _ensure_initialized():
    """
    Ensures the client is initialized by loading credentials from environment
    variables if they exist. Sets _authentication_enabled accordingly.
    This runs only once when an API request is first made.
    """
    global client_id, client_secret, _authentication_enabled, _initialized

    if _initialized:
        return

    loaded_id = os.environ.get("OPENF1_CLIENT_ID")
    loaded_secret = os.environ.get("OPENF1_CLIENT_SECRET")

    if loaded_id and loaded_secret:
        client_id = loaded_id
        client_secret = loaded_secret
        _authentication_enabled = True
    else:
        _authentication_enabled = False

    _initialized = True


def _authenticate():
    """Fetches an OAuth2 access token from the API"""
    global access_token, token_expiry_time

    if not _authentication_enabled:
        raise RuntimeError("Authentication is not enabled. Cannot fetch token.")

    token_url = urljoin(BASE_URL, "token")
    payload = {
        "username": client_id,
        "password": client_secret,
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    response = requests.post(token_url, data=payload, headers=headers)
    response.raise_for_status()

    token_data = response.json()
    access_token = token_data["access_token"]
    token_expiry_time = time.time() + int(token_data["expires_in"]) - 60


def _get_valid_token():
    """
    Returns a valid access token, refreshing the token if necessary.
    Only attempts to get a token if authentication is enabled.
    """
    _ensure_initialized()

    if not _authentication_enabled:
        return None

    if not access_token or time.time() >= token_expiry_time:
        _authenticate()
    return access_token


def get(endpoint, params=None):
    """
    Makes a GET request to a specified API endpoint.
    Includes an authorization header only if authentication is automatically enabled
    by the presence of environment variables.
    """
    _ensure_initialized()

    full_url = urljoin(BASE_URL, endpoint)
    headers = {
        "Accept": "application/json",
    }

    if _authentication_enabled:
        token = _get_valid_token()
        if token:
            headers["Authorization"] = f"Bearer {token}"

    response = requests.get(full_url, headers=headers, params=params)
    response.raise_for_status()
    return response.json()
