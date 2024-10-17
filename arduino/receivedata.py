import serial
import json
from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Inisialisasi SQLAlchemy
DATABASE_URL = 'mysql+mysqlconnector://root:s4k4f4rmA@10.126.15.138:3306/ems_saka'
engine = create_engine(DATABASE_URL)
Base = declarative_base()

# Model untuk tabel machine_1
class MachineData(Base):
    __tablename__ = 'kalbe'
    no = Column(Integer, primary_key=True)
    batch = Column(String(50))
    speed = Column(Integer)
    Tanggal = Column(String(50))
    thickness = Column(Float)
    diameter = Column(Float)
    hardness = Column(Integer)

# Membuat sesi untuk koneksi ke database
Session = sessionmaker(bind=engine)
session = Session()

# Inisialisasi komunikasi serial
ser = serial.Serial('/dev/ttyUSB0', 9600, timeout=1)  # Ganti dengan port yang sesuai di Raspberry Pi

def upload_to_db(data):
    try:
        new_data = MachineData(
            no=int(data['no']),
            batch=data['batch'],
            speed=int(data['speed']),
            Tanggal=data['Tanggal'],
            thickness=float(data['thickness']),
            diameter=float(data['diameter']),
            hardness=int(data['hardness'])
        )
        session.add(new_data)
        session.commit()
        print(f"Data inserted: {data}")
    except Exception as e:
        session.rollback()
        print(f"Failed to insert data: {e}")

def main():
    while True:
        if ser.in_waiting > 0:
            # Membaca data dari serial
            raw_data = ser.readline().decode('utf-8').strip()

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
    main()
