"""
Temporary data fixes.

Functions to apply temporary fixes to various data collections
until the data ingestion process is improved and the database is updated.
"""

from datetime import datetime, timezone

from openf1.util.db import session_key_to_path


def _fix_and_standardize_driver_data(results: list[dict]) -> list[dict]:
    DRIVER_NUM_TO_DATA = {
        1: {
            "broadcast_name": "M VERSTAPPEN",
            "country_code": "NED",
            "first_name": "Max",
            "full_name": "Max VERSTAPPEN",
            "headshot_url": "https://media.formula1.com/d_driver_fallback_image.png/content/dam/fom-website/drivers/M/MAXVER01_Max_Verstappen/maxver01.png.transform/1col/image.png",
            "last_name": "Verstappen",
            "driver_number": 1,
            "team_colour": "3671C6",
            "team_name": "Red Bull Racing",
            "name_acronym": "VER",
        },
        2: {
            "broadcast_name": "L SARGEANT",
            "country_code": "USA",
            "first_name": "Logan",
            "full_name": "Logan SARGEANT",
            "headshot_url": "https://media.formula1.com/d_driver_fallback_image.png/content/dam/fom-website/drivers/L/LOGSAR01_Logan_Sargeant/logsar01.png.transform/1col/image.png",
            "last_name": "Sargeant",
            "driver_number": 2,
            "team_colour": "64C4FF",
            "team_name": "Williams",
            "name_acronym": "SAR",
        },
        4: {
            "broadcast_name": "L NORRIS",
            "country_code": "GBR",
            "first_name": "Lando",
            "full_name": "Lando NORRIS",
            "headshot_url": "https://media.formula1.com/d_driver_fallback_image.png/content/dam/fom-website/drivers/L/LANNOR01_Lando_Norris/lannor01.png.transform/1col/image.png",
            "last_name": "Norris",
            "driver_number": 4,
            "team_colour": "FF8000",
            "team_name": "McLaren",
            "name_acronym": "NOR",
        },
        10: {
            "broadcast_name": "P GASLY",
            "country_code": "FRA",
            "first_name": "Pierre",
            "full_name": "Pierre GASLY",
            "headshot_url": "https://media.formula1.com/d_driver_fallback_image.png/content/dam/fom-website/drivers/P/PIEGAS01_Pierre_Gasly/piegas01.png.transform/1col/image.png",
            "last_name": "Gasly",
            "driver_number": 10,
            "team_colour": "0093cc",
            "team_name": "Alpine",
            "name_acronym": "GAS",
        },
        11: {
            "broadcast_name": "S PEREZ",
            "country_code": "MEX",
            "first_name": "Sergio",
            "full_name": "Sergio PEREZ",
            "headshot_url": "https://media.formula1.com/d_driver_fallback_image.png/content/dam/fom-website/drivers/S/SERPER01_Sergio_Perez/serper01.png.transform/1col/image.png",
            "last_name": "Perez",
            "driver_number": 11,
            "team_colour": "3671C6",
            "team_name": "Red Bull Racing",
            "name_acronym": "PER",
        },
        14: {
            "broadcast_name": "F ALONSO",
            "country_code": "ESP",
            "first_name": "Fernando",
            "full_name": "Fernando ALONSO",
            "headshot_url": "https://media.formula1.com/d_driver_fallback_image.png/content/dam/fom-website/drivers/F/FERALO01_Fernando_Alonso/feralo01.png.transform/1col/image.png",
            "last_name": "Alonso",
            "driver_number": 14,
            "team_colour": "229971",
            "team_name": "Aston Martin",
            "name_acronym": "ALO",
        },
        16: {
            "broadcast_name": "C LECLERC",
            "country_code": "MON",
            "first_name": "Charles",
            "full_name": "Charles LECLERC",
            "headshot_url": "https://media.formula1.com/d_driver_fallback_image.png/content/dam/fom-website/drivers/C/CHALEC01_Charles_Leclerc/chalec01.png.transform/1col/image.png",
            "last_name": "Leclerc",
            "driver_number": 16,
            "team_colour": "E80020",
            "team_name": "Ferrari",
            "name_acronym": "LEC",
        },
        20: {
            "broadcast_name": "K MAGNUSSEN",
            "country_code": "DEN",
            "first_name": "Kevin",
            "full_name": "Kevin MAGNUSSEN",
            "headshot_url": "https://media.formula1.com/d_driver_fallback_image.png/content/dam/fom-website/drivers/K/KEVMAG01_Kevin_Magnussen/kevmag01.png.transform/1col/image.png",
            "last_name": "Magnussen",
            "driver_number": 20,
            "team_colour": "B6BABD",
            "team_name": "Haas F1 Team",
            "name_acronym": "MAG",
        },
        22: {
            "broadcast_name": "Y TSUNODA",
            "country_code": "JPN",
            "first_name": "Yuki",
            "full_name": "Yuki TSUNODA",
            "headshot_url": "https://media.formula1.com/d_driver_fallback_image.png/content/dam/fom-website/drivers/Y/YUKTSU01_Yuki_Tsunoda/yuktsu01.png.transform/1col/image.png",
            "last_name": "Tsunoda",
            "driver_number": 22,
            "team_colour": "6692FF",
            "team_name": "Racing Bulls",
            "name_acronym": "TSU",
        },
        24: {
            "broadcast_name": "G ZHOU",
            "country_code": "CHN",
            "first_name": "Guanyu",
            "full_name": "ZHOU Guanyu",
            "headshot_url": "https://media.formula1.com/d_driver_fallback_image.png/content/dam/fom-website/drivers/G/GUAZHO01_Guanyu_Zhou/guazho01.png.transform/1col/image.png",
            "last_name": "Zhou",
            "driver_number": 24,
            "team_colour": "52E252",
            "team_name": "Kick Sauber",
            "name_acronym": "ZHO",
        },
        27: {
            "broadcast_name": "N HULKENBERG",
            "country_code": "GER",
            "first_name": "Nico",
            "full_name": "Nico HULKENBERG",
            "headshot_url": "https://media.formula1.com/d_driver_fallback_image.png/content/dam/fom-website/drivers/N/NICHUL01_Nico_Hulkenberg/nichul01.png.transform/1col/image.png",
            "last_name": "Hulkenberg",
            "driver_number": 27,
            "team_colour": "52E252",
            "team_name": "Kick Sauber",
            "name_acronym": "HUL",
        },
        31: {
            "broadcast_name": "E OCON",
            "country_code": "FRA",
            "first_name": "Esteban",
            "full_name": "Esteban OCON",
            "headshot_url": "https://media.formula1.com/d_driver_fallback_image.png/content/dam/fom-website/drivers/E/ESTOCO01_Esteban_Ocon/estoco01.png.transform/1col/image.png",
            "last_name": "Ocon",
            "driver_number": 31,
            "team_colour": "B6BABD",
            "team_name": "Haas F1 Team",
            "name_acronym": "OCO",
        },
        44: {
            "broadcast_name": "L HAMILTON",
            "country_code": "GBR",
            "first_name": "Lewis",
            "full_name": "Lewis HAMILTON",
            "headshot_url": "https://media.formula1.com/d_driver_fallback_image.png/content/dam/fom-website/drivers/L/LEWHAM01_Lewis_Hamilton/lewham01.png.transform/1col/image.png",
            "last_name": "Hamilton",
            "driver_number": 44,
            "team_colour": "E80020",
            "team_name": "Ferrari",
            "name_acronym": "HAM",
        },
        55: {
            "broadcast_name": "C SAINZ",
            "country_code": "ESP",
            "first_name": "Carlos",
            "full_name": "Carlos SAINZ",
            "headshot_url": "https://media.formula1.com/d_driver_fallback_image.png/content/dam/fom-website/drivers/C/CARSAI01_Carlos_Sainz/carsai01.png.transform/1col/image.png",
            "last_name": "Sainz",
            "driver_number": 55,
            "team_colour": "64C4FF",
            "team_name": "Williams",
            "name_acronym": "SAI",
        },
        63: {
            "broadcast_name": "G RUSSELL",
            "country_code": "GBR",
            "first_name": "George",
            "full_name": "George RUSSELL",
            "headshot_url": "https://media.formula1.com/d_driver_fallback_image.png/content/dam/fom-website/drivers/G/GEORUS01_George_Russell/georus01.png.transform/1col/image.png",
            "last_name": "Russell",
            "driver_number": 63,
            "team_colour": "27F4D2",
            "team_name": "Mercedes",
            "name_acronym": "RUS",
        },
        81: {
            "broadcast_name": "O PIASTRI",
            "country_code": "AUS",
            "first_name": "Oscar",
            "full_name": "Oscar PIASTRI",
            "headshot_url": "https://media.formula1.com/d_driver_fallback_image.png/content/dam/fom-website/drivers/O/OSCPIA01_Oscar_Piastri/oscpia01.png.transform/1col/image.png",
            "last_name": "Piastri",
            "driver_number": 81,
            "team_colour": "FF8000",
            "team_name": "McLaren",
            "name_acronym": "PIA",
        },
        23: {
            "broadcast_name": "A ALBON",
            "country_code": "THA",
            "first_name": "Alexander",
            "full_name": "Alexander ALBON",
            "headshot_url": "https://media.formula1.com/d_driver_fallback_image.png/content/dam/fom-website/drivers/A/ALEALB01_Alexander_Albon/alealb01.png.transform/1col/image.png",
            "last_name": "Albon",
            "driver_number": 23,
            "team_colour": "64C4FF",
            "team_name": "Williams",
            "name_acronym": "ALB",
        },
        77: {
            "broadcast_name": "V BOTTAS",
            "country_code": "FIN",
            "first_name": "Valtteri",
            "full_name": "Valtteri BOTTAS",
            "headshot_url": "https://media.formula1.com/d_driver_fallback_image.png/content/dam/fom-website/drivers/V/VALBOT01_Valtteri_Bottas/valbot01.png.transform/1col/image.png",
            "last_name": "Bottas",
            "driver_number": 77,
            "team_colour": "52E252",
            "team_name": "Kick Sauber",
            "name_acronym": "BOT",
        },
        18: {
            "broadcast_name": "L STROLL",
            "country_code": "CAN",
            "first_name": "Lance",
            "full_name": "Lance STROLL",
            "headshot_url": "https://media.formula1.com/d_driver_fallback_image.png/content/dam/fom-website/drivers/L/LANSTR01_Lance_Stroll/lanstr01.png.transform/1col/image.png",
            "last_name": "Stroll",
            "driver_number": 18,
            "team_colour": "229971",
            "team_name": "Aston Martin",
            "name_acronym": "STR",
        },
        3: {
            "broadcast_name": "D RICCIARDO",
            "country_code": "AUS",
            "first_name": "Daniel",
            "full_name": "Daniel RICCIARDO",
            "headshot_url": "https://media.formula1.com/d_driver_fallback_image.png/content/dam/fom-website/drivers/D/DANRIC01_Daniel_Ricciardo/danric01.png.transform/1col/image.png",
            "last_name": "Ricciardo",
            "driver_number": 3,
            "team_colour": "6692FF",
            "team_name": "RB",
            "name_acronym": "RIC",
        },
        40: {
            "broadcast_name": "A IWASA",
            "country_code": "JPN",
            "first_name": "Ayumu",
            "full_name": "Ayumu IWASA",
            "headshot_url": None,
            "last_name": "Iwasa",
            "driver_number": 40,
            "team_colour": "6692FF",
            "team_name": "RB",
            "name_acronym": "IWA",
        },
        5: {
            "broadcast_name": "G BORTOLETO",
            "country_code": "BRA",
            "first_name": "Gabriel",
            "full_name": "Gabriel BORTOLETO",
            "headshot_url": "https://media.formula1.com/d_driver_fallback_image.png/content/dam/fom-website/drivers/G/GABBOR01_Gabriel_Bortoleto/gabbor01.png.transform/1col/image.png",
            "last_name": "Bortoleto",
            "driver_number": 5,
            "team_colour": "52E252",
            "team_name": "Kick Sauber",
            "name_acronym": "BOR"
        },
        6: {
            "broadcast_name": "I HADJAR",
            "country_code": "FRA",
            "first_name": "Isack",
            "full_name": "Isack HADJAR",
            "headshot_url": "https://media.formula1.com/d_driver_fallback_image.png/content/dam/fom-website/drivers/I/ISAHAD01_Isack_Hadjar/isahad01.png.transform/1col/image.png",
            "last_name": "Hadjar",
            "driver_number": 6,
            "team_colour": "6692FF",
            "team_name": "Racing Bulls",
            "name_acronym": "HAD"
        },
        7: {
            "broadcast_name": "J DOOHAN",
            "country_code": "AUS",
            "first_name": "Jack",
            "full_name": "Jack DOOHAN",
            "headshot_url": "https://media.formula1.com/d_driver_fallback_image.png/content/dam/fom-website/drivers/J/JACDOO01_Jack_Doohan/jacdoo01.png.transform/1col/image.png",
            "last_name": "Doohan",
            "driver_number": 7,
            "team_colour": "0093cc",
            "team_name": "Alpine",
            "name_acronym": "DOO"
        },
        12: {
            "broadcast_name": "A ANTONELLI",
            "country_code": "ITA",
            "first_name": "Andrea Kimi",
            "full_name": "Andrea Kimi ANTONELLI",
            "headshot_url": "https://media.formula1.com/d_driver_fallback_image.png/content/dam/fom-website/drivers/A/ANDANT01_Andrea%20Kimi_Antonelli/andant01.png.transform/1col/image.png",
            "last_name": "Antonelli",
            "driver_number": 12,
            "team_colour": "27F4D2",
            "team_name": "Mercedes",
            "name_acronym": "ANT"
        },
        30: {
            "broadcast_name": "L LAWSON",
            "country_code": "NZL",
            "first_name": "Liam",
            "full_name": "Liam LAWSON",
            "headshot_url": "https://media.formula1.com/d_driver_fallback_image.png/content/dam/fom-website/drivers/L/LIALAW01_Liam_Lawson/lialaw01.png.transform/1col/image.png",
            "last_name": "Lawson",
            "driver_number": 30,
            "team_colour": "3671C6",
            "team_name": "Red Bull Racing",
            "name_acronym": "LAW"
        },
        87: {
            "broadcast_name": "O BEARMAN",
            "country_code": "GBR",
            "first_name": "Oliver",
            "full_name": "Oliver BEARMAN",
            "headshot_url": "https://media.formula1.com/d_driver_fallback_image.png/content/dam/fom-website/drivers/O/OLIBEA01_Oliver_Bearman/olibea01.png.transform/1col/image.png",
            "last_name": "Bearman",
            "driver_number": 87,
            "team_colour": "B6BABD",
            "team_name": "Haas F1 Team",
            "name_acronym": "BEA"
        },
    }

    for res in results:
        # Set color type to string
        if res["team_colour"] is not None:
            res["team_colour"] = str(res["team_colour"]).upper()

        # Fix Kick Sauber color
        if res["team_name"] == "Kick Sauber":
            res["team_colour"] = "52E252"

        # Fills missing data, but only for the 2024 season
        if res["session_key"] < 9465:
            continue
        for key, val in res.items():
            if val is None:
                ref = DRIVER_NUM_TO_DATA.get(res["driver_number"])
                if ref is not None:
                    res[key] = ref.get(key)

    return results


def _fix_position_data(results: list[dict]) -> list[dict]:
    """Remove entries with None positions."""
    return [r for r in results if r.get("position") is not None]


def _fix_team_radio_data(results: list[dict]) -> list[dict]:
    """Update recording URLs with correct session paths."""
    for res in results:
        path = session_key_to_path(res["session_key"])
        if path is not None:
            res["recording_url"] = res["recording_url"].replace(
                "2024/2024-03-02_Bahrain_Grand_Prix/2024-02-29_Practice_1/", path
            )
    return results


def _add_utc_timezone(results: list[dict]):
    """Add UTC timezone to datetime fields if not set."""
    for res in results:
        for key, val in res.items():
            if isinstance(val, datetime) and val.tzinfo is None:
                res[key] = val.replace(tzinfo=timezone.utc)


def apply_tmp_fixes(collection: str, results: list[dict]) -> list[dict]:
    fixes = {
        "drivers": _fix_and_standardize_driver_data,
        "position": _fix_position_data,
        "team_radio": _fix_team_radio_data,
    }

    if collection in fixes:
        results = fixes[collection](results)

    _add_utc_timezone(results)
    return results
