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

    def start(self):
        self.thread.start()

    def _read_thread(self):
        global serial_port
        buffer = ""

        while True:
            try:
                if serial_port is None:
                    initialize_serial()
                    continue

                # Membaca satu baris dari serial (newline-terminated)
                line = serial_port.readline().decode(encoding='UTF-8', errors='replace').strip()

                if line:
                    print(f"Data received: {line}")  # Debugging untuk melihat data yang diterima

                    # Proses data dengan regex sesuai format yang dikirim dari Arduino
                    match = re.search(
                        r'Testing batch (\d+) speed ([\d.]+) Tanggal (\d{4}-\d{2}-\d{2}) Time (\d{2}:\d{2}:\d{2}) '
                        r'No (\d+) thickness ([\d.]+) diameter ([\d.]+) hardness ([\d.]+)',
                        line
                    )

                    if match:
                        # Ekstrak data dari match
                        batch = int(match.group(1))
                        speed = float(match.group(2))
                        Tanggal = match.group(3)
                        Time = match.group(4)
                        no = int(match.group(5))
                        thickness = float(match.group(6))
                        diameter = float(match.group(7))
                        hardness = float(match.group(8))

                        print(f"Parsed data - No: {no}, Thickness: {thickness}, Diameter: {diameter}, Hardness: {hardness}")

                        # Simpan data ke database
                        self.save_to_db({
                            'no': no,
                            'batch': batch,
                            'speed': speed,
                            'Tanggal': Tanggal,
                            'Time': Time,
                            'thickness': thickness,
                            'diameter': diameter,
                            'hardness': hardness
                        })

                    else:
                        print(f"Unrecognized data format: {line}")

            except serial.SerialException as e:
                print(f"Serial exception: {e}")
                serial_port = None  # Set serial_port to None to trigger reconnection
                time.sleep(5)

    def save_to_db(self, data):
        try:
            new_data = Data(
                id_setup=int(data['no']),
                h_value=float(data['hardness']),
                d_value=float(data['diameter']),
                t_value=float(data['thickness']),
                status="",
                code_instrument="025815"
            )
            session.add(new_data)
            session.commit()
            print(f"Data berhasil diupload ke database: {data}")
        except Exception as e:
            session.rollback()
            print(f"Gagal mengupload data ke database: {e}")

def main():
    reader = SerialReader()
    reader.start()

if __name__ == '__main__':
    main()
