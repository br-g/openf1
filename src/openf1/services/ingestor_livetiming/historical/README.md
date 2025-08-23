# Fetching and ingesting historical livetiming data

### Get schedule

To fetch the raw sessions schedule for the 2024 season:

```bash
python -m openf1.services.ingestor_livetiming.historical.main get-schedule 2024
```

This command only returns past events.

### List available topics for a session

To list the available topics for session `9574` (meeting `1242`, year `2024`):

```bash
python -m openf1.services.ingestor_livetiming.historical.main list-topics 2024 1242 9574
```

### Get topic raw content

To fetch the raw content of topic `DriverList` for session `9574` (meeting `1242`, year `2024`):

```bash
python -m openf1.services.ingestor_livetiming.historical.main get-topic-content 2024 1242 9574 DriverList
```

### Get session t0

To compute the t0 value for session `9574` (meeting `1242`, year `2024`):

```bash
python -m openf1.services.ingestor_livetiming.historical.main get-t0 2024 1242 9574
```

### Get topic messages

To get the messages of topic `DriverList` for session `9574` (meeting `1242`, year `2024`):

```bash
python -m openf1.services.ingestor_livetiming.historical.main get-messages 2024 1242 9574 DriverList
```

### Get processed documents

To get the processed documents of collection `drivers` for session `9574` (meeting `1242`, year `2024`):

```bash
python -m openf1.services.ingestor_livetiming.historical.main get-processed-documents 2024 1242 9574 drivers
```

### Ingest collection

To ingest processed documents of collection `drivers` for session `9574` (meeting `1242`, year `2024`):

```bash
python -m openf1.services.ingestor_livetiming.historical.main ingest-collections 2024 1242 9574 drivers
```

### Ingest session

To ingest processed documents of all the available collections for session `9574` (meeting `1242`, year `2024`):

```bash
python -m openf1.services.ingestor_livetiming.historical.main ingest-session 2024 1242 9574
```

### Ingest meeting

To ingest processed documents of all the available collections for meeting `1242` (year `2024`):

```bash
python -m openf1.services.ingestor_livetiming.historical.main ingest-meeting 2024 1242
```

### Ingest season

To ingest processed documents of all the available collections for season `2024`:

```bash
python -m openf1.services.ingestor_livetiming.historical.main ingest-season 2024
```
