import json
from pathlib import Path
from datetime import datetime, date
import getpass

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db.models import Base, AirfieldReport, Device, Flight, IGCFile, IngestionLog

# Constants
RUN_DATE = date.today().isoformat()  # e.g., "2025-06-18"
BASE_DIR = Path("data/raw") / RUN_DATE
USERNAME = getpass.getuser()

# DB setup
engine = create_engine("sqlite:///igc_flight_analysis.db")
Session = sessionmaker(bind=engine)

# Loop over airfields (folders inside date folder)
for airfield_path in BASE_DIR.iterdir():
    if not airfield_path.is_dir():
        continue

    code = airfield_path.name
    logbook_path = airfield_path / f"logbook_{code}_{RUN_DATE}.json"

    if not logbook_path.exists():
        print(f"⚠️ Missing logbook for {code}. Skipping.")
        continue

    with open(logbook_path, "r", encoding="utf-8") as f:
        logbook = json.load(f)

    session = Session()
    report_date = datetime.strptime(logbook["date"], "%Y-%m-%d").date()

    # Skip if already ingested
    existing = session.query(AirfieldReport).filter_by(
        airfield_code=code, date=report_date
    ).first()

    if existing:
        session.add(IngestionLog(
            airfield_code=code,
            date=report_date,
            status="skipped",
            message="Already ingested.",
            run_by=USERNAME
        ))
        session.commit()
        session.close()
        print(f"⏩ Skipped {code} — already ingested.")
        continue

    try:
        # Insert report
        report = AirfieldReport(
            airfield_code=code,
            date=report_date,
            report_json=logbook
        )
        session.add(report)
        session.commit()

        # Insert devices
        devices = logbook.get("devices", [])
        device_map = {}
        for idx, dev in enumerate(devices):
            device = Device(
                address=dev["address"],
                registration=dev.get("registration"),
                aircraft=dev.get("aircraft"),
                competition=dev.get("competition"),
                device_type=dev.get("device_type"),
                db_org=dev.get("db_org"),
                identified=dev.get("identified", False)
            )
            session.merge(device)
            device_map[idx] = dev["address"]

        session.commit()

        # Insert flights
        flights = logbook.get("flights", [])
        for flight in flights:
            device_address = device_map[flight["device"]]
            start = flight["start_tsp"]
            stop = flight["stop_tsp"]

            f = Flight(
                device_address=device_address,
                report_id=report.id,
                start_tsp=start,
                stop_tsp=stop,
                start_time=flight.get("start"),
                stop_time=flight.get("stop"),
                duration_sec=flight.get("duration"),
                max_alt=flight.get("max_alt"),
                max_height=flight.get("max_height"),
                towing=flight.get("towing"),
                tow_id=None,
                warn=flight.get("warn", False)
            )
            session.add(f)
            session.flush()  # get f.id

            # Add IGC file if exists
            filename = f"{device_address}_{start}_{stop}.igc"
            igc_path = airfield_path / filename
            if igc_path.exists():
                session.add(IGCFile(
                    flight_id=f.id,
                    file_path=str(igc_path.relative_to("data")),
                    downloaded_at=datetime.now()
                ))

        session.add(IngestionLog(
            airfield_code=code,
            date=report_date,
            status="success",
            message=f"Ingested {len(flights)} flights and {len(devices)} devices.",
            run_by=USERNAME
        ))

        session.commit()
        print(f"✅ Ingested {code}: {len(flights)} flights")

    except Exception as e:
        session.rollback()
        session.add(IngestionLog(
            airfield_code=code,
            date=report_date,
            status="error",
            message=str(e),
            run_by=USERNAME
        ))
        session.commit()
        print(f"❌ Error ingesting {code}: {e}")

    finally:
        session.close()
