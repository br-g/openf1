# Ingesting real-time data

To start ingesting a session in progress:

```bash
python -m openf1.services.ingestor_livetiming.real_time.app
```

Start recording 90 minutes before the session for races, practice, and qualifying.

### Live telemetry (optional)

To also ingest live telemetry, provide an F1TV subscription token:

```bash
export F1_TOKEN=...
```

See [this guide](https://github.com/SoMuchForSubtlety/f1viewer/wiki/Getting-your-subscription-token) for how to obtain a token. Note that tokens typically expire after 4 days.
