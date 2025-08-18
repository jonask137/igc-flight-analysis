import json
from pathlib import Path
from datetime import datetime, date, timedelta
import getpass
import argparse

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db.models import Base, AirfieldReport, Device, Flight, IGCFile, IngestionLog

#### NOTE:
# Hvis de ikke har en afslutning lægges de ikke ind i databasen. Vi så d. 4 August at mange piloter landede ude til SAC. Disse vil ikke blive indlæst. Vi skal finde en måde at håndtere disse på.

# Parse arguments for development purposes
parser = argparse.ArgumentParser(description="Ingest flight data into the database.")
parser.add_argument("--start-date", type=str, help="Specify the start date (YYYY-MM-DD).")
parser.add_argument("--end-date", type=str, help="Specify the end date (YYYY-MM-DD).")
parser.add_argument("--airport", type=str, help="Specify the airport code. Default is all airports.")
args = parser.parse_args()

# Use the provided date range or default values
START_DATE = args.start_date
END_DATE = args.end_date
SPECIFIC_AIRPORT = args.airport

if START_DATE and END_DATE:
    date_range = [datetime.strptime(START_DATE, "%Y-%m-%d").date() + timedelta(days=i) 
                  for i in range((datetime.strptime(END_DATE, "%Y-%m-%d").date() - datetime.strptime(START_DATE, "%Y-%m-%d").date()).days + 1)]
else:
    date_range = [date.today()]

USERNAME = getpass.getuser()

for RUN_DATE in date_range:
    BASE_DIR = Path("data/raw") / RUN_DATE.isoformat()
    
    if not BASE_DIR.exists():
        print(f"⚠️ Skipping date {RUN_DATE.isoformat()} as no files exist.")
        continue

    print(f"🚀 Running ingestion for date: {RUN_DATE}, airport: {SPECIFIC_AIRPORT or 'all'}")

    # DB setup
    engine = create_engine("sqlite:///igc_flight_analysis.db")
    Session = sessionmaker(bind=engine)

    # Loop over airfields (folders inside date folder)
    for airfield_path in BASE_DIR.iterdir():
        if not airfield_path.is_dir():
            continue

        code = airfield_path.name

        # Skip if specific airport is set and doesn't match
        if SPECIFIC_AIRPORT and code != SPECIFIC_AIRPORT:
            continue

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
            print(f"🔄 Reloading flights for {code} on {report_date}...")
            # Remove existing flights linked to the report
            session.query(Flight).filter_by(report_id=existing.id).delete()
            session.query(IGCFile).filter(IGCFile.flight_id.in_(
                session.query(Flight.id).filter_by(report_id=existing.id)
            )).delete()
            session.commit()

        try:
            # Check if report already exists
            existing_report = session.query(AirfieldReport).filter_by(
                airfield_code=code, date=report_date
            ).first()
            if existing_report:
                print(f"🔄 Deleting existing report for {code} on {report_date}...")
                session.delete(existing_report)
                session.commit()

            # Insert new report
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
            skipped_flights = 0
            for flight in flights:
                if not flight.get("start_tsp"):
                    print(f"⚠️ Skipping flight without start time: {flight}")
                    skipped_flights += 1
                    continue

                if not flight.get("stop_tsp"):
                    print(f"⚠️ Skipping flight without end time: {flight}")
                    skipped_flights += 1
                    continue

                device_address = device_map[flight["device"]]
                start = flight["start_tsp"]
                stop = flight["stop_tsp"]

                # Skip if flight already ingested
                existing_flight = session.query(Flight).filter_by(
                    device_address=device_address,
                    start_tsp=start,
                    stop_tsp=stop
                ).first()
                if existing_flight:
                    print(f"⏩ Skipping already ingested flight: {flight}")
                    skipped_flights += 1
                    continue

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

            # Add warning to log
            if skipped_flights > 0:
                session.add(IngestionLog(
                    airfield_code=code,
                    date=report_date,
                    status="warning",
                    message=f"Skipped {skipped_flights} flights without end time.",
                    run_by=USERNAME
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
