import serial
import threading
import json
import socket
from sqlalchemy import create_engine, Column, Integer, Text, DateTime, func, Float, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import time
import re

# Konfigurasi untuk SQLAlchemy
DATABASE_URL = "postgresql://users_pims_engineer:Engineer_2023@10.106.1.40/pims_prod"
engine = create_engine(DATABASE_URL, echo=True)
Base = declarative_base()

# Definisi tabel untuk menyimpan data serial
class SerialData(Base):
    __tablename__ = 'sakaplant_prod_ipc_staging'
    id_setup = Column(Integer, primary_key=True)
    h_value = Column(Float)
    d_value = Column(Float)
    t_value = Column(Float)
    status = Column(String)
    code_instrument = Column(String)
    time_series = Column(Integer)
    time_insert = Column(String)
    created_date = Column(String)

# Buat tabel di database
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

# Konfigurasi komunikasi serial
SERIAL_PORT = 'COM3'  # Ganti dengan port COM yang sesuai
BAUD_RATE = 9600

# Variabel global untuk melacak time_series terakhir yang diproses
last_time_series = 0

def read_serial():
    """Membaca data dari komunikasi serial."""
    global last_time_series
    session = Session()  # Pindahkan pembuatan session di dalam fungsi untuk memastikan scope yang benar
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        print(f"Membuka koneksi ke {SERIAL_PORT} dengan baud rate {BAUD_RATE}")

        buffer = ""
        is_recording = False
        while True:
            data = ser.readline().decode('utf-8').strip()
            if data:
                print(f"Data diterima: {data}")

                # Deteksi awal data
                if "Tablet Testing System PTB311E V01.11 E" in data:
                    is_recording = True  # Mulai merekam data
                    buffer = data + "\n"  # Reset buffer dan tambahkan baris pertama
                    last_time_series = 0  # Reset last_time_series untuk data baru
                    print("Mulai merekam data...")

                elif is_recording:
                    buffer += data + "\n"  # Tambahkan data ke buffer
                    print(f"Buffer saat ini: {buffer}")

                    # Jika mendeteksi baris dengan "No." dan "kp"
                    if "No." in data and "kp" in data:
                        print("Mendeteksi baris data hasil...")
                        parsed_data = parse_data(buffer.strip())

                        if parsed_data:
                            for entry in parsed_data:
                                if int(entry['time_series']) > last_time_series:
                                    last_time_series = int(entry['time_series'])
                                    send_to_database(entry, session)  # Kirim data ke database

    except Exception as e:
        print(f"Terjadi kesalahan: {e}")
    finally:
        ser.close()
        session.close()  # Tutup session setelah selesai
        print("Koneksi serial ditutup.")

def parse_data(data):
    """Memparsing data dari buffer ke dalam format yang diinginkan."""
    parsed_data = []

    # Regex untuk mendeteksi baris data yang dimulai dengan "No."
    pattern = re.compile(r"No\.\s+(\d+)\s+:\s+(\d+\.\d+)\s+mm\s+:\s+(\d+\.\d+)\s+mm\s+:\s+(\d+\.\d+)\s+kp")
    matches = pattern.findall(data)

    for match in matches:
        time_series, t_value, d_value, h_value = match

        data_dict = {
            "h_value": h_value,
            "d_value": d_value,
            "t_value": t_value,
            "status": "N",
            "code_instrument": "A20230626002",
            "time_series": time_series,
            "time_insert": datetime.now().strftime('%H:%M:%S'),
            "created_date": datetime.now().strftime('%Y-%m-%d')
        }
        parsed_data.append(data_dict)
    
    return parsed_data

def send_to_database(data, session):
    """Mengirim data yang telah di-parsing ke database."""
    try:
        serial_data = SerialData(
            h_value=float(data['h_value']),
            d_value=float(data['d_value']),
            t_value=float(data['t_value']),
            status=data['status'],
            code_instrument=data['code_instrument'],
            time_series=int(data['time_series']),
            time_insert=data['time_insert'],
            created_date=data['created_date']
        )
        session.add(serial_data)
        session.commit()
        print("Data berhasil dikirim ke database.")
    except Exception as e:
        session.rollback()
        print(f"Gagal mengirim data ke database: {e}")

def start_reading():
    """Fungsi untuk memulai thread membaca serial."""
    read_thread = threading.Thread(target=read_serial)
    read_thread.daemon = True
    read_thread.start()

if __name__ == "__main__":
    start_reading()
    # Menjaga program utama tetap berjalan
    while True:
        time.sleep(1)