# Fetching and ingesting scrapped data

### Session result

```bash
python -m openf1.services.f1_scrapping.session_result --meeting-key 1264 --session-key 9955
```

If the parameters are not provided, it will default to the latest session (last completed session, or session in progress).

### Starting grid

```bash
python -m openf1.services.f1_scrapping.starting_grid --meeting-key 1264 --session-key 9955
```

If the parameters are not provided, it will default to the latest session (last completed session, or session in progress).
Note that this function only works with race sessions (races or sprint races).
