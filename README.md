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

- Investigate upwards movement.

- Investigate circling diameter

- Plot heatmap of thermals



