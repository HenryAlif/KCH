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
                            # Parsing data here...
                            # Simpan data di JSON jika gagal koneksi
                            Data.kirim_data(hardness, diameter, thickness, "", "025815")
                        elif "No." in data and len(data) < 20:
                            # Parsing data lainnya
                            Data.kirim_data(hardness, diameter, thickness, "", "025815")
                        elif "Xm" in data or "Xmean" in data or "Released:" in data:
                            bef = 0
                            buffer = ""
                            prevCount = 0
                            count = 1
                            Arbffr = [[]]
            except serial.SerialException as e:
                print(f"Serial exception: {e}")
                serial_port = None  # Set serial_port to None to trigger reconnection
                time.sleep(5)

# Fungsi untuk menyimpan data ke file JSON jika gagal koneksi ke database
def save_to_json(data, filename="backup_data.json"):
    try:
        with open(filename, 'r+') as file:
            try:
                # Load existing data
                existing_data = json.load(file)
            except (ValueError, json.JSONDecodeError):  # Handle corrupted or empty file
                print("File JSON kosong atau rusak, membuat data baru.")
                existing_data = []
            
            # Tambahkan data baru ke dalam list
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
            try:
                backup_data = json.load(f)
            except (ValueError, json.JSONDecodeError):
                print("Backup file kosong atau rusak.")
                return

        # Upload data ke database
        for data in backup_data:
            upload_to_db(data)

        # Kosongkan file setelah upload berhasil
        open('backup_data.json', 'w').close()

    except FileNotFoundError:
        print("Backup file tidak ditemukan.")
    except Exception as e:
        print(f"Error saat mengupload data dari JSON: {e}")

# Fungsi untuk mengupload data ke database
def upload_to_db(data):
    try:
        new_data = Data(
            id_setup=int(data['id_setup']),
            h_value=float(data['h_value']),
            d_value=float(data['d_value']),
            t_value=float(data['t_value']),
            status=data.get('status', 'Unknown'),
            code_instrument=data.get('code_instrument', '025815'),
        )
        session.add(new_data)
        session.commit()
        print(f"Data berhasil diupload: {data}")
    except Exception as e:
        session.rollback()
        print(f"Gagal mengupload data: {e}")

def main():
    while True:
        if serial_port.in_waiting > 0:
            raw_data = serial_port.readline().decode('utf-8').strip()

            try:
                # Parsing JSON
                data = json.loads(raw_data)
                # Upload data ke database
                upload_to_db(data)

            except json.JSONDecodeError:
                print(f"JSON tidak valid diterima: {raw_data}")
                # Save data ke file JSON jika parsing gagal
                save_to_json({"raw_data": raw_data})
            except Exception as e:
                print(f"Error: {e}")

if __name__ == '__main__':
    reader = SerialReader()
    reader.start()
    main()
