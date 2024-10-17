import serial
import threading
import re
import time
import json
from sqlalchemy import create_engine, Column, Float, Integer, String
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

# Inisialisasi SQLAlchemy
db_url = 'mysql+mysqlconnector://root:password@localhost:3306/kalbe'
engine = create_engine(db_url)
Base = declarative_base()

# Model untuk tabel machine_1
class Data(Base):
    __tablename__ = 'raspberry'
    id_setup = Column(Integer, primary_key=True)
    h_value = Column(Float)
    d_value = Column(Float)
    t_value = Column(Float)
    status = Column(String)
    code_instrument = Column(String)

# Membuat sesi untuk koneksi ke database
Session = sessionmaker(bind=engine)
session = Session()

def initialize_serial():
    global serial_port
    while True:
        try:
            serial_port = serial.Serial(port="/dev/ttyACM0", baudrate=9600, timeout=1)
            serial_port.reset_input_buffer()
            print("Serial connection established.")
            break
        except serial.SerialException as e:
            print(f"Serial connection failed: {e}")
            time.sleep(5)  # Wait for 5 seconds before attempting to reconnect

def initialize_database():
    global engine, session
    try:
        engine = create_engine(db_url)
        Session = sessionmaker(bind=engine)
        session = Session()
        print("Database connection established.")
    except Exception as e:
        print(f"Database connection failed: {e}")
        time.sleep(5)  # Wait for 5 seconds before attempting to reconnect
        initialize_database()  # Try to reconnect

initialize_serial()  # Initialize the serial connection
initialize_database()  # Initialize the database connection

class SerialReader:
    
    def __init__(self):
        self.thread = threading.Thread(target=self._read_thread)
        self.thread.daemon = True
        self.buffer = ""  # Added buffer initialization here
        self.prevCount = 0  # Keep track of the last processed data
        self.Arbffr = [[]]  # Store parsed data for batch processing
    
    def start(self):
        self.thread.start()

    def _read_thread(self):
        global serial_port
        while True:
            try:
                if serial_port is None:
                    initialize_serial()
                    continue

                line = serial_port.readline().decode(encoding='UTF-8', errors='replace').strip()

                if line:
                    self.buffer += line
                    print(f"Raw serial data: {line}")  # For debugging
                    
                    if "Testing" in line:
                        self.process_full_data(self.buffer)
                        self.buffer = ""  # Clear buffer after processing

                    elif "No." in line:
                        self.process_partial_data(self.buffer)
                        self.buffer = ""

                    elif "Xm" in line or "Xmean" in line or "Released:" in line:
                        self.reset_buffer()  # Reset everything when finalizing a batch

            except serial.SerialException as e:
                print(f"Serial exception: {e}")
                serial_port = None  # Set serial_port to None to trigger reconnection
                time.sleep(5)

    def process_full_data(self, buffer):
        try:
            data = re.split(r"\s+|\n", buffer)
            batch = data[22]
            speed = data[24]
            Tanggal = data[28]
            Time = data[30]
            no = data[48]
            thickness = data[50]
            diameter = data[53]
            hardness = data[56]

            count = int(no)
            self.Arbffr[self.prevCount] = [no, batch, speed, Tanggal, Time, thickness, diameter, hardness]
            self.prevCount = count

            print(f"Processed full data - Thickness: {thickness}, Diameter: {diameter}, Hardness: {hardness}")
            self.save_to_db(hardness, diameter, thickness)

        except IndexError as e:
            print(f"Error parsing full data: {e}")

    def process_partial_data(self, buffer):
        try:
            data = re.split(r"\s+|\n", buffer)
            no = data[1]
            thickness = data[3]
            diameter = data[6]
            hardness = data[9]

            count = int(no)
            self.Arbffr.append([no, "", "", "", "", thickness, diameter, hardness])
            self.prevCount = count

            print(f"Processed partial data - Thickness: {thickness}, Diameter: {diameter}, Hardness: {hardness}")
            self.save_to_db(hardness, diameter, thickness)

        except IndexError as e:
            print(f"Error parsing partial data: {e}")

    def save_to_db(self, hardness, diameter, thickness):
        try:
            new_data = Data(
                id_setup=self.prevCount,
                h_value=hardness,
                d_value=diameter,
                t_value=thickness,
                status="",
                code_instrument="025815"
            )
            session.add(new_data)
            session.commit()
            print(f"Data saved to database - Thickness: {thickness}, Diameter: {diameter}, Hardness: {hardness}")
        except Exception as e:
            session.rollback()
            print(f"Failed to save data to database: {e}")

    def reset_buffer(self):
        self.buffer = ""
        self.prevCount = 0
        self.Arbffr = [[]]
        print("Buffer reset for new batch")

def main():
    reader = SerialReader()
    reader.start()

if __name__ == '__main__':
    main()
