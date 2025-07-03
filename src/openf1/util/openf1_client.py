# main.py
#
# Description:
# A Python client for the OpenF1 REST API, using functions and global variables.
#
# This script manages OAuth2 authentication by automatically fetching and
# refreshing access tokens. Initialization is handled lazily on the first
# API request, using environment variables.
#
# Installation:
# Before using this client, you need to install the 'requests' library:
# pip install requests

import os
import time
from urllib.parse import urljoin

import requests

# --- Global variables for API configuration and state ---
BASE_URL = "https://api.openf1.org/"
CLIENT_ID = None
CLIENT_SECRET = None
ACCESS_TOKEN = None
TOKEN_EXPIRY_TIME = 0  # Unix timestamp when the token expires


def _ensure_initialized():
    """
    Ensures the client is initialized by loading credentials from environment
    variables if they haven't been loaded yet. This is called automatically
    on the first API request.
    """
    global CLIENT_ID, CLIENT_SECRET
    # This check ensures we only try to load from env vars once per run.
    if CLIENT_ID is None:
        print(
            "Client not initialized. Attempting to load credentials from environment variables..."
        )
        loaded_id = os.environ.get("OPENF1_CLIENT_ID")
        loaded_secret = os.environ.get("OPENF1_CLIENT_SECRET")

        if not loaded_id or not loaded_secret:
            # Set to empty strings to prevent re-checking on subsequent calls,
            # then fail loudly.
            CLIENT_ID = ""
            CLIENT_SECRET = ""
            raise ValueError(
                "Client credentials could not be found. Please ensure "
                "OPENF1_CLIENT_ID and OPENF1_CLIENT_SECRET environment "
                "variables are set."
            )
        CLIENT_ID = loaded_id
        CLIENT_SECRET = loaded_secret
        print("Credentials loaded successfully.")


def _authenticate():
    """
    Fetches an OAuth2 access token from the API.

    This function sends the client_id and client_secret to the token
    endpoint and stores the received access token and its expiry time in global variables.
    It is called automatically when a token is needed or has expired.

    Raises:
        requests.exceptions.HTTPError: If the token request fails.
    """
    global ACCESS_TOKEN, TOKEN_EXPIRY_TIME

    token_url = urljoin(BASE_URL, "token")
    payload = {
        "username": CLIENT_ID,
        "password": CLIENT_SECRET,
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    try:
        print("Authenticating and fetching a new access token...")
        response = requests.post(token_url, data=payload, headers=headers)
        response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)

        token_data = response.json()
        ACCESS_TOKEN = token_data["access_token"]
        # Set expiry time with a 60-second buffer to be safe
        TOKEN_EXPIRY_TIME = time.time() + int(token_data["expires_in"]) - 60
        print("Successfully obtained new access token.")

    except requests.exceptions.RequestException as e:
        print(f"Error obtaining access token: {e}")
        # In case of an error, response might not be set or might not have text
        if "response" in locals() and hasattr(response, "text"):
            print(f"Response body: {response.text}")
        raise


def _get_valid_token():
    """
    Returns a valid access token, ensuring the client is initialized and
    refreshing the token if necessary.
    """
    _ensure_initialized()
    # Check if token is None or if the current time is past the expiry time
    if not ACCESS_TOKEN or time.time() >= TOKEN_EXPIRY_TIME:
        _authenticate()
    return ACCESS_TOKEN


def get(endpoint, params=None):
    """
    Makes an authenticated GET request to a specified API endpoint.

    This is a generic function to access any GET endpoint on the API.

    Args:
        endpoint (str): The API endpoint path (e.g., 'v1/sessions').
        params (dict, optional): A dictionary of query parameters. Defaults to None.

    Returns:
        dict or list: The JSON response from the API.

    Raises:
        requests.exceptions.HTTPError: If the API request fails.
    """
    access_token = _get_valid_token()
    full_url = urljoin(BASE_URL, endpoint)
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json",
    }

    try:
        response = requests.get(full_url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error making API request to {full_url}: {e}")
        if hasattr(e.response, "text"):
            print(f"Response body: {e.response.text}")
        raise
