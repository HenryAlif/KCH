from sqlalchemy import create_engine, Column, Integer, String, Float, Date
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.exc import SQLAlchemyError
import json
import time

# Membuat Base untuk ORM
Base = declarative_base()

# Definisi model untuk tabel machine_1
class Machine1(Base):
    __tablename__ = 'machine_1'

    no = Column(String(10), primary_key=True)
    batch = Column(String(50))
    speed = Column(String(10))
    Tanggal = Column(Date)
    thickness = Column(Float)
    diameter = Column(Float)
    hardness = Column(String(10))

# Setup database connection using SQLAlchemy
DATABASE_URL = "mysql+mysqlconnector://root:s4k4f4rmA:3306/kalbe"

# Membuat engine
engine = create_engine(DATABASE_URL)

# Membuat session
Session = sessionmaker(bind=engine)
session = Session()

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

        for item in backup_data:
            upload_to_db(item)

        # Kosongkan file setelah upload berhasil
        open('backup_data.json', 'w').close()

    except FileNotFoundError:
        print("No backup file found.")
    except Exception as e:
        print(f"Error uploading data from JSON: {e}")

# Fungsi untuk mengupload data ke database menggunakan SQLAlchemy
def upload_to_db(item):
    try:
        # Membuat objek baru untuk dimasukkan ke dalam tabel machine_1
        new_record = Machine1(
            no=item['no'],
            batch=item['batch'],
            speed=item['speed'],
            Tanggal=item['Tanggal'],
            thickness=float(item['thickness']),
            diameter=float(item['diameter']),
            hardness=item['hardness']
        )

        # Menambahkan record ke session
        session.add(new_record)
        session.commit()  # Simpan perubahan ke database
        print("Data inserted successfully.")

    except SQLAlchemyError as e:
        print(f"Database error: {e}")
        session.rollback()  # Rollback jika terjadi kesalahan
        save_to_json(item)  # Simpan ke JSON jika koneksi database gagal
    except Exception as e:
        print(f"Unexpected error: {e}")
        save_to_json(item)  # Simpan ke JSON jika terjadi error lainnya

# Fungsi utama untuk memproses data dan mengupload
def main_process(new_data_list):
    for new_data in new_data_list:
        upload_to_db(new_data)
        time.sleep(1)  # Delay untuk simulasi koneksi stabil

    # Jika data disimpan ke file JSON saat koneksi terputus, coba upload lagi setelah koneksi stabil
    while True:
        try:
            upload_from_json()
            break  # Keluar dari loop jika semua data berhasil diupload
        except Exception as e:
            print("Re-upload failed. Retrying in 5 seconds...")
            time.sleep(5)  # Coba upload lagi setiap 5 detik jika gagal

# Contoh data yang akan di-upload
new_data_list = [
    {"no": str(i), "batch": f"Batch_{i:03}", "speed": str(100 + i), "Tanggal": "2024-09-18",
     "thickness": f"{2.5 + i * 0.01:.2f}", "diameter": f"{5.6 + i * 0.02:.2f}", "hardness": str(80 + i)}
    for i in range(1, 101)
]

# Menjalankan proses
main_process(new_data_list)
