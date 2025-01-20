import serial
import threading
import re
import time
import logging
import sqlalchemy
from sqlalchemy import create_engine, Column, Float, Integer, String
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', 
                    handlers=[logging.FileHandler("serial_data.txt"), logging.StreamHandler()])
error_log = set()

# Define the database model
Base = declarative_base()

class Data(Base):
    __tablename__ = 'sakaplant_prod_ipc_staging'
    id_setup = Column(Integer, primary_key=True, autoincrement=True)
    h_value = Column(Float)
    d_value = Column(Float)
    t_value = Column(Float)
    status = Column(String)
    code_instrument = Column(String)
    time_series = Column(Integer)

# Database setup
DATABASE_URL = "postgresql://users_pims_engineer:Engineer_2023@10.106.1.40/pims_prod"
engine = create_engine(DATABASE_URL)
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()

# Serial port setup
SERIAL_PORT = 'COM3'  # Change to your serial port
BAUD_RATE = 9600

def parse_data(raw_data):
    raw_data = re.sub(r"-{2,}", "", raw_data).strip()
    lines = [line.strip() for line in raw_data.split("\n") if line.strip()]

    # Extract entries
    entries = []
    for line in lines:
        if line.startswith("No."):
            match = re.match(r'No\.\s*(\d+)\s*:\s*([\d.]+) mm\s*:\s*([\d.]+) mm\s*:\s*([\d.]+) kp', line)
            if match:
                time_series = int(match.group(1))
                t_value = float(match.group(2))
                d_value = float(match.group(3))
                h_value = float(match.group(4))
                entries.append((time_series, t_value, d_value, h_value))
    return entries

def log_error_once(error_message):
    if error_message not in error_log:
        logging.error(error_message)
        error_log.add(error_message)

def log_serial_data(data):
    current_time = datetime.now()
    log_entry = {
        'h_value': data.h_value,
        'd_value': data.d_value,
        't_value': data.t_value,
        'status': data.status,
        'code_instrument': data.code_instrument,
        'time_series': data.time_series,
        'time_insert': current_time.strftime('%H:%M:%S'),
        'created_date': current_time.strftime('%Y-%m-%d')
    }
    logging.info(f"{current_time.strftime('%Y-%m-%d %H:%M:%S')}: {log_entry}")

    # Log to local file in the desired format
    with open("local_serial_data_log.txt", "a") as f:
        f.write(f"{current_time.strftime('%Y-%m-%d %H:%M:%S')}: {log_entry}\n")

def read_from_serial():
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
    while True:
        try:
            raw_data = ser.readline().decode('utf-8').strip()
            if raw_data:
                logging.info(f"Raw data received: {raw_data}")
                parsed_entries = parse_data(raw_data)
                for entry in parsed_entries:
                    time_series, t_value, d_value, h_value = entry
                    data_entry = Data(
                        # id_setup=time_series,
                        h_value=h_value,
                        d_value=d_value,
                        t_value=t_value,
                        status='N',
                        code_instrument='A20230626002',  # Example code instrument
                        time_series=time_series
                    )
                    session.add(data_entry)
                    session.commit()
                    logging.info(f"Data committed to database: {data_entry}")
                    log_serial_data(data_entry)
        except Exception as e:
            log_error_once(f"Error reading from serial port: {e}")
        time.sleep(1)

if __name__ == "__main__":
    serial_thread = threading.Thread(target=read_from_serial)
    serial_thread.daemon = True
    serial_thread.start()

    while True:
        try:
            time.sleep(1)
        except KeyboardInterrupt:
            logging.info("Shutting down...")
            break