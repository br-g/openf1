# Import libraries
import argparse
from datetime import date
import requests
import time
from collections import namedtuple, defaultdict
from tabulate import tabulate


def get_session_keys(year: int):
    """
    Obtain the session keys for each race and sprint session
    """

    # Obtain the sprint races from the current year
    url_sprint = "https://api.openf1.org/v1/sessions?session_name=Sprint&year=" + str(
        year
    )
    response_sprint = requests.get(url_sprint)
    sprints = response_sprint.json()

    # Obtain the races from the current year
    url_race = "https://api.openf1.org/v1/sessions?session_name=Race&year=" + str(year)
    response_race = requests.get(url_race)
    races = response_race.json()

    # Save the session keys for each type
    races = {session["session_key"]: session["circuit_short_name"] for session in races}
    sprints = {
        session["session_key"]: session["circuit_short_name"] for session in sprints
    }

    return {**races, **sprints}


def calculate_points(session: int) -> dict:
    """
    Calculate the points for each driver in a race session
    """
    url = "https://api.openf1.org/v1/session_result?session_key=" + str(session)
    response = requests.get(url)
    data = response.json()

    points = dict()
    for position in data:
        points[position["driver_number"]] = int(position["points"])

    return points


def get_drivers(session: int) -> list:
    """
    Obtain the drivers of each team for each session
    """
    Driver = namedtuple(
        "Driver",
        ["name_acronym", "driver_number", "last_name", "team_name", "headshot_url"],
    )

    unique_drivers = {}

    url = f"https://api.openf1.org/v1/drivers?session_key={session}"
    response = requests.get(url)
    data = response.json()

    for driver in data:
        number = driver["driver_number"]
        if number not in unique_drivers:
            headshot_url = driver.get("headshot_url")

            if not headshot_url:
                full_name = driver.get("full_name", "")
                if full_name and " " in full_name:
                    first_name, last_name = full_name.split(" ", 1)
                    driver_code = (last_name[:3] + first_name[:3] + "01").upper()
                    first_letter = driver_code[0]
                    headshot_url = (
                        f"https://media.formula1.com/d_driver_fallback_image.png"
                        f"/content/dam/fom-website/drivers/{first_letter}/{driver_code}/{driver_code}.png.transform/1col/image.png"
                    )
                else:
                    headshot_url = "null"

            driver_entry = Driver(
                driver["name_acronym"],
                number,
                driver["last_name"],
                driver["team_name"],
                headshot_url,
            )
            unique_drivers[number] = driver_entry

    all_drivers = list(unique_drivers.values())

    return all_drivers


def team_colors(session: int) -> dict:
    """
    Obtain the colors of each team from the year

    Input: The session_key of first race of the year
    Output: A dictionary with the colors of each team
    """

    url = "https://api.openf1.org/v1/drivers?session_key=" + str(session)
    response = requests.get(url)
    data = response.json()

    teams = dict()
    for driver in data:
        if driver["team_name"] not in teams:
            teams[driver["team_name"]] = "#" + driver["team_colour"]

    return teams


def standings(year: int):
    """
    Generate the standings with name_acronym as keys
    """
    sessions = list(get_session_keys(year).keys())
    standings = dict()

    for session in sessions:
        time.sleep(1.05)  # avoid rate limit
        points = calculate_points(session)

        time.sleep(1.05)
        drivers = get_drivers(session)

        # Build a mapping from driver_number to name_acronym
        number_to_acronym = {
            driver.driver_number: driver.name_acronym for driver in drivers
        }

        for driver_number, point in points.items():
            name_acronym = number_to_acronym.get(driver_number)

            if name_acronym:
                standings[name_acronym] = standings.get(name_acronym, 0) + point

    # Sort by points
    standings = dict(sorted(standings.items(), key=lambda item: item[1], reverse=True))
    return standings


def driver_standings_table(year: int):
    standings_data = standings(year)
    session_dict = get_session_keys(year)
    driver_info_map = {}

    # Sort sessions chronologically so the latest overwrites older info
    sorted_sessions = sorted(session_dict.keys())
    for session in sorted_sessions:
        time.sleep(1.05)
        drivers = get_drivers(session)
        for driver in drivers:
            driver_info_map[driver.name_acronym] = {
                "last_name": driver.last_name,
                "team_name": driver.team_name,
                "headshot_url": driver.headshot_url,
            }

    # Build table
    table = []
    for i, (driver_acronym, points) in enumerate(standings_data.items(), start=1):
        info = driver_info_map.get(driver_acronym, {})
        last_name = info.get("last_name", driver_acronym)
        team = info.get("team_name", "Unknown")
        table.append([i, last_name, team, points])

    headers = ["Position", "Driver", "Team", "Points"]
    print(tabulate(table, headers=headers, tablefmt="fancy_grid"))


def team_standings_table(year: int):
    standings_data = standings(year)
    session_dict = get_session_keys(year)

    # --- Build driver info map (latest info wins) ---
    driver_info_map = {}
    sorted_sessions = sorted(session_dict.keys())
    for session in sorted_sessions:
        time.sleep(1.05)
        drivers = get_drivers(session)
        for driver in drivers:
            driver_info_map[driver.name_acronym] = {
                "last_name": driver.last_name,
                "team_name": driver.team_name,
                "headshot_url": driver.headshot_url,
            }

    # --- Aggregate points by team using the info map ---
    team_points = defaultdict(int)
    for driver_acronym, points in standings_data.items():
        team = driver_info_map.get(driver_acronym, {}).get("team_name", "Unknown")
        team_points[team] += points

    # --- Sort and print table ---
    sorted_teams = sorted(team_points.items(), key=lambda x: x[1], reverse=True)

    table = []
    for i, (team, points) in enumerate(sorted_teams, start=1):
        table.append([i, team, points])

    headers = ["Position", "Team", "Points"]
    print(tabulate(table, headers=headers, tablefmt="fancy_grid"))


def driver_standings_html(year: int, filename: str = "driver_standings.html") -> None:
    # --- Data Collection ---
    standings_data = standings(year)
    session_dict = get_session_keys(year)
    driver_info_map = {}

    sorted_sessions = sorted(session_dict.keys())
    for session in sorted_sessions:
        time.sleep(1.05)
        drivers = get_drivers(session)
        for driver in drivers:
            driver_info_map[driver.name_acronym] = {
                "last_name": driver.last_name,
                "team_name": driver.team_name,
                "headshot_url": driver.headshot_url,
            }

    first_session = sorted_sessions[0]
    team_color_map = team_colors(first_session)

    # --- HTML Rows Construction ---
    rows_html = []
    for i, (driver_acronym, points) in enumerate(standings_data.items(), start=1):
        info = driver_info_map.get(driver_acronym, {})
        team_name = info.get("team_name")
        last_name = info.get("last_name")
        headshot = info.get("headshot_url")
        team_color = team_color_map.get(team_name, "#333333")

        team_code = team_name.lower().replace(" ", "")
        if team_code in {"mclaren", "alpine", "astonmartin"}:
            logo_url = f"https://media.formula1.com/image/upload/common/f1/{year}/{team_code}/{year}{team_code}logowhite.webp"
        else:
            logo_url = f"https://media.formula1.com/image/upload/common/f1/{year}/{team_code}/{year}{team_code}logo.webp"

        rows_html.append(
            f"""
            <tr style="background-color: {team_color};">
                <td class="position">{i}</td>
                <td><img class="team-logo" src="{logo_url}" alt="{team_name} logo" height="60"/></td>
                <td class="headshot-cell"><img class="headshot" src="{headshot}" alt="{driver_acronym}"/></td>
                <td class="last-name">{last_name}</td>
                <td class="points">{points}</td>
            </tr>
        """
        )

    # --- Full HTML ---
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <meta charset="UTF-8">
    <title>Driver Standings</title>
    <style>
        @font-face {{
            font-family: 'F1Regular';
            src: url('https://www.formula1.com/etc/designs/fom-website/fonts/F1Regular/Formula1-Regular.woff2') format('woff2');
            font-weight: normal;
            font-style: normal;
        }}
        body {{
            font-family: 'F1Regular', sans-serif;
            background-color: #f9f9f9;
        }}
        .standings-container {{
            max-width: 750px;
            margin: 40px auto;
        }}
        .logo {{
            display: block;
            width: 100%;
            height: 150px;
            object-fit: cover;
            object-position: center 55%;
            margin: 0;
        }}
        h2 {{
            text-align: center;
            font-size: 50px;
            color: white;
            font-weight: bold;
            margin: 0;
            background-color: #2E3336;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
        }}
        tr {{
            border-bottom: 2px solid white;
        }}
        td {{
            padding: 10px;
            vertical-align: middle;
        }}
        .position {{
            background-color: #2E3336;
            text-align: center;
            color: white;
            font-weight: bold;
            font-size: 32px;
            width: 60px;
        }}
        .headshot-cell {{
            width: 100px;
            height: 80px;
            padding: 0;
            overflow: hidden;	
        }}
        .headshot {{
            width: 100%;
            height: 100px;
            object-fit: cover;
            object-position: center 10%;
            display: block.
        }}
        .last-name {{
            font-size: 42px;
            color: white;
            text-transform: uppercase;
            font-weight: bold.
        }}
        .points {{
            background-color: red;
            color: white;
            font-weight: bold;
            font-size: 40px;
            text-align: center;
        }}
        .team-logo {{
            display: block;
            margin: auto;
        }}
    </style>
    </head>
    <body>
        <div class="standings-container">
            <img src="https://raw.githubusercontent.com/br-g/openf1/refs/heads/main/documentation/images/logo.png" class="logo">
            <h2>DRIVER STANDINGS</h2>
            <table>
                <tbody>
                    {''.join(rows_html)}
                </tbody>
            </table>
        </div>
    </body>
    </html>
    """

    # --- Write to File ---
    with open(filename, "w", encoding="utf-8") as f:
        f.write(html.strip())


def team_standings_html(year: int, filename: str = "team_standings.html") -> None:
    import time
    from collections import defaultdict

    standings_data = standings(year)
    session_dict = get_session_keys(year)

    # Get latest team info per driver
    driver_team_map = {}
    sorted_sessions = sorted(session_dict.keys())
    for session in sorted_sessions:
        time.sleep(1.05)
        drivers = get_drivers(session)
        for driver in drivers:
            driver_team_map[driver.name_acronym] = driver.team_name

    # Get team colors from first session
    first_session = sorted_sessions[0]
    team_color_map = team_colors(first_session)

    # Aggregate points per team
    team_points = defaultdict(int)
    for driver_acronym, points in standings_data.items():
        team = driver_team_map.get(driver_acronym, "Unknown")
        team_points[team] += points

    # Sort by points
    sorted_teams = sorted(team_points.items(), key=lambda x: x[1], reverse=True)

    # Build HTML rows
    rows_html = []
    for i, (team_name, points) in enumerate(sorted_teams, start=1):
        team_color = team_color_map.get(team_name, "#333333")
        team_code = team_name.lower().replace(" ", "")
        if team_code in {"mclaren", "alpine", "astonmartin"}:
            logo_url = f"https://media.formula1.com/image/upload/common/f1/{year}/{team_code}/{year}{team_code}logowhite.webp"
        else:
            logo_url = f"https://media.formula1.com/image/upload/common/f1/{year}/{team_code}/{year}{team_code}logo.webp"

        rows_html.append(
            f"""
            <tr style="background-color: {team_color};">
                <td class="position">{i}</td>
                <td><img class="team-logo" src="{logo_url}" alt="{team_name} logo" height="60"/></td>
                <td class="team-name">{team_name}</td>
                <td class="points">{points}</td>
            </tr>
        """
        )

    # Build full HTML
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <meta charset="UTF-8">
    <title>Team Standings</title>
    <style>
        @font-face {{
            font-family: 'F1Regular';
            src: url('https://www.formula1.com/etc/designs/fom-website/fonts/F1Regular/Formula1-Regular.woff2') format('woff2');
            font-weight: normal;
            font-style: normal;
        }}
        body {{
            font-family: 'F1Regular', sans-serif;
            background-color: #f9f9f9;
        }}
        .standings-container {{
            max-width: 750px;
            margin: 40px auto;
        }}
        .logo {{
            display: block;
            width: 100%;
            height: 150px;
            object-fit: cover;
            object-position: center 55%;
            margin: 0;
        }}
        h2 {{
            text-align: center;
            font-size: 50px;
            color: white;
            font-weight: bold;
            margin: 0;
            background-color: #2E3336;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
        }}
        tr {{
            border-bottom: 2px solid white;
        }}
        td {{
            padding: 10px;
            vertical-align: middle;
        }}
        .position {{
            background-color: #2E3336;
            text-align: center;
            color: white;
            font-weight: bold;
            font-size: 32px;
            width: 60px;
        }}
        .team-logo {{
            display: block;
            margin: auto;
        }}
        .team-name {{
            font-size: 42px;
            color: white;
            text-transform: uppercase;
            font-weight: bold;
        }}
        .points {{
            background-color: red;
            color: white;
            font-weight: bold;
            font-size: 40px;
            text-align: center;
        }}
    </style>
    </head>
    <body>
        <div class="standings-container">
            <img src="https://raw.githubusercontent.com/br-g/openf1/refs/heads/main/documentation/images/logo.png" class="logo">
            <h2>TEAM STANDINGS</h2>
            <table>
                <tbody>
                    {''.join(rows_html)}
                </tbody>
            </table>
        </div>
    </body>
    </html>
    """

    # Write HTML to file
    with open(filename, "w", encoding="utf-8") as f:
        f.write(html.strip())


if __name__ == "__main__":
    current_year = date.today().year

    parser = argparse.ArgumentParser(
        description="Generate standings (driver/team) in standard or HTML format."
    )
    parser.add_argument(
        "--standings",
        choices=["driver", "team"],
        default="driver",
        help="Which standings to generate (default: driver)",
    )
    parser.add_argument(
        "--year",
        type=int,
        default=current_year,
        help=f"Season year (default: {current_year})",
    )
    parser.add_argument(
        "--html",
        action="store_true",
        help="Output as HTML instead of standard table",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Optional output filename for HTML",
    )

    args = parser.parse_args()

    # Route based on args
    if args.standings == "driver":
        if args.html:
            filename = args.output or "driver_standings.html"
            if not filename.endswith(".html"):
                filename += ".html"
            driver_standings_html(args.year, filename=filename)
            print("Done!")
        else:
            print(f"Generating {args.year} Driver Standings!")
            driver_standings_table(args.year)

    elif args.standings == "team":
        if args.html:
            filename = args.output or "team_standings.html"
            if not filename.endswith(".html"):
                filename += ".html"
            team_standings_html(args.year, filename=filename)
            print("Done!")
        else:
            print(f"Generating {args.year} Team Standings!")
            team_standings_table(args.year)
