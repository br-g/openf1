import requests

HEADERS = {
    "apiKey": "v1JVGPgXlahatAqwhakbrGtFdxW5rQBz",  # Is this key rotated sometime?
    "locale": "en",
}


def fetch_meetings(year: int | None) -> dict:
    """If year param is not provided, returns list of meeting for the latest available season."""
    url = "http://api.formula1.com/v1/editorial-eventlisting/events"

    params = {"season": year} if year else {}

    response = requests.get(url, params=params, headers=HEADERS)

    if response.status_code == 200:
        data = response.json()
        return data
    else:
        print(f"Error: {response.status_code}")
        print(response.text)


def _fetch_meeting_details(meeting_key: int) -> dict:
    url = f"https://api.formula1.com/v1/event-tracker/meeting/{meeting_key}"

    try:
        response = requests.get(url, headers=HEADERS)

        if response.status_code == 200:
            data = response.json()
            timetables = data.get("meetingContext", {}).get("timetables", [])
            return data
        else:
            print(f"Error {response.status_code}: {response.text}")

    except Exception as e:
        print(f"Connection Error: {e}")


def fetch_sessions(year: int | None) -> dict:
    """If year param is not provided, returns list of sessions for the latest available season."""
    meetings = fetch_meetings(year)
