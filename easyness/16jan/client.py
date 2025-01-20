import serial
import threading
import json
import socket
from sqlalchemy import create_engine, Column, Integer, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import time

# Konfigurasi untuk SQLAlchemy
DATABASE_URL = "sqlite:///raw_data.db"
engine = create_engine(DATABASE_URL)
Base = declarative_base()

# Definisi tabel untuk menyimpan data serial
class SerialData(Base):
    __tablename__ = 'raw_data_table'

    id = Column(Integer, primary_key=True, autoincrement=True)
    raw_data = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
# Buat tabel di database
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()

# Konfigurasi komunikasi serial
SERIAL_PORT = 'COM3'  # Ganti dengan port COM yang sesuai
BAUD_RATE = 9600

# Variabel global untuk melacak time_series terakhir yang diproses
last_time_series = 0

def read_serial():
    """Membaca data dari komunikasi serial."""
    global last_time_series
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

                elif is_recording:
                    buffer += data + "\n"  # Tambahkan data ke buffer

                    # Jika mendeteksi baris dengan "No." dan "kp"
                    if "No." in data and "kp" in data:
                        save_to_database(buffer.strip())  # Simpan buffer ke database

                        # Parse data saat ini dan kirim data terbaru ke server
                        parsed_data = parse_data(buffer.strip())

                        if parsed_data:
                            for entry in parsed_data:
                                if int(entry['time_series']) > last_time_series:
                                    last_time_series = int(entry['time_series'])
                                    send_to_server(entry)  # Kirim data terbaru ke server

    except Exception as e:
        print(f"Terjadi kesalahan: {e}")
    finally:
        ser.close()
        print("Koneksi serial ditutup.")

def save_to_database(data):
    """Menyimpan data ke database."""
    try:
        new_data = SerialData(raw_data=data)
        session.add(new_data)
        session.commit()
        print(f"Data disimpan ke database: {data}")
    except Exception as e:
        session.rollback()
        print(f"Gagal menyimpan data: {e}")

def parse_data(data):
    """Memparsing data dari buffer ke dalam format yang diinginkan."""
    parsed_data = []
    lines = data.split("\n")
    for line in lines:
        if "No." in line and "kp" in line:
            parts = line.split(":")
            time_series = parts[0].split()[1]
            t_value = parts[1].strip().split()[0]
            d_value = parts[2].strip().split()[0]
            h_value = parts[3].strip().split()[0]

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

def send_to_server(data):
    """Mengirim data ke server socket dalam bentuk JSON."""
    server_address = ('localhost', 65432)  # Ganti dengan alamat dan port server yang sesuai
    while True:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect(server_address)

            message = json.dumps(data)
            sock.sendall(message.encode('utf-8'))
            print(f"Data dikirim ke server: {message}")
            with open("log_client.txt", "a") as file:
                file.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')}: {data}\n")

            sock.close()
            break  # Keluar dari loop jika berhasil mengirim data
        except Exception as e:
            print(f"Gagal mengirim data ke server: {e}")
            time.sleep(5)  # Tunggu sebelum mencoba lagi

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