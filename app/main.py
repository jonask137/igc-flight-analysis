import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))

import streamlit as st
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from db.models import Base, AirfieldReport, Device, Flight, IGCFile
from datetime import datetime

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
