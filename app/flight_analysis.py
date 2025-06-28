import streamlit as st
from libigc import Flight
from pathlib import Path
from datetime import datetime

# --- PAGE CONFIG ---
st.set_page_config(page_title="Toy Example: libigc", layout="wide")
st.title("🎲 Toy Example: Using libigc")

# --- FILE SELECTION ---
st.write("Select an `.igc` file from the `data/raw` directory.")
data_dir = Path("data/raw")
available_files = list(data_dir.rglob("*.igc"))
file_options = [str(file.relative_to(data_dir)) for file in available_files]

selected_file = st.selectbox("Select IGC File", options=file_options)

if selected_file:
    try:
        # Parse the selected file
        file_path = data_dir / selected_file
        flight = Flight.create_from_file(file_path)

        if flight.valid:
            # Display basic flight information
            st.write("### Flight Information")
            st.write(f"Takeoff Time: {flight.takeoff_fix.timestamp}")
            st.write(f"Landing Time: {flight.landing_fix.timestamp}")
            st.write(f"Number of Thermals: {len(flight.thermals)}")

            # Display track points
            st.write("### Track Points")
            track_points = [
                {
                    "Timestamp": datetime.fromtimestamp(fix.timestamp),  # Convert timestamp to datetime
                    "Latitude": fix.lat,
                    "Longitude": fix.lon,
                    "Altitude": fix.alt,
                    "Ground Speed": fix.gsp,
                    "Bearing": fix.bearing,
                    "Bearing Change Rate": fix.bearing_change_rate,
                    "Flying": fix.flying,
                    "Circling": fix.circling,
                }
                for fix in flight.fixes
            ]
            st.dataframe(track_points)
        else:
            st.error("Flight is invalid")
            st.write("Reasons:", flight.notes)

    except Exception as e:
        st.error(f"Error parsing the file: {e}")
else:
    st.info("Please select an `.igc` file to begin.")
