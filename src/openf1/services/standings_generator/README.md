# Standings generator

The script `standings.py` generates the Formula 1 standings (driver 
or team) for a given season via the API methods. 

There are 2 different output formats, via console tables or a HTML file.

> NOTE: The HTML option only works propperly for the current season.

## Usage

Run the script from the command line

```bash
python3 standings.py [OPTIONS]
```

## Options

In case you need, there is a help command by using `-h` or `--help`.

| Option                  | Description                                                   | Default                        |
|--------------------------|---------------------------------------------------------------|--------------------------------|
| `--standings {driver,team}` | Which standings to generate (`driver` or `team`)             | `driver`                       |
| `--year YEAR`            | Season year to fetch standings for                            | Current year                   |
| `--html`                 | Output standings as an HTML file instead of a terminal table  | `False`                        |
| `--output FILE`          | Optional filename for the HTML output (adds `.html` if missing) | `driver_standings.html` or `team_standings.html` |

## Examples

Generate **driver standings for the current season** in the terminal:
```bash
python standings.py --standings driver
```

Generate **team standings for 2023** in the terminal:

```bash
python standings.py --standings team --year 2023
```

Export **team standings for the current season to a custom filename**:
```bash
python standings.py --standings team --html --output my_teams.html
```