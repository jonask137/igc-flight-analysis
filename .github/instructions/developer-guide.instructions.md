---
applyTo: '**'
---

# 🧾 Project Summary: IGC Flight Analysis System

## 🎯 Purpose

Build a system that:

- Scrapes glider flight logs from GliderNet Flightbook API

- Stores flight and device metadata in a local SQLite database

- Downloads and stores associated .igc files

- Provides a Streamlit app to explore flight data and visualize flight tracks on a map

# 🧑‍💻 README.dev.md — Developer Guide for IGC Flight Analysis

This document provides implementation details for contributors and GitHub Copilot to extend and maintain the project.

# 🔧 Stack & Architecture

| Component      | Description                                                     |
| -------------- | --------------------------------------------------------------- |
| `scraper/`     | Downloads `.igc` files and daily flight metadata from GliderNet |
| `scripts/`     | Ingests scraped data into the SQLite database                   |
| `db/models.py` | SQLAlchemy ORM schema definitions                               |
| `app/main.py`  | Streamlit frontend for exploring and visualizing flights        |
| `data/raw/`    | Storage for `.igc` files and raw JSON                           |
| `uv.toml`      | UV dependency configuration                                     |
| `.venv/`       | Virtual environment with Streamlit, SQLAlchemy, etc.            |


📁 Project Layout

```bash
igc-flight-analysis/
├── app/                 # Streamlit UI
│   └── main.py
├── db/                  # SQLAlchemy ORM models
│   └── models.py
├── scraper/             # Data scraping from flightbook.glidernet.org
│   └── fetcher.py
├── scripts/             # Data ingestion pipeline
│   └── ingest_scraped_data.py
├── data/raw/            # Folder hierarchy: YYYY-MM-DD/AIRFIELD_CODE/
│   └── <IGC files and logbook JSON>
├── igc_flight_analysis.db  # SQLite database (auto-created)
├── uv.toml              # UV dependency configuration
└── README.dev.md        # This file
```

# 📡 Scraper: scraper/fetcher.py

- Targets multiple airfields (e.g. EKGL, EKAB, EKTRU)

- Calls: https://flightbook.glidernet.org/api/logbook/{AIRFIELD}/

- Downloads .igc files using:

```python
https://flightbook.glidernet.org/api/live/igc/{DEVICE_ID}/{START_TSP}/{STOP_TSP}?date={YYYY-MM-DD}
```

- Saves to: data/raw/YYYY-MM-DD/AIRFIELD_CODE/


# 🗃️ Database Schema (db/models.py)

| Table            | Grain                    | Purpose                           |
| ---------------- | ------------------------ | --------------------------------- |
| `AirfieldReport` | 1 row per airfield/day   | Wraps full logbook JSON           |
| `Device`         | 1 row per tracker device | Aircraft metadata                 |
| `Flight`         | 1 row per flight         | Links to report + device          |
| `IGCFile`        | 1 per downloaded flight  | File location of `.igc`           |
| `IngestionLog`   | 1 per run per airfield   | Tracks success, skips, and errors |


The SQLite database is created via Base.metadata.create_all(engine).

# 🔄 Ingestion: scripts/ingest_scraped_data.py

- Loops through data/raw/YYYY-MM-DD/*/

- Skips ingestion if that airfield/date already exists in AirfieldReport

- Populates Flight, Device, and IGCFile

- Logs result in IngestionLog

# 🖥️ Streamlit App: app/main.py

- Filters by date and airfield (dropdowns)

- Displays flights in a table

- Parses .igc files manually (no external libs)

- Extracts lat/lon from B records

- Plots tracks using st.map() with selectable flights

```python
{"lat": 55.8834, "lon": 12.2361}
```

Future upgrade path includes pydeck or Folium for line/path visualizations.

# ⚠️ Constraints

- No backfill: The API only returns today’s data.

- .igc files must be downloaded the same day.

- Use Task Scheduler (or cron) to automate fetcher.py + ingest_scraped_data.py.

# 🚀 Developer TODOs

- Replace st.map() with pydeck.Chart for colored paths

- Add altitude profile (barometric or GPS)

- Visualize tows between aircraft (Flight.tow_id)

- Add flight duration histogram or summary stats

- Enable file download directly from Streamlit

- Optional Postgres support

# 🧪 Testing & Debugging

To test ingestion manually:

´´´bash
uv venv && uv pip install -r uv.toml
python -m scripts.ingest_scraped_data
´´´

To run the app:

```bash
streamlit run app/main.py
```

To test .igc parsing:

```python
from app.main import extract_latlon_from_igc
print(extract_latlon_from_igc("path/to/flight.igc"))
```
