import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))

import streamlit as st
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from db.models import Base, AirfieldReport, Device, Flight, IGCFile
from datetime import datetime

def extract_latlon_from_igc(path):
    coords = []

    def convert_lat_lon(value, direction):
        try:
            if direction in ['N', 'S']:
                degrees = int(value[:2])
                minutes = float(value[2:]) / 60000.0
            else:
                degrees = int(value[:3])
                minutes = float(value[3:]) / 60000.0
            coord = degrees + minutes
            if direction in ['S', 'W']:
                coord *= -1
            return coord
        except Exception:
            return None

    try:
        with open(path, "r", encoding="utf-8") as file:
            for line in file:
                if not line.startswith("B"):
                    continue
                lat_raw = line[7:14]
                lat_dir = line[14]
                lon_raw = line[15:23]
                lon_dir = line[23]

                lat = convert_lat_lon(lat_raw, lat_dir)
                lon = convert_lat_lon(lon_raw, lon_dir)

                if isinstance(lat, float) and isinstance(lon, float):
                    coords.append({"lat": lat, "lon": lon})
    except Exception as e:
        print(f"Error parsing IGC file {path}: {e}")
    return coords



# --- DB SETUP ---
engine = create_engine("sqlite:///igc_flight_analysis.db")
Session = sessionmaker(bind=engine)
session = Session()

# --- PAGE CONFIG ---
st.set_page_config(page_title="IGC Flight Browser", layout="wide")
st.title("🛩️ Recorded Glider Flights")

# --- FILTERS ---
dates = session.query(AirfieldReport.date).distinct().order_by(AirfieldReport.date.desc()).all()
date_options = [d[0] for d in dates]
selected_date = st.selectbox("Select flight date", date_options)

airfields = session.query(AirfieldReport.airfield_code).distinct().order_by(AirfieldReport.airfield_code).all()
airfield_options = [a[0] for a in airfields]
selected_airfield = st.selectbox("Select airfield", airfield_options)

# --- QUERY FLIGHTS ---
flights = (
    session.query(Flight, Device, IGCFile)
    .join(Device, Flight.device_address == Device.address)
    .outerjoin(IGCFile, IGCFile.flight_id == Flight.id)
    .join(AirfieldReport, Flight.report_id == AirfieldReport.id)
    .filter(AirfieldReport.date == selected_date)
    .filter(AirfieldReport.airfield_code == selected_airfield)
    .all()
)

# --- DISPLAY ---
st.write(f"### Found {len(flights)} flights for **{selected_airfield}** on **{selected_date}**")

if flights:
    flight_data = []
    for flight, device, igc_file in flights:
        flight_data.append({
            "Registration": device.registration,
            "Aircraft": device.aircraft,
            "Competition": device.competition,
            "Start Time": flight.start_time,
            "Stop Time": flight.stop_time,
            "Duration (min)": round((flight.duration_sec or 0) / 60, 1),
            "Max Alt (m)": flight.max_alt,
            "IGC File": f"[Download](/data/{igc_file.file_path})" if igc_file else "N/A"
        })

    st.dataframe(flight_data, use_container_width=True)
else:
    st.info("No flights recorded for this selection.")

session.close()


st.write("### Flight Tracks on Map")

# Let user pick flights to show on the map
track_options = [f"{device.registration} {flight.start_time}-{flight.stop_time}" for flight, device, igc_file in flights]
selected_tracks = st.multiselect("Select flights to show on map", track_options, default=track_options)

map_points = []

for (flight, device, igc_file), label in zip(flights, track_options):
    if label not in selected_tracks or not igc_file:
        continue

    igc_path = Path("data") / igc_file.file_path
    latlon = extract_latlon_from_igc(igc_path)

    # Validate each point
    for point in latlon:
        if (
            isinstance(point, dict)
            and isinstance(point.get("lat"), float)
            and isinstance(point.get("lon"), float)
        ):
            map_points.append(point)

st.write("Map preview (first 5 points):", map_points[:5])

if map_points:
    st.map(map_points)
else:
    st.info("No track data available to display.")