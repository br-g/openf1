# Ingesting real-time data

To start ingesting a session in progress:

```bash
python -m openf1.services.ingestor_livetiming.real_time.app
```

The recording must be started at least 1h before the start of the session for races,
and at least 15 minutes before the start of the session for practice and qualifying.

### Live telemetry (optional)

To also ingest live telemetry, provide an F1TV subscription token:

```bash
export F1_TOKEN=...
```

See [this guide](https://github.com/SoMuchForSubtlety/f1viewer/wiki/Getting-your-subscription-token) for how to obtain a token. Note that tokens typically expire after **4 days**.
