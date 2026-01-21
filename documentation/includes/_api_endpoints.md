# API endpoints

## Car data

Some data about each car, at a sample rate of about 3.7 Hz.

<aside class="notice">
Live data for this endpoint is currently unavailable during sessions.  
The data will be provided shortly after each session instead.
</aside>

```shell
curl "https://api.openf1.org/v1/car_data?driver_number=55&session_key=9159&speed>=315"
```

```python
from urllib.request import urlopen
import json

response = urlopen('https://api.openf1.org/v1/car_data?driver_number=55&session_key=9159&speed>=315')
data = json.loads(response.read().decode('utf-8'))
print(data)

# If you want, you can import the results in a DataFrame (you need to install the `pandas` package first)
# import pandas as pd
# df = pd.DataFrame(data)
```

```r
# If needed, install libraries
# install.packages('httr')
# install.packages('jsonlite')

library(httr)
library(jsonlite)

response <- GET('https://api.openf1.org/v1/car_data?driver_number=55&session_key=9159&speed>=315')
parsed_data <- fromJSON(content(response, 'text'))
print(parsed_data)

# If you want, you can import the results in a DataFrame
# df <- do.call(rbind, lapply(parsed_data, data.frame, stringsAsFactors = FALSE))
# df <- as.data.frame(t(as.matrix(df)))
```

```javascript
fetch(
  "https://api.openf1.org/v1/car_data?driver_number=55&session_key=9159&speed>=315"
)
  .then((response) => response.json())
  .then((jsonContent) => console.log(jsonContent));
```

> Output:

```json
[
  {
    "brake": 0,
    "date": "2023-09-15T13:08:19.923000+00:00",
    "driver_number": 55,
    "drs": 12,
    "meeting_key": 1219,
    "n_gear": 8,
    "rpm": 11141,
    "session_key": 9159,
    "speed": 315,
    "throttle": 99
  },
  {
    "brake": 100,
    "date": "2023-09-15T13:35:41.808000+00:00",
    "driver_number": 55,
    "drs": 8,
    "meeting_key": 1219,
    "n_gear": 8,
    "rpm": 11023,
    "session_key": 9159,
    "speed": 315,
    "throttle": 57
  }
]
```

### HTTP Request

`GET https://api.openf1.org/v1/car_data`

### Sample URL

<a href="https://api.openf1.org/v1/car_data?driver_number=55&amp;session_key=9159&amp;speed&gt;=315" target="_blank">https://api.openf1.org/v1/car_data?driver_number=55&amp;session_key=9159&amp;speed&gt;=315</a>

### Attributes

| Name          | Description                                                                                                                                                                           |
| ------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| brake         | Whether the brake pedal is pressed (`100`) or not (`0`).                                                                                                                              |
| date          | The UTC date and time, in ISO 8601 format.                                                                                                                                            |
| driver_number | The unique number assigned to an F1 driver (cf. <a href="https://en.wikipedia.org/wiki/List_of_Formula_One_driver_numbers#Formula_One_driver_numbers" target="_blank">Wikipedia</a>). |
| drs           | The Drag Reduction System (DRS) status (see mapping table below).                                                                                                                     |
| meeting_key   | The unique identifier for the meeting. Use `latest` to identify the latest or current meeting.                                                                                        |
| n_gear        | Current gear selection, ranging from 1 to 8. `0` indicates neutral or no gear engaged.                                                                                                |
| rpm           | Revolutions per minute of the engine.                                                                                                                                                 |
| session_key   | The unique identifier for the session. Use `latest` to identify the latest or current session.                                                                                        |
| speed         | Velocity of the car in km/h.                                                                                                                                                          |
| throttle      | Percentage of maximum engine power being used.                                                                                                                                        |

<br /><br />

            Below is a table that correlates DRS values to its supposed interpretation
            (from <a href="https://github.com/theOehrly/Fast-F1/blob/317bacf8c61038d7e8d0f48165330167702b349f/fastf1/_api.py#L863" target="_blank">FastF1</a>).

            <table id="drs_values">
                <thead>
                    <tr>
                    <th>DRS value</th>
                    <th>Interpretation</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                    <td>0</td>
                    <td>DRS off</td>
                    </tr>
                    <tr>
                    <td>1</td>
                    <td>DRS off</td>
                    </tr>
                    <tr>
                    <td>2</td>
                    <td>?</td>
                    </tr>
                    <tr>
                    <td>3</td>
                    <td>?</td>
                    </tr>
                    <tr>
                    <td>8</td>
                    <td>Detected, eligible once in activation zone</td>
                    </tr>
                    <tr>
                    <td>9</td>
                    <td>?</td>
                    </tr>
                    <tr>
                    <td>10</td>
                    <td>DRS on</td>
                    </tr>
                    <tr>
                    <td>12</td>
                    <td>DRS on</td>
                    </tr>
                    <tr>
                    <td>14</td>
                    <td>DRS on</td>
                    </tr>
                </tbody>
            </table>

## Drivers championship (beta)

Provides championship standings for drivers. Only available for race sessions.

```shell
curl "https://api.openf1.org/v1/championship_drivers?session_key=9839&driver_number=4&driver_number=81"
```

```python
from urllib.request import urlopen
import json

response = urlopen('https://api.openf1.org/v1/championship_drivers?session_key=9839&driver_number=4&driver_number=81')
data = json.loads(response.read().decode('utf-8'))
print(data)

# If you want, you can import the results in a DataFrame (you need to install the `pandas` package first)
# import pandas as pd
# df = pd.DataFrame(data)
```

```r
# If needed, install libraries
# install.packages('httr')
# install.packages('jsonlite')

library(httr)
library(jsonlite)

response <- GET('https://api.openf1.org/v1/championship_drivers?session_key=9839&driver_number=4&driver_number=81')
parsed_data <- fromJSON(content(response, 'text'))
print(parsed_data)

# If you want, you can import the results in a DataFrame
# df <- do.call(rbind, lapply(parsed_data, data.frame, stringsAsFactors = FALSE))
# df <- as.data.frame(t(as.matrix(df)))
```

```javascript
fetch(
  "https://api.openf1.org/v1/championship_drivers?session_key=9839&driver_number=4&driver_number=81"
)
  .then((response) => response.json())
  .then((jsonContent) => console.log(jsonContent));
```

> Output:

```json
[
  {
    "driver_number": 4,
    "meeting_key": 1276,
    "points_current": 423,
    "points_start": 408,
    "position_current": 1,
    "position_start": 1,
    "session_key": 9839
  },
  {
    "driver_number": 81,
    "meeting_key": 1276,
    "points_current": 410,
    "points_start": 392,
    "position_current": 3,
    "position_start": 3,
    "session_key": 9839
  }
]
```

### HTTP Request

`GET https://api.openf1.org/v1/championship_drivers`

### Sample URL

<a href="https://api.openf1.org/v1/championship_drivers?session_key=9839&amp;driver_number=4&amp;driver_number=81" target="_blank">https://api.openf1.org/v1/championship_drivers?session_key=9839&amp;driver_number=4&amp;driver_number=81</a>

### Attributes

| Name             | Description                                                                                                                                                                           |
| ---------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| driver_number    | The unique number assigned to an F1 driver (cf. <a href="https://en.wikipedia.org/wiki/List_of_Formula_One_driver_numbers#Formula_One_driver_numbers" target="_blank">Wikipedia</a>). |
| meeting_key      | The unique identifier for the meeting. Use `latest` to identify the latest or current meeting.                                                                                        |
| points_current   | Championship points during/after the race (depends on call timing).                                                                                                                   |
| points_start     | Championship points before the race started.                                                                                                                                          |
| position_current | Championship position during/after the race (depends on call timing).                                                                                                                 |
| position_start   | Championship position before the race started.                                                                                                                                        |
| session_key      | The unique identifier for the session. Use `latest` to identify the latest or current session.                                                                                        |

## Teams championship (beta)

Provides championship standings for teams. Only available for race sessions.

```shell
curl "https://api.openf1.org/v1/championship_teams?session_key=9839&team_name=McLaren"
```

```python
from urllib.request import urlopen
import json

response = urlopen('https://api.openf1.org/v1/championship_teams?session_key=9839&team_name=McLaren')
data = json.loads(response.read().decode('utf-8'))
print(data)

# If you want, you can import the results in a DataFrame (you need to install the `pandas` package first)
# import pandas as pd
# df = pd.DataFrame(data)
```

```r
# If needed, install libraries
# install.packages('httr')
# install.packages('jsonlite')

library(httr)
library(jsonlite)

response <- GET('https://api.openf1.org/v1/championship_teams?session_key=9839&team_name=McLaren')
parsed_data <- fromJSON(content(response, 'text'))
print(parsed_data)

# If you want, you can import the results in a DataFrame
# df <- do.call(rbind, lapply(parsed_data, data.frame, stringsAsFactors = FALSE))
# df <- as.data.frame(t(as.matrix(df)))
```

```javascript
fetch(
  "https://api.openf1.org/v1/championship_teams?session_key=9839&team_name=McLaren"
)
  .then((response) => response.json())
  .then((jsonContent) => console.log(jsonContent));
```

> Output:

```json
[
  {
    "meeting_key": 1276,
    "points_current": 833,
    "points_start": 800,
    "position_current": 1,
    "position_start": 1,
    "session_key": 9839,
    "team_name": "McLaren"
  }
]
```

### HTTP Request

`GET https://api.openf1.org/v1/championship_teams`

### Sample URL

<a href="https://api.openf1.org/v1/championship_teams?session_key=9839&amp;team_name=McLaren" target="_blank">https://api.openf1.org/v1/championship_teams?session_key=9839&amp;team_name=McLaren</a>

### Attributes

| Name             | Description                                                                                    |
| ---------------- | ---------------------------------------------------------------------------------------------- |
| meeting_key      | The unique identifier for the meeting. Use `latest` to identify the latest or current meeting. |
| points_current   | Championship points during/after the race (depends on call timing).                            |
| points_start     | Championship points before the race started.                                                   |
| position_current | Championship position during/after the race (depends on call timing).                          |
| position_start   | Championship position before the race started.                                                 |
| session_key      | The unique identifier for the session. Use `latest` to identify the latest or current session. |
| team_name        | The name of the team.                                                                          |

## Drivers

Provides information about drivers for each session.

```shell
curl "https://api.openf1.org/v1/drivers?driver_number=1&session_key=9158"
```

```python
from urllib.request import urlopen
import json

response = urlopen('https://api.openf1.org/v1/drivers?driver_number=1&session_key=9158')
data = json.loads(response.read().decode('utf-8'))
print(data)

# If you want, you can import the results in a DataFrame (you need to install the `pandas` package first)
# import pandas as pd
# df = pd.DataFrame(data)
```

```r
# If needed, install libraries
# install.packages('httr')
# install.packages('jsonlite')

library(httr)
library(jsonlite)

response <- GET('https://api.openf1.org/v1/drivers?driver_number=1&session_key=9158')
parsed_data <- fromJSON(content(response, 'text'))
print(parsed_data)

# If you want, you can import the results in a DataFrame
# df <- do.call(rbind, lapply(parsed_data, data.frame, stringsAsFactors = FALSE))
# df <- as.data.frame(t(as.matrix(df)))
```

```javascript
fetch("https://api.openf1.org/v1/drivers?driver_number=1&session_key=9158")
  .then((response) => response.json())
  .then((jsonContent) => console.log(jsonContent));
```

> Output:

```json
[
  {
    "broadcast_name": "M VERSTAPPEN",
    "country_code": "NED",
    "driver_number": 1,
    "first_name": "Max",
    "full_name": "Max VERSTAPPEN",
    "headshot_url": "https://www.formula1.com/content/dam/fom-website/drivers/M/MAXVER01_Max_Verstappen/maxver01.png.transform/1col/image.png",
    "last_name": "Verstappen",
    "meeting_key": 1219,
    "name_acronym": "VER",
    "session_key": 9158,
    "team_colour": "3671C6",
    "team_name": "Red Bull Racing"
  }
]
```

### HTTP Request

`GET https://api.openf1.org/v1/drivers`

### Sample URL

<a href="https://api.openf1.org/v1/drivers?driver_number=1&amp;session_key=9158" target="_blank">https://api.openf1.org/v1/drivers?driver_number=1&amp;session_key=9158</a>

### Attributes

| Name           | Description                                                                                                                                                                           |
| -------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| broadcast_name | The driver's name, as displayed on TV.                                                                                                                                                |
| country_code   | A code that uniquely identifies the country.                                                                                                                                          |
| driver_number  | The unique number assigned to an F1 driver (cf. <a href="https://en.wikipedia.org/wiki/List_of_Formula_One_driver_numbers#Formula_One_driver_numbers" target="_blank">Wikipedia</a>). |
| first_name     | The driver's first name.                                                                                                                                                              |
| full_name      | The driver's full name.                                                                                                                                                               |
| headshot_url   | URL of the driver's face photo.                                                                                                                                                       |
| last_name      | The driver's last name.                                                                                                                                                               |
| meeting_key    | The unique identifier for the meeting. Use `latest` to identify the latest or current meeting.                                                                                        |
| name_acronym   | Three-letter acronym of the driver's name.                                                                                                                                            |
| session_key    | The unique identifier for the session. Use `latest` to identify the latest or current session.                                                                                        |
| team_colour    | The hexadecimal color value (RRGGBB) of the driver's team.                                                                                                                            |
| team_name      | Name of the driver's team.                                                                                                                                                            |

## Intervals

            Fetches real-time interval data between drivers and their gap to the race leader.
            Available during races only, with updates approximately every 4 seconds.

<aside class="notice">
Live data for this endpoint is currently unavailable during sessions.  
The data will be provided shortly after each session instead.
</aside>

```shell
curl "https://api.openf1.org/v1/intervals?session_key=9165&interval>0&interval<0.005"
```

```python
from urllib.request import urlopen
import json

response = urlopen('https://api.openf1.org/v1/intervals?session_key=9165&interval>0&interval<0.005')
data = json.loads(response.read().decode('utf-8'))
print(data)

# If you want, you can import the results in a DataFrame (you need to install the `pandas` package first)
# import pandas as pd
# df = pd.DataFrame(data)
```

```r
# If needed, install libraries
# install.packages('httr')
# install.packages('jsonlite')

library(httr)
library(jsonlite)

response <- GET('https://api.openf1.org/v1/intervals?session_key=9165&interval>0&interval<0.005')
parsed_data <- fromJSON(content(response, 'text'))
print(parsed_data)

# If you want, you can import the results in a DataFrame
# df <- do.call(rbind, lapply(parsed_data, data.frame, stringsAsFactors = FALSE))
# df <- as.data.frame(t(as.matrix(df)))
```

```javascript
fetch(
  "https://api.openf1.org/v1/intervals?session_key=9165&interval>0&interval<0.005"
)
  .then((response) => response.json())
  .then((jsonContent) => console.log(jsonContent));
```

> Output:

```json
[
  {
    "date": "2023-09-17T13:31:02.395000+00:00",
    "driver_number": 1,
    "gap_to_leader": 41.019,
    "interval": 0.003,
    "meeting_key": 1219,
    "session_key": 9165
  }
]
```

### HTTP Request

`GET https://api.openf1.org/v1/intervals`

### Sample URL

<a href="https://api.openf1.org/v1/intervals?session_key=9165&amp;interval&lt;0.005" target="_blank">https://api.openf1.org/v1/intervals?session_key=9165&amp;interval&lt;0.005</a>

### Attributes

| Name          | Description                                                                                                                                                                           |
| ------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| date          | The UTC date and time, in ISO 8601 format.                                                                                                                                            |
| driver_number | The unique number assigned to an F1 driver (cf. <a href="https://en.wikipedia.org/wiki/List_of_Formula_One_driver_numbers#Formula_One_driver_numbers" target="_blank">Wikipedia</a>). |
| gap_to_leader | The time gap to the race leader in seconds, `+1 LAP` if lapped, or `null` for the race leader.                                                                                        |
| interval      | The time gap to the car ahead in seconds, `+1 LAP` if lapped, or `null` for the race leader.                                                                                          |
| meeting_key   | The unique identifier for the meeting. Use `latest` to identify the latest or current meeting.                                                                                        |
| session_key   | The unique identifier for the session. Use `latest` to identify the latest or current session.                                                                                        |

## Laps

            Provides detailed information about individual laps.

```shell
curl "https://api.openf1.org/v1/laps?session_key=9161&driver_number=63&lap_number=8"
```

```python
from urllib.request import urlopen
import json

response = urlopen('https://api.openf1.org/v1/laps?session_key=9161&driver_number=63&lap_number=8')
data = json.loads(response.read().decode('utf-8'))
print(data)

# If you want, you can import the results in a DataFrame (you need to install the `pandas` package first)
# import pandas as pd
# df = pd.DataFrame(data)
```

```r
# If needed, install libraries
# install.packages('httr')
# install.packages('jsonlite')

library(httr)
library(jsonlite)

response <- GET('https://api.openf1.org/v1/laps?session_key=9161&driver_number=63&lap_number=8')
parsed_data <- fromJSON(content(response, 'text'))
print(parsed_data)

# If you want, you can import the results in a DataFrame
# df <- do.call(rbind, lapply(parsed_data, data.frame, stringsAsFactors = FALSE))
# df <- as.data.frame(t(as.matrix(df)))
```

```javascript
fetch(
  "https://api.openf1.org/v1/laps?session_key=9161&driver_number=63&lap_number=8"
)
  .then((response) => response.json())
  .then((jsonContent) => console.log(jsonContent));
```

> Output:

```json
[
  {
    "date_start": "2023-09-16T13:59:07.606000+00:00",
    "driver_number": 63,
    "duration_sector_1": 26.966,
    "duration_sector_2": 38.657,
    "duration_sector_3": 26.12,
    "i1_speed": 307,
    "i2_speed": 277,
    "is_pit_out_lap": false,
    "lap_duration": 91.743,
    "lap_number": 8,
    "meeting_key": 1219,
    "segments_sector_1": [2049, 2049, 2049, 2051, 2049, 2051, 2049, 2049],
    "segments_sector_2": [2049, 2049, 2049, 2049, 2049, 2049, 2049, 2049],
    "segments_sector_3": [2048, 2048, 2048, 2048, 2048, 2064, 2064, 2064],
    "session_key": 9161,
    "st_speed": 298
  }
]
```

### HTTP Request

`GET https://api.openf1.org/v1/laps`

### Sample URL

<a href="https://api.openf1.org/v1/laps?session_key=9161&amp;driver_number=63&amp;lap_number=8" target="_blank">https://api.openf1.org/v1/laps?session_key=9161&amp;driver_number=63&amp;lap_number=8</a>

### Attributes

| Name              | Description                                                                                                                                                                           |
| ----------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| date_start        | The UTC starting date and time, in ISO 8601 format. This date is approximate.                                                                                                         |
| driver_number     | The unique number assigned to an F1 driver (cf. <a href="https://en.wikipedia.org/wiki/List_of_Formula_One_driver_numbers#Formula_One_driver_numbers" target="_blank">Wikipedia</a>). |
| duration_sector_1 | The time taken, in seconds, to complete the first sector of the lap.                                                                                                                  |
| duration_sector_2 | The time taken, in seconds, to complete the second sector of the lap.                                                                                                                 |
| duration_sector_3 | The time taken, in seconds, to complete the third sector of the lap.                                                                                                                  |
| i1_speed          | The speed of the car, in km/h, at the first intermediate point on the track.                                                                                                          |
| i2_speed          | The speed of the car, in km/h, at the second intermediate point on the track.                                                                                                         |
| is_pit_out_lap    | A boolean value indicating whether the lap is an "out lap" from the pit (`true` if it is, `false` otherwise).                                                                         |
| lap_duration      | The total time taken, in seconds, to complete the entire lap.                                                                                                                         |
| lap_number        | The sequential number of the lap within the session (starts at 1).                                                                                                                    |
| meeting_key       | The unique identifier for the meeting. Use `latest` to identify the latest or current meeting.                                                                                        |
| segments_sector_1 | A list of values representing the "mini-sectors" within the first sector (see mapping table below).                                                                                   |
| segments_sector_2 | A list of values representing the "mini-sectors" within the second sector (see mapping table below).                                                                                  |
| segments_sector_3 | A list of values representing the "mini-sectors" within the third sector (see mapping table below).                                                                                   |
| session_key       | The unique identifier for the session. Use `latest` to identify the latest or current session.                                                                                        |
| st_speed          | The speed of the car, in km/h, at the speed trap, which is a specific point on the track where the highest speeds are usually recorded.                                               |

<br /><br />

            Below is a table that correlates segment values to their meaning.

            <table id="segment_mapping">
                <thead>
                    <tr>
                    <th>Value</th>
                    <th>Color</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                    <td>0</td>
                    <td>not available</td>
                    </tr>
                    <tr>
                    <td><span style="color: #fdde00;">2048</span></td>
                    <td><span style="color: #fdde00;">yellow sector</span></td>
                    </tr>
                    <tr>
                    <td><span style="color: #4bdd49;">2049</span></td>
                    <td><span style="color: #4bdd49;">green sector</span></td>
                    </tr>
                    <tr>
                    <td>2050</td>
                    <td>?</td>
                    </tr>
                    <tr>
                    <td><span style="color: #c92cd5;">2051</span></td>
                    <td><span style="color: #c92cd5;">purple sector</span></td>
                    </tr>
                    <tr>
                    <td>2052</td>
                    <td>?</td>
                    </tr>
                    <tr>
                    <td>2064</td>
                    <td>pitlane</td>
                    </tr>
                    <tr>
                    <td>2068</td>
                    <td>?</td>
                    </tr>
                </tbody>
            </table>

            Segments are not available during races.
            Also, The segment values may not always align perfectly with the colors shown on TV, for unknown reasons.

## Location

            The approximate location of the cars on the circuit, at a sample rate of about 3.7 Hz.
            Useful for gauging their progress along the track, but lacks details about lateral placement — i.e. whether
            the car is on the left or right side of the track. The origin point (0, 0, 0) appears to be arbitrary
            and not tied to any specific location on the track.

<aside class="notice">
Live data for this endpoint is currently unavailable during sessions.  
The data will be provided shortly after each session instead.
</aside>

```shell
curl "https://api.openf1.org/v1/location?session_key=9161&driver_number=81&date>2023-09-16T13:03:35.200&date<2023-09-16T13:03:35.800"
```

```python
from urllib.request import urlopen
import json

response = urlopen('https://api.openf1.org/v1/location?session_key=9161&driver_number=81&date>2023-09-16T13:03:35.200&date<2023-09-16T13:03:35.800')
data = json.loads(response.read().decode('utf-8'))
print(data)

# If you want, you can import the results in a DataFrame (you need to install the `pandas` package first)
# import pandas as pd
# df = pd.DataFrame(data)
```

```r
# If needed, install libraries
# install.packages('httr')
# install.packages('jsonlite')

library(httr)
library(jsonlite)

response <- GET('https://api.openf1.org/v1/location?session_key=9161&driver_number=81&date>2023-09-16T13:03:35.200&date<2023-09-16T13:03:35.800')
parsed_data <- fromJSON(content(response, 'text'))
print(parsed_data)

# If you want, you can import the results in a DataFrame
# df <- do.call(rbind, lapply(parsed_data, data.frame, stringsAsFactors = FALSE))
# df <- as.data.frame(t(as.matrix(df)))
```

```javascript
fetch(
  "https://api.openf1.org/v1/location?session_key=9161&driver_number=81&date>2023-09-16T13:03:35.200&date<2023-09-16T13:03:35.800"
)
  .then((response) => response.json())
  .then((jsonContent) => console.log(jsonContent));
```

> Output:

```json
[
  {
    "date": "2023-09-16T13:03:35.292000+00:00",
    "driver_number": 81,
    "meeting_key": 1219,
    "session_key": 9161,
    "x": 567,
    "y": 3195,
    "z": 187
  },
  {
    "date": "2023-09-16T13:03:35.752000+00:00",
    "driver_number": 81,
    "meeting_key": 1219,
    "session_key": 9161,
    "x": 489,
    "y": 3403,
    "z": 186
  }
]
```

### HTTP Request

`GET https://api.openf1.org/v1/location`

### Sample URL

<a href="https://api.openf1.org/v1/location?session_key=9161&amp;driver_number=81&amp;date&gt;2023-09-16T13:03:35.200&amp;date&lt;2023-09-16T13:03:35.800" target="_blank">https://api.openf1.org/v1/location?session_key=9161&amp;driver_number=81&amp;date&gt;2023-09-16T13:03:35.200&amp;date&lt;2023-09-16T13:03:35.800</a>

### Attributes

| Name          | Description                                                                                                                                                                           |
| ------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| date          | The UTC date and time, in ISO 8601 format.                                                                                                                                            |
| driver_number | The unique number assigned to an F1 driver (cf. <a href="https://en.wikipedia.org/wiki/List_of_Formula_One_driver_numbers#Formula_One_driver_numbers" target="_blank">Wikipedia</a>). |
| meeting_key   | The unique identifier for the meeting. Use `latest` to identify the latest or current meeting.                                                                                        |
| session_key   | The unique identifier for the session. Use `latest` to identify the latest or current session.                                                                                        |
| x             | The 'x' value in a 3D Cartesian coordinate system representing the current approximate location of the car on the track.                                                              |
| y             | The 'y' value in a 3D Cartesian coordinate system representing the current approximate location of the car on the track.                                                              |
| z             | The 'z' value in a 3D Cartesian coordinate system representing the current approximate location of the car on the track.                                                              |

## Meetings

            Provides information about meetings.
            A meeting refers to a Grand Prix or testing weekend and usually includes multiple sessions (practice, qualifying, race, ...).
            Meetings are updated every day at midnight UTC.

```shell
curl "https://api.openf1.org/v1/meetings?year=2026&country_name=Singapore"
```

```python
from urllib.request import urlopen
import json

response = urlopen('https://api.openf1.org/v1/meetings?year=2026&country_name=Singapore')
data = json.loads(response.read().decode('utf-8'))
print(data)

# If you want, you can import the results in a DataFrame (you need to install the `pandas` package first)
# import pandas as pd
# df = pd.DataFrame(data)
```

```r
# If needed, install libraries
# install.packages('httr')
# install.packages('jsonlite')

library(httr)
library(jsonlite)

response <- GET('https://api.openf1.org/v1/meetings?year=2026&country_name=Singapore')
parsed_data <- fromJSON(content(response, 'text'))
print(parsed_data)

# If you want, you can import the results in a DataFrame
# df <- do.call(rbind, lapply(parsed_data, data.frame, stringsAsFactors = FALSE))
# df <- as.data.frame(t(as.matrix(df)))
```

```javascript
fetch("https://api.openf1.org/v1/meetings?year=2026&country_name=Singapore")
  .then((response) => response.json())
  .then((jsonContent) => console.log(jsonContent));
```

> Output:

```json
[
  {
    "circuit_key": 61,
    "circuit_image": "https://media.formula1.com/content/dam/fom-website/2018-redesign-assets/Track%20icons%204x3/Singapore%20carbon.png",
    "circuit_short_name": "Singapore",
    "circuit_type": "Temporary - Street",
    "country_code": "SGP",
    "country_flag": "https://media.formula1.com/content/dam/fom-website/2018-redesign-assets/Flags%2016x9/singapore-flag.png",
    "country_key": 157,
    "country_name": "Singapore",
    "date_end": "2026-10-11T14:00:00+00:00",
    "date_start": "2026-10-09T09:30:00+00:00",
    "gmt_offset": "08:00:00",
    "location": "Marina Bay",
    "meeting_key": 1296,
    "meeting_name": "Singapore Grand Prix",
    "meeting_official_name": "FORMULA 1 SINGAPORE AIRLINES SINGAPORE GRAND PRIX 2026",
    "year": 2026
  }
]
```

### HTTP Request

`GET https://api.openf1.org/v1/meetings`

### Sample URL

<a href="https://api.openf1.org/v1/meetings?year=2026&amp;country_name=Singapore" target="_blank">https://api.openf1.org/v1/meetings?year=2026&amp;country_name=Singapore</a>

### Attributes

| Name                  | Description                                                                                                        |
| --------------------- | ------------------------------------------------------------------------------------------------------------------ |
| circuit_key           | The unique identifier for the circuit where the event takes place.                                                 |
| circuit_image         | An image of the circuit.                                                                                           |
| circuit_short_name    | The short or common name of the circuit where the event takes place.                                               |
| circuit_type          | The type of the circuit ("Permanent", "Temporary - Street", or "Temporary - Road")                                 |
| country_code          | A code that uniquely identifies the country.                                                                       |
| country_flag          | An image of the country flag.                                                                                      |
| country_key           | The unique identifier for the country where the event takes place.                                                 |
| country_name          | The full name of the country where the event takes place.                                                          |
| date_end              | The UTC ending date and time, in ISO 8601 format.                                                                  |
| date_start            | The UTC starting date and time, in ISO 8601 format.                                                                |
| gmt_offset            | The difference in hours and minutes between local time at the location of the event and Greenwich Mean Time (GMT). |
| location              | The city or geographical location where the event takes place.                                                     |
| meeting_key           | The unique identifier for the meeting. Use `latest` to identify the latest or current meeting.                     |
| meeting_name          | The name of the meeting.                                                                                           |
| meeting_official_name | The official name of the meeting.                                                                                  |
| year                  | The year the event takes place.                                                                                    |

## Overtakes

            Provides information about overtakes.
            An overtake refers to one driver (the overtaking driver) exchanging positions with another driver (the overtaken driver). This includes both on-track passes and position changes resulting from pit stops or post-race penalties.
            This data is only available during races and may be incomplete.

```shell
curl "https://api.openf1.org/v1/overtakes?session_key=9636&overtaking_driver_number=63&overtaken_driver_number=4&position=1"
```

```python
from urllib.request import urlopen
import json

response = urlopen('https://api.openf1.org/v1/overtakes?session_key=9636&overtaking_driver_number=63&overtaken_driver_number=4&position=1')
data = json.loads(response.read().decode('utf-8'))
print(data)

# If you want, you can import the results in a DataFrame (you need to install the `pandas` package first)
# import pandas as pd
# df = pd.DataFrame(data)
```

```r
# If needed, install libraries
# install.packages('httr')
# install.packages('jsonlite')

library(httr)
library(jsonlite)

response <- GET('https://api.openf1.org/v1/overtakes?session_key=9636&overtaking_driver_number=63&overtaken_driver_number=4&position=1')
parsed_data <- fromJSON(content(response, 'text'))
print(parsed_data)

# If you want, you can import the results in a DataFrame
# df <- do.call(rbind, lapply(parsed_data, data.frame, stringsAsFactors = FALSE))
# df <- as.data.frame(t(as.matrix(df)))
```

```javascript
fetch(
  "https://api.openf1.org/v1/overtakes?session_key=9636&overtaking_driver_number=63&overtaken_driver_number=4&position=1"
)
  .then((response) => response.json())
  .then((jsonContent) => console.log(jsonContent));
```

> Output:

```json
[
  {
    "date": "2024-11-03T15:50:07.565000+00:00",
    "meeting_key": 1249,
    "overtaken_driver_number": 4,
    "overtaking_driver_number": 63,
    "position": 1,
    "session_key": 9636
  }
]
```

### HTTP Request

`GET https://api.openf1.org/v1/overtakes`

### Sample URL

<a href="https://api.openf1.org/v1/overtakes?session_key=9636&amp;overtaking_driver_number=63&amp;overtaken_driver_number=4&amp;position=1" target="_blank">https://api.openf1.org/v1/overtakes?session_key=9636&amp;overtaking_driver_number=63&amp;overtaken_driver_number=4&amp;position=1</a>

### Attributes

| Name                     | Description                                                                                                                                                                                       |
| ------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| date                     | The UTC date and time, in ISO 8601 format.                                                                                                                                                        |
| meeting_key              | The unique identifier for the meeting. Use `latest` to identify the latest or current meeting.                                                                                                    |
| overtaken_driver_number  | The unique number assigned to the overtaken F1 driver (cf. <a href="https://en.wikipedia.org/wiki/List_of_Formula_One_driver_numbers#Formula_One_driver_numbers" target="_blank">Wikipedia</a>).  |
| overtaking_driver_number | The unique number assigned to the overtaking F1 driver (cf. <a href="https://en.wikipedia.org/wiki/List_of_Formula_One_driver_numbers#Formula_One_driver_numbers" target="_blank">Wikipedia</a>). |
| position                 | The position of the overtaking F1 driver after the overtake was completed (starts at 1).                                                                                                          |
| session_key              | The unique identifier for the session. Use `latest` to identify the latest or current session.                                                                                                    |

## Pit

            Provides information about cars going through the pit lane.

```shell
curl "https://api.openf1.org/v1/pit?session_key=9877&stop_duration<2.3"
```

```python
from urllib.request import urlopen
import json

response = urlopen('https://api.openf1.org/v1/pit?session_key=9877&stop_duration<2.3')
data = json.loads(response.read().decode('utf-8'))
print(data)

# If you want, you can import the results in a DataFrame (you need to install the `pandas` package first)
# import pandas as pd
# df = pd.DataFrame(data)
```

```r
# If needed, install libraries
# install.packages('httr')
# install.packages('jsonlite')

library(httr)
library(jsonlite)

response <- GET('https://api.openf1.org/v1/pit?session_key=9877&stop_duration<2.3')
parsed_data <- fromJSON(content(response, 'text'))
print(parsed_data)

# If you want, you can import the results in a DataFrame
# df <- do.call(rbind, lapply(parsed_data, data.frame, stringsAsFactors = FALSE))
# df <- as.data.frame(t(as.matrix(df)))
```

```javascript
fetch("https://api.openf1.org/v1/pit?session_key=9877&stop_duration<2.3")
  .then((response) => response.json())
  .then((jsonContent) => console.log(jsonContent));
```

> Output:

```json
[
  {
    "date": "2025-10-26T20:46:37.358000+00:00",
    "driver_number": 16,
    "lane_duration": 22.215,
    "lap_number": 31,
    "meeting_key": 1272,
    "pit_duration": 22.215,
    "session_key": 9877,
    "stop_duration": 2.2
  },
  {
    "date": "2025-10-26T21:09:49.689000+00:00",
    "driver_number": 81,
    "lane_duration": 22.159,
    "lap_number": 47,
    "meeting_key": 1272,
    "pit_duration": 22.159,
    "session_key": 9877,
    "stop_duration": 2.1
  }
]
```

### HTTP Request

`GET https://api.openf1.org/v1/pit`

### Sample URL

<a href="https://api.openf1.org/v1/pit?session_key=9877&amp;stop_duration&lt;2.3" target="_blank">https://api.openf1.org/v1/pit?session_key=9877&amp;stop_duration&lt;2.3</a>

### Attributes

| Name                      | Description                                                                                                                                                                           |
| ------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| date                      | The UTC date and time, in ISO 8601 format.                                                                                                                                            |
| driver_number             | The unique number assigned to an F1 driver (cf. <a href="https://en.wikipedia.org/wiki/List_of_Formula_One_driver_numbers#Formula_One_driver_numbers" target="_blank">Wikipedia</a>). |
| lane_duration             | The time spent in the pit lane, in seconds.                                                                                                                                           |
| lap_number                | The sequential number of the lap within the session (starts at 1).                                                                                                                    |
| meeting_key               | The unique identifier for the meeting. Use `latest` to identify the latest or current meeting.                                                                                        |
| pit_duration (deprecated) | Same as 'lane_duration'. This field will be removed at the end of the 2026 season.                                                                                                    |
| session_key               | The unique identifier for the session. Use `latest` to identify the latest or current session.                                                                                        |
| stop_duration             | The stationary pit stop time, in seconds. This field is only available from the 2024 US GP onwards.                                                                                   |

## Position

            Provides driver positions throughout a session, including initial
            placement and subsequent changes.

```shell
curl "https://api.openf1.org/v1/position?meeting_key=1217&driver_number=40&position<=3"
```

```python
from urllib.request import urlopen
import json

response = urlopen('https://api.openf1.org/v1/position?meeting_key=1217&driver_number=40&position<=3')
data = json.loads(response.read().decode('utf-8'))
print(data)

# If you want, you can import the results in a DataFrame (you need to install the `pandas` package first)
# import pandas as pd
# df = pd.DataFrame(data)
```

```r
# If needed, install libraries
# install.packages('httr')
# install.packages('jsonlite')

library(httr)
library(jsonlite)

response <- GET('https://api.openf1.org/v1/position?meeting_key=1217&driver_number=40&position<=3')
parsed_data <- fromJSON(content(response, 'text'))
print(parsed_data)

# If you want, you can import the results in a DataFrame
# df <- do.call(rbind, lapply(parsed_data, data.frame, stringsAsFactors = FALSE))
# df <- as.data.frame(t(as.matrix(df)))
```

```javascript
fetch(
  "https://api.openf1.org/v1/position?meeting_key=1217&driver_number=40&position<=3"
)
  .then((response) => response.json())
  .then((jsonContent) => console.log(jsonContent));
```

> Output:

```json
[
  {
    "date": "2023-08-26T09:30:47.199000+00:00",
    "driver_number": 40,
    "meeting_key": 1217,
    "position": 2,
    "session_key": 9144
  },
  {
    "date": "2023-08-26T09:35:51.477000+00:00",
    "driver_number": 40,
    "meeting_key": 1217,
    "position": 3,
    "session_key": 9144
  }
]
```

### HTTP Request

`GET https://api.openf1.org/v1/position`

### Sample URL

<a href="https://api.openf1.org/v1/position?meeting_key=1217&amp;driver_number=40&amp;position&lt;=3" target="_blank">https://api.openf1.org/v1/position?meeting_key=1217&amp;driver_number=40&amp;position&lt;=3</a>

### Attributes

| Name          | Description                                                                                                                                                                           |
| ------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| date          | The UTC date and time, in ISO 8601 format.                                                                                                                                            |
| driver_number | The unique number assigned to an F1 driver (cf. <a href="https://en.wikipedia.org/wiki/List_of_Formula_One_driver_numbers#Formula_One_driver_numbers" target="_blank">Wikipedia</a>). |
| meeting_key   | The unique identifier for the meeting. Use `latest` to identify the latest or current meeting.                                                                                        |
| position      | Position of the driver (starts at 1).                                                                                                                                                 |
| session_key   | The unique identifier for the session. Use `latest` to identify the latest or current session.                                                                                        |

## Race control

            Provides information about race control (session status, racing incidents, flags, safety car, ...).

```shell
curl "https://api.openf1.org/v1/race_control?flag=BLACK AND WHITE&driver_number=1&date>=2023-01-01&date<2023-09-01"
```

```python
from urllib.request import urlopen
import json

response = urlopen('https://api.openf1.org/v1/race_control?flag=BLACK AND WHITE&driver_number=1&date>=2023-01-01&date<2023-09-01')
data = json.loads(response.read().decode('utf-8'))
print(data)

# If you want, you can import the results in a DataFrame (you need to install the `pandas` package first)
# import pandas as pd
# df = pd.DataFrame(data)
```

```r
# If needed, install libraries
# install.packages('httr')
# install.packages('jsonlite')

library(httr)
library(jsonlite)

response <- GET('https://api.openf1.org/v1/race_control?flag=BLACK AND WHITE&driver_number=1&date>=2023-01-01&date<2023-09-01')
parsed_data <- fromJSON(content(response, 'text'))
print(parsed_data)

# If you want, you can import the results in a DataFrame
# df <- do.call(rbind, lapply(parsed_data, data.frame, stringsAsFactors = FALSE))
# df <- as.data.frame(t(as.matrix(df)))
```

```javascript
fetch(
  "https://api.openf1.org/v1/race_control?flag=BLACK AND WHITE&driver_number=1&date>=2023-01-01&date<2023-09-01"
)
  .then((response) => response.json())
  .then((jsonContent) => console.log(jsonContent));
```

> Output:

```json
[
  {
    "category": "Flag",
    "date": "2023-06-04T14:21:01+00:00",
    "driver_number": 1,
    "flag": "BLACK AND WHITE",
    "lap_number": 59,
    "meeting_key": 1211,
    "message": "BLACK AND WHITE FLAG FOR CAR 1 (VER) - TRACK LIMITS",
    "qualifying_phase": null,
    "scope": "Driver",
    "sector": null,
    "session_key": 9102
  }
]
```

### HTTP Request

`GET https://api.openf1.org/v1/race_control`

### Sample URL

<a href="https://api.openf1.org/v1/race_control?flag=BLACK AND WHITE&amp;driver_number=1&amp;date&gt;=2023-01-01&amp;date&lt;2023-09-01" target="_blank">https://api.openf1.org/v1/race_control?flag=BLACK AND WHITE&amp;driver_number=1&amp;date&gt;=2023-01-01&amp;date&lt;2023-09-01</a>

### Attributes

| Name             | Description                                                                                                                                                                           |
| ---------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| category         | The category of the event (`SessionStatus`, `CarEvent`, `Drs`, `Flag`, `SafetyCar`, ...).                                                                                             |
| date             | The UTC date and time, in ISO 8601 format.                                                                                                                                            |
| driver_number    | The unique number assigned to an F1 driver (cf. <a href="https://en.wikipedia.org/wiki/List_of_Formula_One_driver_numbers#Formula_One_driver_numbers" target="_blank">Wikipedia</a>). |
| flag             | Type of flag displayed (`GREEN`, `YELLOW`, `DOUBLE YELLOW`, `CHEQUERED`, ...).                                                                                                        |
| lap_number       | The sequential number of the lap within the session (starts at 1), in a race.                                                                                                         |
| meeting_key      | The unique identifier for the meeting. Use `latest` to identify the latest or current meeting.                                                                                        |
| message          | Description of the event or action.                                                                                                                                                   |
| qualifying_phase | The specific phase (`1`, `2`, or `3`) if the session is a qualifying session.                                                                                                         |
| scope            | The scope of the event (`Track`, `Driver`, `Sector`, ...).                                                                                                                            |
| sector           | Segment ("mini-sector") of the track where the event occurred? (starts at 1).                                                                                                         |
| session_key      | The unique identifier for the session. Use `latest` to identify the latest or current session.                                                                                        |

## Sessions

            Provides information about sessions.
            A session refers to a distinct period of track activity during a Grand Prix or testing weekend (practice, qualifying, sprint, race, ...).
            Sessions are updated every day at midnight UTC.

```shell
curl "https://api.openf1.org/v1/sessions?country_name=Belgium&session_name=Sprint%20Qualifying&year=2023"
```

```python
from urllib.request import urlopen
import json

response = urlopen('https://api.openf1.org/v1/sessions?country_name=Belgium&session_name=Sprint%20Qualifying&year=2023')
data = json.loads(response.read().decode('utf-8'))
print(data)

# If you want, you can import the results in a DataFrame (you need to install the `pandas` package first)
# import pandas as pd
# df = pd.DataFrame(data)
```

```r
# If needed, install libraries
# install.packages('httr')
# install.packages('jsonlite')

library(httr)
library(jsonlite)

response <- GET('https://api.openf1.org/v1/sessions?country_name=Belgium&session_name=Sprint%20Qualifying&year=2023')
parsed_data <- fromJSON(content(response, 'text'))
print(parsed_data)

# If you want, you can import the results in a DataFrame
# df <- do.call(rbind, lapply(parsed_data, data.frame, stringsAsFactors = FALSE))
# df <- as.data.frame(t(as.matrix(df)))
```

```javascript
fetch(
  "https://api.openf1.org/v1/sessions?country_name=Belgium&session_name=Sprint%20Qualifying&year=2023"
)
  .then((response) => response.json())
  .then((jsonContent) => console.log(jsonContent));
```

> Output:

```json
[
  {
    "circuit_key": 7,
    "circuit_short_name": "Spa-Francorchamps",
    "country_code": "BEL",
    "country_key": 16,
    "country_name": "Belgium",
    "date_end": "2023-07-29T15:35:00+00:00",
    "date_start": "2023-07-29T15:05:00+00:00",
    "gmt_offset": "02:00:00",
    "location": "Spa-Francorchamps",
    "meeting_key": 1216,
    "session_key": 9140,
    "session_name": "Sprint Qualifying",
    "session_type": "Sprint Qualifying",
    "year": 2023
  }
]
```

### HTTP Request

`GET https://api.openf1.org/v1/sessions`

### Sample URL

<a href="https://api.openf1.org/v1/sessions?country_name=Belgium&amp;session_name=Sprint%20Qualifying&amp;year=2023" target="_blank">https://api.openf1.org/v1/sessions?country_name=Belgium&amp;session_name=Sprint%20Qualifying&amp;year=2023</a>

### Attributes

| Name               | Description                                                                                                        |
| ------------------ | ------------------------------------------------------------------------------------------------------------------ |
| circuit_key        | The unique identifier for the circuit where the event takes place.                                                 |
| circuit_short_name | The short or common name of the circuit where the event takes place.                                               |
| country_code       | A code that uniquely identifies the country.                                                                       |
| country_key        | The unique identifier for the country where the event takes place.                                                 |
| country_name       | The full name of the country where the event takes place.                                                          |
| date_end           | The UTC ending date and time, in ISO 8601 format.                                                                  |
| date_start         | The UTC starting date and time, in ISO 8601 format.                                                                |
| gmt_offset         | The difference in hours and minutes between local time at the location of the event and Greenwich Mean Time (GMT). |
| location           | The city or geographical location where the event takes place.                                                     |
| meeting_key        | The unique identifier for the meeting. Use `latest` to identify the latest or current meeting.                     |
| session_key        | The unique identifier for the session. Use `latest` to identify the latest or current session.                     |
| session_name       | The name of the session (`Practice 1`, `Qualifying`, `Race`, ...).                                                 |
| session_type       | The type of the session (`Practice`, `Qualifying`, `Race`, ...).                                                   |
| year               | The year the event takes place.                                                                                    |

## Session result

            Provides standings after a session.

```shell
curl "https://api.openf1.org/v1/session_result?session_key=7782&position%3C=3"
```

```python
from urllib.request import urlopen
import json

response = urlopen('https://api.openf1.org/v1/session_result?session_key=7782&position%3C=3')
data = json.loads(response.read().decode('utf-8'))
print(data)

# If you want, you can import the results in a DataFrame (you need to install the `pandas` package first)
# import pandas as pd
# df = pd.DataFrame(data)
```

```r
# If needed, install libraries
# install.packages('httr')
# install.packages('jsonlite')

library(httr)
library(jsonlite)

response <- GET('https://api.openf1.org/v1/session_result?session_key=7782&position%3C=3')
parsed_data <- fromJSON(content(response, 'text'))
print(parsed_data)

# If you want, you can import the results in a DataFrame
# df <- do.call(rbind, lapply(parsed_data, data.frame, stringsAsFactors = FALSE))
# df <- as.data.frame(t(as.matrix(df)))
```

```javascript
fetch("https://api.openf1.org/v1/session_result?session_key=7782&position%3C=3")
  .then((response) => response.json())
  .then((jsonContent) => console.log(jsonContent));
```

> Output:

```json
[
  {
    "dnf": false,
    "dns": false,
    "dsq": false,
    "driver_number": 1,
    "duration": 77.565,
    "gap_to_leader": 0,
    "number_of_laps": 24,
    "meeting_key": 1143,
    "position": 1,
    "session_key": 7782
  },
  {
    "dnf": false,
    "dns": false,
    "dsq": false,
    "driver_number": 14,
    "duration": 77.727,
    "gap_to_leader": 0.162,
    "number_of_laps": 26,
    "meeting_key": 1143,
    "position": 2,
    "session_key": 7782
  },
  {
    "dnf": false,
    "dns": false,
    "dsq": false,
    "driver_number": 31,
    "duration": 77.938,
    "gap_to_leader": 0.373,
    "number_of_laps": 23,
    "meeting_key": 1143,
    "position": 3,
    "session_key": 7782
  }
]
```

### HTTP Request

`GET https://api.openf1.org/v1/session_result`

### Sample URL

<a href="https://api.openf1.org/v1/session_result?session_key=7782&position<=3" target="_blank">https://api.openf1.org/v1/session_result?session_key=7782&position<=3</a>

### Attributes

| Name           | Description                                                                                                                                                                           |
| -------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| dnf            | Indicates whether the driver _Did Not Finish_ the race. This can be `true` only for qualifying and race sessions.                                                                     |
| dns            | Indicates whether the driver _Did Not Start_ the race. This can be `true` only for qualifying and race sessions.                                                                      |
| dsq            | Indicates whether the driver was disqualified.                                                                                                                                        |
| driver_number  | The unique number assigned to an F1 driver (cf. <a href="https://en.wikipedia.org/wiki/List_of_Formula_One_driver_numbers#Formula_One_driver_numbers" target="_blank">Wikipedia</a>). |
| duration       | Either the best lap time (for practice or qualifying), or the total race time (for races), in seconds. In qualifying, this is an array of three values for Q1, Q2, and Q3.            |
| gap_to_leader  | The time gap to the session leader in seconds, or `+N LAP(S)` if the driver was lapped. In qualifying, this is an array of three values for Q1, Q2, and Q3.                           |
| number_of_laps | Total number of laps completed during the session.                                                                                                                                    |
| meeting_key    | The unique identifier for the meeting. Use `latest` to identify the latest or current meeting.                                                                                        |
| position       | The driver’s final position at the end of the session.                                                                                                                                |
| session_key    | The unique identifier for the session. Use `latest` to identify the latest or current session.                                                                                        |

## Starting grid

            Provides the starting grid for the upcoming race.

```shell
curl "https://api.openf1.org/v1/starting_grid?session_key=7783&position%3C=3"
```

```python
from urllib.request import urlopen
import json

response = urlopen("https://api.openf1.org/v1/starting_grid?session_key=7783&position%3C=3")
data = json.loads(response.read().decode('utf-8'))
print(data)

# If you want, you can import the results in a DataFrame (you need to install the `pandas` package first)
# import pandas as pd
# df = pd.DataFrame(data)
```

```r
# If needed, install libraries
# install.packages('httr')
# install.packages('jsonlite')

library(httr)
library(jsonlite)

response <- GET("https://api.openf1.org/v1/starting_grid?session_key=7783&position%3C=3")
parsed_data <- fromJSON(content(response, 'text'))
print(parsed_data)

# If you want, you can import the results in a DataFrame
# df <- do.call(rbind, lapply(parsed_data, data.frame, stringsAsFactors = FALSE))
# df <- as.data.frame(t(as.matrix(df)))
```

```javascript
fetch("https://api.openf1.org/v1/starting_grid?session_key=7783&position%3C=3")
  .then((response) => response.json())
  .then((jsonContent) => console.log(jsonContent));
```

> Output:

```json
[
  {
    "position": 1,
    "driver_number": 1,
    "lap_duration": 76.732,
    "meeting_key": 1143,
    "session_key": 7783
  },
  {
    "position": 2,
    "driver_number": 63,
    "lap_duration": 76.968,
    "meeting_key": 1143,
    "session_key": 7783
  },
  {
    "position": 3,
    "driver_number": 44,
    "lap_duration": 77.104,
    "meeting_key": 1143,
    "session_key": 7783
  }
]
```

### HTTP Request

`GET https://api.openf1.org/v1/starting_grid`

### Sample URL

<a href="https://api.openf1.org/v1/starting_grid?session_key=7783&position<=3" target="_blank">https://api.openf1.org/v1/starting_grid?session_key=7783&position<=3</a>

### Attributes

| Name          | Description                                                                                                                                                                           |
| ------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| driver_number | The unique number assigned to an F1 driver (cf. <a href="https://en.wikipedia.org/wiki/List_of_Formula_One_driver_numbers#Formula_One_driver_numbers" target="_blank">Wikipedia</a>). |
| lap_duration  | Duration, in seconds, of the qualifying lap.                                                                                                                                          |
| meeting_key   | The unique identifier for the meeting. Use `latest` to identify the latest or current meeting.                                                                                        |
| position      | Position on the grid.                                                                                                                                                                 |
| session_key   | The unique identifier for the session. Use `latest` to identify the latest or current session.                                                                                        |

## Stints

            Provides information about individual stints.
            A stint refers to a period of continuous driving by a driver during a session.

```shell
curl "https://api.openf1.org/v1/stints?session_key=9165&tyre_age_at_start>=3"
```

```python
from urllib.request import urlopen
import json

response = urlopen('https://api.openf1.org/v1/stints?session_key=9165&tyre_age_at_start>=3')
data = json.loads(response.read().decode('utf-8'))
print(data)

# If you want, you can import the results in a DataFrame (you need to install the `pandas` package first)
# import pandas as pd
# df = pd.DataFrame(data)
```

```r
# If needed, install libraries
# install.packages('httr')
# install.packages('jsonlite')

library(httr)
library(jsonlite)

response <- GET('https://api.openf1.org/v1/stints?session_key=9165&tyre_age_at_start>=3')
parsed_data <- fromJSON(content(response, 'text'))
print(parsed_data)

# If you want, you can import the results in a DataFrame
# df <- do.call(rbind, lapply(parsed_data, data.frame, stringsAsFactors = FALSE))
# df <- as.data.frame(t(as.matrix(df)))
```

```javascript
fetch("https://api.openf1.org/v1/stints?session_key=9165&tyre_age_at_start>=3")
  .then((response) => response.json())
  .then((jsonContent) => console.log(jsonContent));
```

> Output:

```json
[
  {
    "compound": "SOFT",
    "driver_number": 16,
    "lap_end": 20,
    "lap_start": 1,
    "meeting_key": 1219,
    "session_key": 9165,
    "stint_number": 1,
    "tyre_age_at_start": 3
  },
  {
    "compound": "SOFT",
    "driver_number": 20,
    "lap_end": 62,
    "lap_start": 44,
    "meeting_key": 1219,
    "session_key": 9165,
    "stint_number": 3,
    "tyre_age_at_start": 3
  }
]
```

### HTTP Request

`GET https://api.openf1.org/v1/stints`

### Sample URL

<a href="https://api.openf1.org/v1/stints?session_key=9165&amp;tyre_age_at_start&gt;=3" target="_blank">https://api.openf1.org/v1/stints?session_key=9165&amp;tyre_age_at_start&gt;=3</a>

### Attributes

| Name              | Description                                                                                                                                                                           |
| ----------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| compound          | The specific compound of tyre used during the stint (`SOFT`, `MEDIUM`, `HARD`, ...).                                                                                                  |
| driver_number     | The unique number assigned to an F1 driver (cf. <a href="https://en.wikipedia.org/wiki/List_of_Formula_One_driver_numbers#Formula_One_driver_numbers" target="_blank">Wikipedia</a>). |
| lap_end           | Number of the last completed lap in this stint.                                                                                                                                       |
| lap_start         | Number of the initial lap in this stint (starts at 1).                                                                                                                                |
| meeting_key       | The unique identifier for the meeting. Use `latest` to identify the latest or current meeting.                                                                                        |
| session_key       | The unique identifier for the session. Use `latest` to identify the latest or current session.                                                                                        |
| stint_number      | The sequential number of the stint within the session (starts at 1).                                                                                                                  |
| tyre_age_at_start | The age of the tyres at the start of the stint, in laps completed.                                                                                                                    |

## Team radio

            Provides a collection of radio exchanges between Formula 1 drivers and their respective teams during sessions.
            Please note that only a limited selection of communications are included, not the complete record of radio interactions.

```shell
curl "https://api.openf1.org/v1/team_radio?session_key=9158&driver_number=11"
```

```python
from urllib.request import urlopen
import json

response = urlopen('https://api.openf1.org/v1/team_radio?session_key=9158&driver_number=11')
data = json.loads(response.read().decode('utf-8'))
print(data)

# If you want, you can import the results in a DataFrame (you need to install the `pandas` package first)
# import pandas as pd
# df = pd.DataFrame(data)
```

```r
# If needed, install libraries
# install.packages('httr')
# install.packages('jsonlite')

library(httr)
library(jsonlite)

response <- GET('https://api.openf1.org/v1/team_radio?session_key=9158&driver_number=11')
parsed_data <- fromJSON(content(response, 'text'))
print(parsed_data)

# If you want, you can import the results in a DataFrame
# df <- do.call(rbind, lapply(parsed_data, data.frame, stringsAsFactors = FALSE))
# df <- as.data.frame(t(as.matrix(df)))
```

```javascript
fetch("https://api.openf1.org/v1/team_radio?session_key=9158&driver_number=11")
  .then((response) => response.json())
  .then((jsonContent) => console.log(jsonContent));
```

> Output:

```json
[
  {
    "date": "2023-09-15T09:40:43.005000+00:00",
    "driver_number": 11,
    "meeting_key": 1219,
    "recording_url": "https://livetiming.formula1.com/static/2023/2023-09-17_Singapore_Grand_Prix/2023-09-15_Practice_1/TeamRadio/SERPER01_11_20230915_104008.mp3",
    "session_key": 9158
  },
  {
    "date": "2023-09-15T10:32:47.325000+00:00",
    "driver_number": 11,
    "meeting_key": 1219,
    "recording_url": "https://livetiming.formula1.com/static/2023/2023-09-17_Singapore_Grand_Prix/2023-09-15_Practice_1/TeamRadio/SERPER01_11_20230915_113201.mp3",
    "session_key": 9158
  }
]
```

### HTTP Request

`GET https://api.openf1.org/v1/team_radio`

### Sample URL

<a href="https://api.openf1.org/v1/team_radio?session_key=9158&amp;driver_number=11" target="_blank">https://api.openf1.org/v1/team_radio?session_key=9158&amp;driver_number=11</a>

### Attributes

| Name          | Description                                                                                                                                                                           |
| ------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| date          | The UTC date and time, in ISO 8601 format.                                                                                                                                            |
| driver_number | The unique number assigned to an F1 driver (cf. <a href="https://en.wikipedia.org/wiki/List_of_Formula_One_driver_numbers#Formula_One_driver_numbers" target="_blank">Wikipedia</a>). |
| meeting_key   | The unique identifier for the meeting. Use `latest` to identify the latest or current meeting.                                                                                        |
| recording_url | URL of the radio recording.                                                                                                                                                           |
| session_key   | The unique identifier for the session. Use `latest` to identify the latest or current session.                                                                                        |

## Weather

The weather over the track, updated every minute.

```shell
curl "https://api.openf1.org/v1/weather?meeting_key=1208&wind_direction>=130&track_temperature>=52"
```

```python
from urllib.request import urlopen
import json

response = urlopen('https://api.openf1.org/v1/weather?meeting_key=1208&wind_direction>=130&track_temperature>=52')
data = json.loads(response.read().decode('utf-8'))
print(data)

# If you want, you can import the results in a DataFrame (you need to install the `pandas` package first)
# import pandas as pd
# df = pd.DataFrame(data)
```

```r
# If needed, install libraries
# install.packages('httr')
# install.packages('jsonlite')

library(httr)
library(jsonlite)

response <- GET('https://api.openf1.org/v1/weather?meeting_key=1208&wind_direction>=130&track_temperature>=52')
parsed_data <- fromJSON(content(response, 'text'))
print(parsed_data)

# If you want, you can import the results in a DataFrame
# df <- do.call(rbind, lapply(parsed_data, data.frame, stringsAsFactors = FALSE))
# df <- as.data.frame(t(as.matrix(df)))
```

```javascript
fetch(
  "https://api.openf1.org/v1/weather?meeting_key=1208&wind_direction>=130&track_temperature>=52"
)
  .then((response) => response.json())
  .then((jsonContent) => console.log(jsonContent));
```

> Output:

```json
[
  {
    "air_temperature": 27.8,
    "date": "2023-05-07T18:42:25.233000+00:00",
    "humidity": 58,
    "meeting_key": 1208,
    "pressure": 1018.7,
    "rainfall": 0,
    "session_key": 9078,
    "track_temperature": 52.5,
    "wind_direction": 136,
    "wind_speed": 2.4
  }
]
```

### HTTP Request

`GET https://api.openf1.org/v1/weather`

### Sample URL

<a href="https://api.openf1.org/v1/weather?meeting_key=1208&amp;wind_direction&gt;=130&amp;track_temperature&gt;=52" target="_blank">https://api.openf1.org/v1/weather?meeting_key=1208&amp;wind_direction&gt;=130&amp;track_temperature&gt;=52</a>

### Attributes

| Name              | Description                                                                                    |
| ----------------- | ---------------------------------------------------------------------------------------------- |
| air_temperature   | Air temperature (°C).                                                                          |
| date              | The UTC date and time, in ISO 8601 format.                                                     |
| humidity          | Relative humidity (%).                                                                         |
| meeting_key       | The unique identifier for the meeting. Use `latest` to identify the latest or current meeting. |
| pressure          | Air pressure (mbar).                                                                           |
| rainfall          | Whether there is rainfall.                                                                     |
| session_key       | The unique identifier for the session. Use `latest` to identify the latest or current session. |
| track_temperature | Track temperature (°C).                                                                        |
| wind_direction    | Wind direction (°), from 0° to 359°.                                                           |
| wind_speed        | Wind speed (m/s).                                                                              |
