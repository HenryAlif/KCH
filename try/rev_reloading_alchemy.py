import json
import time
from sqlalchemy import create_engine, Column, Integer, String, Float, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# Membuat deklarasi base untuk ORM SQLAlchemy
Base = declarative_base()

# Mendefinisikan tabel dengan SQLAlchemy
class MachineData(Base):
    __tablename__ = 'kalbe'
    
    no = Column(Integer, primary_key=True)
    batch = Column(String(50))
    speed = Column(Integer)
    Tanggal = Column(Date)
    thickness = Column(Float)
    diameter = Column(Float)
    hardness = Column(Integer)

# Koneksi ke database MariaDB menggunakan SQLAlchemy
DATABASE_URL = "mysql+mysqlconnector://root:s4k4f4rmA@10.126.15.138:3306/ems_saka"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Membuat tabel jika belum ada
Base.metadata.create_all(bind=engine)

# Fungsi untuk menyimpan data ke file JSON
def save_to_json(data, filename="backup_data_revisi.json"):
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
        with open('backup_data_revisi.json', 'r') as f:
            file_content = f.read().strip()
            if not file_content:
                print("Backup file is empty. No data to upload.")
                return

            backup_data_revisi = json.loads(file_content)

        for item in backup_data_revisi[:]:
            if upload_to_db(item):  # Jika berhasil diupload
                backup_data_revisi.remove(item)
            else:
                print(f"Failed to upload item: {item}")  # Tampilkan data yang gagal diupload

        # Simpan kembali data yang belum terupload
        with open('backup_data_revisi.json', 'w') as f:
            json.dump(backup_data_revisi, f, indent=4)

    except FileNotFoundError:
        print("No backup file found.")
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
    except Exception as e:
        print(f"Error uploading data from JSON: {e}")

# Fungsi untuk mengupload data ke database menggunakan SQLAlchemy
def upload_to_db(item):
    try:
        session = SessionLocal()
        # Convert "Tanggal" to Python's datetime object
        try:
            tanggal = datetime.strptime(item['Tanggal'], "%Y-%m-%d")
        except ValueError:
            print(f"Invalid date format for item: {item}")
            return False
        
        # Membuat instance dari class MachineData
        machine_data = MachineData(
            no=int(item['no']),
            batch=item['batch'],
            speed=int(item['speed']),
            Tanggal=tanggal,
            thickness=float(item['thickness']),
            diameter=float(item['diameter']),
            hardness=int(item['hardness'])
        )
        
        session.add(machine_data)
        session.commit()
        session.close()
        print(f"Data with no {item['no']} inserted into the database.")
        return True
    except Exception as e:
        print(f"Error inserting data: {e}")
        return False

# Fungsi utama untuk memproses data dan mengupload
def main_process(new_data_list):
    for new_data in new_data_list:
        if not upload_to_db(new_data):  # Simpan ke JSON jika gagal upload
            save_to_json(new_data)
        time.sleep(1)  # Delay untuk simulasi koneksi stabil

    # Jika data disimpan ke file JSON saat koneksi terputus, coba upload lagi setelah koneksi stabil
    while True:
        try:
            upload_from_json()  # Coba upload data yang tersimpan di JSON
            break  # Keluar dari loop jika semua data berhasil diupload
        except Exception as e:
            print("Re-upload failed. Retrying in 5 seconds...")
            time.sleep(5)  # Coba upload lagi setiap 5 detik jika gagal

# Contoh data yang akan di-upload
new_data_list = [
    {"no": str(i), "batch": f"{i:03}", "speed": str(100 + i), "Tanggal": "2024-09-18",
     "thickness": f"{2.5 + i * 0.01:.2f}", "diameter": f"{5.6 + i * 0.02:.2f}", "hardness": str(80 + i)}
    for i in range(1, 20)
]

# Menjalankan proses
main_process(new_data_list)
