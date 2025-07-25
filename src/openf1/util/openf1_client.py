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


def _ensure_initialized():
    """
    Ensures the client is initialized by loading credentials from environment
    variables if they haven't been loaded yet. This is called automatically
    on the first API request.
    """
    global client_id, client_secret
    if client_id is None:
        loaded_id = os.environ.get("OPENF1_CLIENT_ID")
        loaded_secret = os.environ.get("OPENF1_CLIENT_SECRET")

        if not loaded_id or not loaded_secret:
            client_id = ""
            client_secret = ""
            raise ValueError(
                "Client credentials could not be found. Please ensure "
                "OPENF1_CLIENT_ID and OPENF1_CLIENT_SECRET environment "
                "variables are set."
            )
        client_id = loaded_id
        client_secret = loaded_secret


def _authenticate():
    """Fetches an OAuth2 access token from the API"""
    global access_token, token_expiry_time

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
    Returns a valid access token, ensuring the client is initialized and
    refreshing the token if necessary.
    """
    _ensure_initialized()
    if not access_token or time.time() >= token_expiry_time:
        _authenticate()
    return access_token


def get(endpoint, params=None):
    """Makes an authenticated GET request to a specified API endpoint"""
    access_token = _get_valid_token()
    full_url = urljoin(BASE_URL, endpoint)
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json",
    }
    response = requests.get(full_url, headers=headers, params=params)
    response.raise_for_status()
    return response.json()
