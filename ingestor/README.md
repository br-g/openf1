# Ingestor

The Data Ingestor is a cloud-based service designed to efficiently ingest real-time and historical data. The service is hosted on Google Cloud Run and uses Python 3.9 and Flask.


## Features

- **Real-time data ingestion**: captures and processes data streams in real-time, providing low-latency data availability.
- **Redundancy**: maintains at least two instances during live sessions to ensure data reliability.
- **Data normalization**: performs basic data normalization for efficient database indexing.
- **Historical data**: supports ingestion of past events using a separate script (`ingest_history.py`).


## Requirements

- Python 3.9
- MongoDB
- Google Cloud Run
- Google Cloud Storage


## Quick start

### Install dependencies
First install the required Python packages.
```
pip install -r requirements.txt
```

### Environment variables
Set the necessary environment variables for MongoDB, Google Cloud, and storage bucket.
```
export MONGO_CONNECTION_STRING=... # MongoDB connection string
export GOOGLE_CREDENTIALS=...      # Google Cloud Platform credentials
export BUCKET_API_RAW=...          # Google Cloud Storage bucket for raw data
```

### Run the service
Once your environment is set up, launch the Data Ingestor service.
```
python app.py
```

Start recording data and ingesting by navigating to this URL in your web browser: <a href="http://127.0.0.1:8080" target="_blank">http://127.0.0.1:8080</a>.


## Historical data ingestion

After installing dependencies and setting environment variables, you can use the <a href="https://github.com/br-g/openf1/blob/main/ingestor/ingest_history.py" target="_blank">ingest_history.py</a> script to ingest data for a past Grand Prix event.

For example, to ingest data for the 2023 Bahrain Grand Prix (meeting key: `1141`), run:
```
python ingest_history.py ingest-meeting 2023 1141
```

To find meeting keys for other events, visit <a href="https://livetiming.formula1.com/static/2023/Index.json" target="_blank">https://livetiming.formula1.com/static/2023/Index.json</a>.
