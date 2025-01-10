import serial
import threading
import re
import time
import logging
import sqlalchemy
from sqlalchemy import create_engine, Column, Float, Integer, String
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.exc import OperationalError
from datetime import datetime
from contextlib import contextmanager
import json
import os

# Setup logging
logger = logging.getLogger('serialLogger')
logger.setLevel(logging.INFO)

# File handlers
info_handler = logging.FileHandler('info_log.txt')
error_handler = logging.FileHandler('serial_log.txt')

# Set levels
info_handler.setLevel(logging.INFO)
error_handler.setLevel(logging.ERROR)

# Formatters
formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
info_handler.setFormatter(formatter)
error_handler.setFormatter(formatter)

# Add handlers
logger.addHandler(info_handler)
logger.addHandler(error_handler)

# Initialize global variables
bef = 0
count = 1
prevCount = 0
buffer = ""
Arbffr = [[]]
thickness = ""
diameter = ""
hardness = ""
time_series = ""
last_error_message = None
local_data_file = 'local_data.json'

# Get the current date in the desired format
tanggal_waktu_terformat = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

# Database configuration
db_url = "postgresql://user:password@localhost:5432/mydatabase"
engine = create_engine(db_url, pool_pre_ping=True)
Base = declarative_base()

# Database models
class Data(Base):
    __tablename__ = 'ipc_staging'
    id_setup = Column(Integer, primary_key=True)
    h_value = Column(Float)
    d_value = Column(Float)
    t_value = Column(Float)
    status = Column(String)
    code_instrument = Column(String)
    time_series = Column(Integer)

    @classmethod
    def kirim_data(cls, h_value, d_value, t_value, status, code_instrument, time_series):
        try:
            with session_scope() as session:
                data_baru = cls(h_value=h_value, d_value=d_value, t_value=t_value, status=status, code_instrument=code_instrument, time_series=time_series)
                session.add(data_baru)
                session.commit()
        except OperationalError:
            # Save to local file if the PostgreSQL connection fails
            save_to_local_file(h_value, d_value, t_value, status, code_instrument, time_series)

class Log(Base):
    __tablename__ = 'error_log'
    Id = Column(Integer, primary_key=True)
    error = Column(String)
    time = Column(String)

    @classmethod
    def kirim_log(cls, error, time):
        with session_scope() as session:
            lognya = cls(error=error, time=time)
            session.add(lognya)

# Session management
Session = sessionmaker(bind=engine)

@contextmanager
def session_scope():
    session = Session()
    try:
        yield session
        session.commit()
    except OperationalError:
        session.rollback()
        # Log the reconnection attempt
        logger.error("Database connection lost. Attempting to reconnect...")
        # Try to reconnect
        engine.dispose()
        session.bind = engine.connect()
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

# Save data to local file
def save_to_local_file(h_value, d_value, t_value, status, code_instrument, time_series):
    data = {
        "h_value": h_value,
        "d_value": d_value,
        "t_value": t_value,
        "status": status,
        "code_instrument": code_instrument,
        "time_series": time_series
    }
    if os.path.exists(local_data_file):
        with open(local_data_file, 'r') as file:
            local_data = json.load(file)
    else:
        local_data = []

    local_data.append(data)

    with open(local_data_file, 'w') as file:
        json.dump(local_data, file)

# Retry sending data from local file to PostgreSQL
def retry_sending_local_data():
    if not os.path.exists(local_data_file):
        return

    with open(local_data_file, 'r') as file:
        local_data = json.load(file)

    if not local_data:
        return

    for data in local_data:
        try:
            Data.kirim_data(data["h_value"], data["d_value"], data["t_value"], data["status"], data["code_instrument"], data["time_series"])
            local_data.remove(data)
        except OperationalError:
            break  # If the connection fails, stop retrying and wait for the next attempt

    with open(local_data_file, 'w') as file:
        json.dump(local_data, file)

# Initialize serial port
serial_port = None

def close_serial():
    global serial_port
    if serial_port and serial_port.is_open:
        serial_port.close()
        logger.info("Serial port closed.")

def initialize_serial():
    global serial_port, tanggal_waktu_terformat, last_error_message
    base_delay = 5  # seconds
    attempt = 0

    while True:
        try:
            serial_port = serial.Serial(port="COM4", baudrate=9600, timeout=1)
            serial_port.reset_input_buffer()
            logger.info(f"Serial connection established on {serial_port.port} with baudrate {serial_port.baudrate} at {tanggal_waktu_terformat}")
            error_message = f"ESTABLISHED {serial_port.port} at {tanggal_waktu_terformat}"
            Log.kirim_log(error=error_message, time=tanggal_waktu_terformat)
            time.sleep(2)
            break
        except serial.SerialException as e:
            error_message = f"Serial FAILED: {e}"
            logger.error(error_message)
            if last_error_message != error_message:
                Log.kirim_log(error=error_message, time=tanggal_waktu_terformat)
                last_error_message = error_message
            attempt += 1
            retry_delay = base_delay * (2 ** (attempt - 1))  # Exponential backoff
            time.sleep(retry_delay)
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            break

initialize_serial()

class SerialReader:
    def __init__(self):
        self.thread = threading.Thread(target=self._read_thread)
        self.thread.daemon = True

    def start(self):
        self.thread.start()

    def _read_thread(self):
        global serial_port, bef, buffer, Arbffr, prevCount, tanggal_waktu_terformat, last_error_message
        while True:
            try:
                if serial_port is None:
                    initialize_serial()
                    continue
                line = serial_port.readline().decode(encoding='UTF-8', errors='replace')
                if line:
                    buffer += line
                    if bef == 0:
                        bef = 1
                        buffer = ""
                    else:
                        bef = 1
                else:
                    if bef == 1:
                        data = re.split(r"\s+|\n", buffer)
                        if "Testing" in data:
                            try:
                                dataindex = data.index("Results")
                                batch = data[22]
                                speed = data[24]
                                Tanggal = data[28]
                                Time = data[30]
                                no = data[48]
                                thickness = float(data[dataindex+4])
                                diameter = float(data[dataindex+7])
                                hardness = float(data[dataindex+10])
                                count = int(no)
                                Arbffr[prevCount].append(no)
                                Arbffr[prevCount].append(batch)
                                Arbffr[prevCount].append(speed)
                                Arbffr[prevCount].append(Tanggal)
                                Arbffr[prevCount].append(Time)
                                Arbffr[prevCount].append(thickness)
                                Arbffr[prevCount].append(diameter)
                                Arbffr[prevCount].append(hardness)
                                prevCount = count
                                buffer = ""
                                Data.kirim_data(hardness, diameter, thickness, "N", "A20230626002", time_series=no)
                                with open("data_log.txt", "a") as file:
                                    file.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')}: {no}, {thickness}, {diameter}, {hardness}, {Tanggal}, {tanggal_waktu_terformat}\n")
                            except (ValueError, IndexError) as conversion_error:
                                error_message = f"Data CONVERSION: {conversion_error}"
                                logger.error(error_message)
                                if last_error_message != error_message:
                                    Log.kirim_log(error=error_message, time=tanggal_waktu_terformat)
                                    last_error_message = error_message
                                bef = 0
                                buffer = ""
                                prevCount = 0
                                count = 1
                                data = ""
                                Arbffr = [[]]
                        elif "No." in data and len(data) < 20:
                            try:
                                dataindex = data.index("mm")
                                no = data[1]
                                thickness = float(data[dataindex-1])
                                diameter = float(data[dataindex+2])
                                hardness = float(data[dataindex+5])
                                count = int(no)
                                Arbffr.append([])
                                Arbffr[prevCount].append(no)
                                Arbffr[prevCount].append(batch)
                                Arbffr[prevCount].append(speed)
                                Arbffr[prevCount].append(Tanggal)
                                Arbffr[prevCount].append(Time)
                                Arbffr[prevCount].append(thickness)
                                Arbffr[prevCount].append(diameter)
                                Arbffr[prevCount].append(hardness)
                                prevCount = count
                                buffer = ""
                                with open("data_log.txt", "a") as file:
                                    file.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')}: {no}, {thickness}, {diameter}, {hardness}, {Tanggal}, {tanggal_waktu_terformat}\n")
                                Data.kirim_data(hardness, diameter, thickness, "N", "A20230626002", time_series=no)
                            except (ValueError, IndexError) as conversion_error:
                                bef = 0
                                buffer = ""
                                prevCount = 0
                                count = 1
                                data = ""
                                Arbffr = [[]]
                        elif "Xm" in data or "Xmean" in data or "Released:" in data:
                            bef = 0
                            buffer = ""
                            prevCount = 0
                            count = 1
                            data = ""
                            time.sleep(5)
                            Arbffr = [[]]
            except serial.SerialException as e:
                error_message = f"Serial exception: {e}"
                logger.error(error_message)
                if last_error_message != error_message:
                    Log.kirim_log(error=error_message, time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                    last_error_message = error_message
                serial_port = None
                time.sleep(5)
            except Exception as e:
                error_message = f"Unexpected error: {e}"
                logger.error(error_message)
                if last_error_message != error_message:
                    Log.kirim_log(error=error_message, time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                    last_error_message = error_message
                time.sleep(5)

if __name__ == "__main__":
    Reading = SerialReader()
    Reading.start()
    while True:
        retry_sending_local_data()  # Attempt to send any locally stored data
        h_value = hardness
        d_value = diameter
        t_value = thickness
        status = ""
        code_instrument = "A20230626002"
        created_date = tanggal_waktu_terformat
        if hardness != "":
            with open("data_log.txt", "a") as file:
                file.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')}: {Arbffr}\n")
                file.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')}: {time_series}, {thickness}, {diameter}, {hardness}, {tanggal_waktu_terformat}\n")
        time.sleep(60)