import requests
import os
import json
from datetime import date
from pathlib import Path

# Multiple airfields supported
AIRFIELDS = ["EKGL", "EKAB", "EKTRU", "EKBH", "EKHM", "EKSA", "EKVH", "EKVB", "EKEL", "EKFRE", "EKFRS", "EKKS", "EKSL"]
BASE_URL = "https://flightbook.glidernet.org/api"
TODAY = date.today().isoformat()  # e.g., '2025-06-18'

for code in AIRFIELDS:
    print(f"📡 Fetching logbook for {code}...")

    try:
        # Create save path
        save_dir = Path("data/raw") / TODAY / code
        save_dir.mkdir(parents=True, exist_ok=True)

        # Step 1: Fetch daily logbook
        logbook_url = f"{BASE_URL}/logbook/{code}/"
        response = requests.get(logbook_url)
        response.raise_for_status()
        logbook = response.json()

        # Step 2: Save raw JSON
        json_path = save_dir / f"logbook_{code}_{TODAY}.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(logbook, f, indent=2)

        # Step 3: Parse and download IGC files
        flights = logbook.get("flights", [])
        devices = logbook.get("devices", [])
        print(f"🛩️ Found {len(flights)} flights for {code}...")

        for flight in flights:
            device_idx = flight["device"]
            device = devices[device_idx]
            device_id = device["address"]
            start = flight["start_tsp"]
            stop = flight["stop_tsp"]

            igc_url = f"{BASE_URL}/live/igc/{device_id}/{start}/{stop}?date={TODAY}"
            igc_response = requests.get(igc_url)

            if igc_response.status_code == 200:
                filename = f"{device_id}_{start}_{stop}.igc"
                with open(save_dir / filename, "w", encoding="utf-8") as f:
                    f.write(igc_response.text)
                print(f"✅ Saved {filename}")
            else:
                print(f"⚠️ Failed to fetch IGC for {device_id} [{start}–{stop}] - Status {igc_response.status_code}")

    except Exception as e:
        print(f"❌ Error fetching {code}: {e}")
