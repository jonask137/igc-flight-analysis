# 🛩️ IGC Flight Analysis

This project provides a full pipeline for collecting, storing, analyzing, and visualizing IGC (International Gliding Commission) flight logs. It includes:

- 🔄 Daily scraping of IGC files
- 🧊 Local storage and database integration
- 📈 Tools for plotting flight paths and altitude profiles
- 🌐 A Streamlit web app for interactive exploration


## 📁 Project Structure

```
igc-flight-analysis/
├── app/ # Streamlit frontend
├── data/ # Raw and processed IGC files
├── db/ # Database schema and utilities
├── notebooks/ # Optional Jupyter notebooks for EDA
├── plotting/ # Plotting utilities (matplotlib, etc.)
├── scraper/ # Daily scraper for IGC files
├── scripts/ # CLI jobs (e.g. daily ingest)
├── tests/ # Unit tests
├── uv.toml # UV project config
└── README.md # You're here!
```

## 🚀 Getting Started

### 1. Clone the Repo

```bash
git clone https://github.com/your-username/igc-flight-analysis.git
cd igc-flight-analysis
```

### 2. Set Up the Environment

```bash
uv init
uv pip install matplotlib pandas numpy streamlit sqlalchemy
```

### 3. Run the Streamlit App

```bash
streamlit run app/main.py
```

# 🔄 Daily IGC Scraping

A daily job (scraper/fetcher.py) pulls new .igc flight logs from your configured source and stores them in data/raw/. You can automate it with scripts/ingest_daily.ps1.

To run manually:

```bash
python scraper/fetcher.py
```

# 🗄️ Database

Flights are stored in a local SQLite or PostgreSQL database defined in db/models.py. This allows metadata querying, performance filtering, and versioned records.

# 📊 Plotting & Analysis

Use plotting/visualizer.py to:

Plot flight paths (latitude vs longitude)

Show altitude over time (barometric and GPS)

Detect takeoff/landing, thermals, or flight segments

# 🧪 Testing

Basic unit tests are in tests/. To run:


# 📌 TODO

- Use libigc for storing the flight tracker data. Link flight tracks on date, device, start_tsp and stop_tsp.
    - see flight tracks notebook. we can extract the tracks, get thermal and glide stats. This can be persisted to a table. We can relate it to the rest of the database using the file name. this will always be a unique identifier.
    - create delta logic to ingest flight tracks. and thermal + glide stats.

- Create dbt project for prepping the data for analysis. https://docs.getdbt.com/docs/core/connect-data-platform/sqlite-setup

- Add github actions to trigger the scraper and ingest jobs


