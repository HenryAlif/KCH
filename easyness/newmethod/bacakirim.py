import serial
from sqlalchemy import create_engine, Column, Integer, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# Konfigurasi untuk SQLAlchemy
# DATABASE_URL = "mysql+mysqlconnector://root:s4k4f4rmA@10.126.15.138:3306/ems_saka"  # Ganti dengan URL database yang sesuai
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

def read_serial():
    """Membaca data dari komunikasi serial."""
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

                elif is_recording:
                    buffer += data + "\n"  # Tambahkan data ke buffer

                    # Jika mendeteksi baris dengan "No." dan "kp"
                    if "No." in data and "kp" in data:
                        save_to_database(buffer.strip())  # Simpan buffer ke database

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



if __name__ == "__main__":
    read_serial()
