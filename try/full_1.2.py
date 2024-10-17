import serial
import threading
import re
import time
import json
from sqlalchemy import create_engine, Column, Float, Integer, String
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
# Initialize global variables
bef = 0
count = 1
prevCount = 0
buffer = ""
Arbffr = [[]]
thickness= ""
diameter = ""
hardness= ""
# Get the current date in the desired format
tanggal_waktu_terformat = datetime.now().strftime('%Y-%m-%d')
# Konfigurasi koneksi ke database PostgreSQL
db_url = "postgresql://users_pims_engineer:Engineer_2023@10.106.1.40/pims_prod"
engine = create_engine(db_url)
# Buat kelas model untuk tabel data
Base = declarative_base()
# Define the Data class
class Data(Base):
    __tablename__ = 'sakaplant_prod_ipc_staging'
    id_setup = Column(Integer, primary_key=True)
    h_value = Column(Float)
    d_value = Column(Float)
    t_value = Column(Float)
    status = Column(String)
    code_instrument = Column(String)
    @classmethod
    def kirim_data(cls, h_value, d_value, t_value, status, code_instrument, ):
        try:
            data_baru = cls(h_value=h_value,
                            d_value=d_value,
                            t_value=t_value,
                            status=status,
                            code_instrument=code_instrument)
            session.add(data_baru)
            session.commit()
        except Exception as e:
            print(f"Database error: {e}")
            session.rollback()
            initialize_database() # Attempt to reconnect to the Database
            
Session = sessionmaker(bind=engine)
session = Session()
serial_port = None

def initialize_serial():
    global serial_port
    while True:
        try:
            serial_port = serial.Serial(port="/dev/ttyUSB0", baudrate=9600, timeout=1)
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
        initialize_database() # Try to reconnect
        
initialize_serial()  # Initialize the serial connection
initialize_database() # Initialize the database connection
class SerialReader:
    
    def __init__(self):
        self.thread = threading.Thread(target=self._read_thread)
        self.thread.daemon = True
    def start(self):
        self.thread.start()
    def _read_thread(self):
        global serial_port, bef, buffer, Arbffr, prevCount
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
                            batch = data[22]
                            speed = data[24]
                            Tanggal = data[28]
                            Time = data[30]
                            no = data[48]
                            thickness = data[50]
                            diameter = data[53]
                            hardness = data[56]
                            Rev_thickness = data[38]
                            Rev_diameter = data[41]
                            Rev_hardness = data[44]
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
                            print(thickness, diameter, hardness, Tanggal)
                            Data.kirim_data(hardness, diameter, thickness, "", "025815")
                        elif "No." in data and len(data) < 20:
                            no = data[1]
                            thickness = data[3]
                            diameter = data[6]
                            hardness = data[9]
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
                            print(thickness, diameter, hardness, Tanggal)
                            Data.kirim_data(hardness, diameter, thickness, "", "025815")
                        elif "Xm" in data or "Xmean" in data or "Released:" in data:
                            bef = 0
                            buffer = ""
                            prevCount = 0
                            count = 1
                            data = ""
                            Arbffr = [[]]
            except serial.SerialException as e:
                print(f"Serial exception: {e}")
                serial_port = None  # Set ser to None to trigger reconnection
                time.sleep(5)  # Wait for 5 seconds before attempting to reconnect

if __name__ == "__main__":
    Reading = SerialReader()
    Reading.start()
    while True:
        # Read and assign values from global variables
        h_value = hardness
        d_value = diameter
        t_value = thickness
        status = ""
        code_instrument = "025815"
        created_date = tanggal_waktu_terformat
        # Print or use the values as needed
        #if (hardness != ""):
            #print(h_value, d_value, t_value, status, code_instrument)