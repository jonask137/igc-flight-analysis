import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))

import streamlit as st
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from db.models import Base, AirfieldReport, Device, Flight, IGCFile
from datetime import datetime
import pydeck as pdk  # Add pydeck for advanced map visualization

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

# Replace flight date selection with date range selection
start_date, end_date = st.date_input("Select date range", value=(min(date_options), max(date_options)))
selected_dates = [d for d in date_options if start_date <= d <= end_date]

airfields = session.query(AirfieldReport.airfield_code).distinct().order_by(AirfieldReport.airfield_code).all()
airfield_options = [a[0] for a in airfields]
selected_airfields = st.multiselect("Select airfields", airfield_options, default=airfield_options)

select_all_airfields = st.checkbox("Select All Airfields", value=False)
if select_all_airfields:
    selected_airfields = airfield_options

# Add registration search
registration_search = st.text_input("Search by registration", value="")

# --- QUERY FLIGHTS ---
flights = (
    session.query(Flight, Device, IGCFile)
    .join(Device, Flight.device_address == Device.address)
    .outerjoin(IGCFile, IGCFile.flight_id == Flight.id)
    .join(AirfieldReport, Flight.report_id == AirfieldReport.id)
    .filter(AirfieldReport.date.in_(selected_dates))
    .filter(AirfieldReport.airfield_code.in_(selected_airfields))
    .filter(Device.registration.like(f"%{registration_search}%") if registration_search else True)
    .all()
)

# --- DISPLAY ---
st.write(f"### Found {len(flights)} flights for **{selected_airfields}** on **{selected_dates}**")

if flights:
    flight_data = []
    flight_labels = []
    for flight, device, igc_file in flights:
        airfield_name = session.query(AirfieldReport.airfield_code).filter(AirfieldReport.id == flight.report_id).scalar()
        label = f"{device.registration} {flight.start_time}-{flight.stop_time}"
        flight_labels.append(label)
        flight_data.append({
            "Select": False,  # Checkbox column for selection
            "Registration": device.registration,
            "Aircraft": device.aircraft,
            "Competition": device.competition,
            "Start Time": flight.start_time,
            "Stop Time": flight.stop_time,
            "Duration (min)": round((flight.duration_sec or 0) / 60, 1),
            "Max Alt (m)": flight.max_alt,
            "Airfield": airfield_name,  # Retrieve airfield name from AirfieldReport
            "IGC File": f"[Download](/data/{igc_file.file_path})" if igc_file else "N/A"
        })

    # Add "Select All" checkbox
    select_all = st.checkbox("Select All Flights", value=False)
    if select_all:
        for row in flight_data:
            row["Select"] = True

    selected_rows = st.data_editor(flight_data, use_container_width=True)  # Correct method
    selected_tracks = [flight_labels[i] for i, row in enumerate(selected_rows) if row["Select"]]
else:
    st.info("No flights recorded for this selection.")
    selected_tracks = []

session.close()

st.write("### Flight Tracks on Map")

# Add a toggle for 2D/3D visualization
map_view_option = st.radio("Select Map View", options=["2D", "3D"], index=0)

# Allow user to adjust view angle when 3D is selected
pitch = st.slider("Adjust Pitch", min_value=0, max_value=90, value=50) if map_view_option == "3D" else 0
bearing = st.slider("Adjust Bearing", min_value=0, max_value=360, value=0) if map_view_option == "3D" else 0

map_layers = []

for (flight, device, igc_file), label in zip(flights, flight_labels):
    if label not in selected_tracks or not igc_file:
        continue

    igc_path = Path("data") / igc_file.file_path
    latlon = extract_latlon_from_igc(igc_path)

    # Validate and prepare points for visualization
    valid_points = [
        [point["lon"], point["lat"], point.get("alt", 0)]  # Include altitude for 3D visualization
        for point in latlon
        if isinstance(point, dict) and isinstance(point.get("lat"), float) and isinstance(point.get("lon"), float)
    ]

    if valid_points:
        # Add a layer for the flight track
        map_layers.append(
            pdk.Layer(
                "PathLayer",
                data=[{"path": valid_points, "registration": device.registration, "aircraft": device.aircraft}],
                get_path="path",
                width_scale=20,
                width_min_pixels=2,
                get_color=[255, 0, 0],  # Red color for the track
                pickable=True,
                elevation_scale=100 if map_view_option == "3D" else 0,  # Elevation for 3D view
                get_elevation="path[2]" if map_view_option == "3D" else None,  # Use altitude for 3D
            )
        )

if map_layers:
    # Adjust view state based on 2D/3D selection and user inputs
    view_state = pdk.ViewState(
        latitude=valid_points[0][1],
        longitude=valid_points[0][0],
        zoom=10,
        pitch=pitch,  # User-adjustable pitch
        bearing=bearing,  # User-adjustable bearing
    )
    deck = pdk.Deck(
        layers=map_layers,
        initial_view_state=view_state,
        tooltip={"html": "<b>Registration:</b> {registration}<br><b>Aircraft:</b> {aircraft}", "style": {"color": "white"}}
    )
    st.pydeck_chart(deck)
else:
    st.info("No track data available to display.")