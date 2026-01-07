# Fetching and ingesting scraped data

### Schedule

Meetings:

```bash
python -m openf1.services.f1_scraping.schedule ingest-meetings --year 2025
```

Sessions:

```bash
python -m openf1.services.f1_scraping.schedule ingest-sessions --year 2025
```

### Session result

```bash
python -m openf1.services.f1_scraping.session_result --meeting-key 1264 --session-key 9955
```

If the parameters are not provided, it will default to the latest session (last completed session, or session in progress).

### Starting grid

```bash
python -m openf1.services.f1_scraping.starting_grid --meeting-key 1264 --session-key 9951
```

If the parameters are not provided, it will default to the latest session (last completed session, or session in progress).
Note that this function only works with qualifying sessions.
