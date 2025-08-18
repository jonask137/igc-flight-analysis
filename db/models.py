from sqlalchemy import (
    create_engine, Column, Integer, String, Boolean, Date, DateTime, Text, ForeignKey, JSON
)
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()


class AirfieldReport(Base):
    __tablename__ = "airfield_reports"

    id = Column(Integer, primary_key=True)
    airfield_code = Column(String, nullable=False)
    date = Column(Date, nullable=False)
    report_json = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    flights = relationship("Flight", back_populates="report")


class Device(Base):
    __tablename__ = "devices"

    address = Column(String, primary_key=True)
    registration = Column(String)
    aircraft = Column(String)
    competition = Column(String)
    device_type = Column(String)
    db_org = Column(String)
    identified = Column(Boolean)

    flights = relationship("Flight", back_populates="device")


class Flight(Base):
    __tablename__ = "flights"

    id = Column(Integer, primary_key=True)
    device_address = Column(String, ForeignKey("devices.address"), nullable=False)
    report_id = Column(Integer, ForeignKey("airfield_reports.id"), nullable=False)

    start_tsp = Column(Integer, nullable=False)
    stop_tsp = Column(Integer, nullable=True)  # Allow NULL for outlanded flights
    start_time = Column(String)
    stop_time = Column(String)
    duration_sec = Column(Integer)
    max_alt = Column(Integer)
    max_height = Column(Integer)
    towing = Column(Boolean)
    tow_id = Column(Integer, ForeignKey("flights.id"), nullable=True)
    warn = Column(Boolean)

    device = relationship("Device", back_populates="flights")
    report = relationship("AirfieldReport", back_populates="flights")
    igc_file = relationship("IGCFile", back_populates="flight", uselist=False)
    tow_flight = relationship("Flight", remote_side=[id])


class IGCFile(Base):
    __tablename__ = "igc_files"

    id = Column(Integer, primary_key=True)
    flight_id = Column(Integer, ForeignKey("flights.id"), nullable=False)
    file_path = Column(Text, nullable=False)
    downloaded_at = Column(DateTime, default=datetime.utcnow)

    flight = relationship("Flight", back_populates="igc_file")

class IngestionLog(Base):
    __tablename__ = "ingestion_log"

    id = Column(Integer, primary_key=True)
    airfield_code = Column(String, nullable=False)
    date = Column(Date, nullable=False)
    status = Column(String, nullable=False)
    message = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)
    run_by = Column(String, default="auto")  # you can override this in script

# Create the SQLite database
if __name__ == "__main__":
    engine = create_engine("sqlite:///igc_flight_analysis.db")
    Base.metadata.create_all(engine)
    print("✅ Database and tables created.")

