import re
import time
from sqlalchemy import create_engine, Table, MetaData, Column, Integer, Float, DateTime, Text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import text
from datetime import datetime

# Koneksi ke database sumber dan tujuan
DATABASE_URL = "sqlite:///raw_data.db"

# Inisialisasi koneksi database
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()

# Definisi tabel tujuan jika belum ada
metadata = MetaData()
parsed_data_table = Table(
    "parsed_data_table", metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("h_value", Float, nullable=False),
    Column("d_value", Float, nullable=False),
    Column("t_value", Float, nullable=False),
    Column("time_series", Integer, nullable=False),
    Column("timestamp", DateTime, default=datetime.utcnow)
)
metadata.create_all(engine)

# Fungsi untuk memparsing data
def parse_data(buffer, last_no):
    parsed_entries = []
    for line in buffer.splitlines():
        match = re.match(r"No\.\s+(\d+)\s*:\s*([\d.]+)\s*mm\s*:\s*([\d.]+)\s*mm\s*:\s*([\d.]+)\s*kp", line)
        if match:
            time_series = int(match.group(1))
            if time_series > last_no:  # Hanya memproses No. setelah last_no
                t_value = float(match.group(2))
                d_value = float(match.group(3))
                h_value = float(match.group(4))
                parsed_entries.append({
                    "time_series": time_series,
                    "t_value": t_value,
                    "d_value": d_value,
                    "h_value": h_value
                })
    return parsed_entries

# Fungsi untuk mendapatkan ID terakhir dari raw_data_table
def get_latest_raw_data():
    result = session.execute(
        text("SELECT id, raw_data FROM raw_data_table ORDER BY id DESC LIMIT 1")
    ).fetchone()
    return result

# Fungsi untuk memproses data terbaru
def process_latest_data(last_no):
    latest_entry = get_latest_raw_data()
    
    if not latest_entry:
        print("Tidak ada data di tabel raw_data_table.")
        return last_no
    
    raw_id, raw_data = latest_entry
    print(f"Memproses data terbaru ID {raw_id}...")
    
    parsed_entries = parse_data(raw_data, last_no)
    
    if parsed_entries:
        # Masukkan hasil parsing ke parsed_data_table
        for data in parsed_entries:
            session.execute(
                parsed_data_table.insert().values(
                    h_value=data["h_value"],
                    d_value=data["d_value"],
                    t_value=data["t_value"],
                    time_series=data["time_series"]
                )
            )
        session.commit()
        print(f"Data ID {raw_id} berhasil diproses. Entri baru dari No. {last_no + 1} hingga {parsed_entries[-1]['time_series']} disimpan.")
        return max(entry["time_series"] for entry in parsed_entries)
    else:
        print(f"Tidak ada entri baru untuk diproses pada ID {raw_id}.")
        return last_no

# Program utama (standby)
if __name__ == "__main__":
    last_no = 0  # Inisialisasi nomor terakhir yang diproses
    print("Program berjalan, menunggu data baru...")
    
    while True:
        last_no = process_latest_data(last_no)
        time.sleep(5)  # Tunggu 5 detik sebelum mengecek data baru lagi
