import serial
import threading
import re
import time
import json
from sqlalchemy import create_engine, Column, Float, Integer, String
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

bef = 0
count = 1
prevCount = 0
buffer = ""
Arbffr = [[]]
thickness= ""
diameter = ""
hardness= ""

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

# Inisialisasi komunikasi serial
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

# Fungsi untuk menyimpan data ke file JSON
def save_to_json(data, filename="backup_data.json"):
    try:
        with open(filename, 'r+') as file:
            try:
                existing_data = json.load(file)
            except json.JSONDecodeError:
                existing_data = []
            existing_data.append(data)
            file.seek(0)
            json.dump(existing_data, file, indent=4)
    except FileNotFoundError:
        with open(filename, 'w') as file:
            json.dump([data], file, indent=4)

# Fungsi untuk mengupload data dari file JSON ke database setelah koneksi pulih
def upload_from_json():
    try:
        with open('backup_data.json', 'r') as f:
            backup_data = json.load(f)

        for data in backup_data:
            upload_to_db(data)
        # Clear file after successful upload
        open('backup_data.json', 'w').close()

    except FileNotFoundError:
        print("No backup file found.")
    except Exception as e:
        print(f"Error uploading data from JSON: {e}")

def upload_to_db(data):
    try:
        new_data = Data(
            id_setup=int(data['id_setup']),
            h_value=float(data['h_value']),
            d_value=float(data['d_value']),
            t_value=float(data['t_value']),
            status=(data['status']),
            code_instrument=('025815'),
        )
        session.add(new_data)
        session.commit()
        print(f"Data inserted: {data}")
    except Exception as e:
        session.rollback()
        print(f"Failed to insert data: {e}")

def main():
    while True:
        if serial_port.in_waiting > 0:
            # Membaca data dari serial
            raw_data = serial_port.readline().decode('utf-8').strip()

            try:
                # Parsing JSON
                data = json.loads(raw_data)

                # Upload data ke database
                upload_to_db(data)

            except json.JSONDecodeError:
                print(f"Invalid JSON received: {raw_data}")
            except Exception as e:
                print(f"Error: {e}")

if __name__ == '__main__':
    Reading = SerialReader()
    Reading.start()
    main()
