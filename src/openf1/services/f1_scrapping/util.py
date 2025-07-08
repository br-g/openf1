from pathlib import Path

import requests


def download_page(url: str, output_file: Path) -> bool:
    """Downloads the HTML content of a URL and saves it to a file"""
    try:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            )
        }
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()

        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(response.text)

        return True

    except requests.exceptions.HTTPError as http_err:
        print(
            f"HTTP error occurred: {http_err} "
            f"- Status code: {http_err.response.status_code}"
        )
    except requests.exceptions.ConnectionError as conn_err:
        print(f"Connection error occurred: {conn_err}")
    except requests.exceptions.Timeout as timeout_err:
        print(f"Timeout error occurred: {timeout_err}")
    except requests.exceptions.RequestException as req_err:
        print(f"An unexpected error occurred with the request: {req_err}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

    return False
