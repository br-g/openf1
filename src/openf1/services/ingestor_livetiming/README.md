# Ingestion of live timing data

This module receives, processes, and stores F1 live timing data.<br />
Live timing data can be ingested during a session (cf. [real_time/](real_time/))
or afterwards (cf. [historical/](historical/)).

## Main concepts

### Topics and Messages

A **topic** represents a channel through which raw data is streamed from the Formula 1
in the form of messages.<br />
Each **topic** delivers a specific kind of data (driver list, tyre information, ...).

### t0 (reference time)

**t0** is the reference time point for a session.<br />
In historical sessions, most timestamps in the data are relative to this **t0**.<br />
This reference time is essential for converting relative times into absolute timestamps.

### Documents and Collections

Processed data is stored as **documents**, which are derived from the incoming **messages**.<br />
A **collection** is a set of **documents** of the same type.<br />
**Documents** and **collections** are defined in [core/processing/collections/](core/processing/collections/).
