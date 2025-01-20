import sqlite3
from sqlalchemy import create_engine, Table, Column, Integer, Float, String, MetaData, DateTime, select, insert, func
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# Koneksi ke database raw_data.db
engine_raw = create_engine('sqlite:///raw_data.db')
metadata_raw = MetaData()
received_data = Table('received_data', metadata_raw, autoload_with=engine_raw)

# Koneksi ke database new_data.db
engine_new = create_engine('sqlite:///raw_data.db')
metadata_new = MetaData()
TESTKOCAK = Table(
    'TESTKOCAK', 
    metadata_new,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('h_value', Float, nullable=False),
    Column('d_value', Float, nullable=False),
    Column('t_value', Float, nullable=False),
    Column('status', String, nullable=False),
    Column('code_instrument', String, nullable=False),
    Column('time_series', String, nullable=False),
    Column('time_insert', DateTime, nullable=False),
    Column('created_date', DateTime, nullable=False)
)
metadata_new.create_all(engine_new)  # Membuat tabel jika belum ada

# Membuat sesi untuk kedua database
SessionRaw = sessionmaker(bind=engine_raw)
session_raw = SessionRaw()

SessionNew = sessionmaker(bind=engine_new)
session_new = SessionNew()

# Mengambil data terbaru dari tabel received_data yang tidak null
query_received_data = select(received_data).where(
    received_data.c.h_value.isnot(None),
    received_data.c.d_value.isnot(None),
    received_data.c.t_value.isnot(None),
    received_data.c.status.isnot(None),
    received_data.c.code_instrument.isnot(None),
    received_data.c.time_series.isnot(None)
)
result_received_data = session_raw.execute(query_received_data).fetchall()

# Mengambil nama kolom dari tabel received_data
columns = received_data.columns.keys()

# Mengambil waktu data terakhir yang ada di tabel TESTKOCAK
query_last_time = select(func.max(TESTKOCAK.c.time_insert))
last_time_result = session_new.execute(query_last_time).scalar()

# Jika tidak ada data di TESTKOCAK, set waktu terakhir ke waktu sangat lama
if last_time_result is None:
    last_time_result = datetime.min

for row in result_received_data:
    # Mengonversi row ke dictionary
    row_dict = dict(zip(columns, row))
    time_series_value = row_dict['time_series']
    time_insert_value = row_dict['time_insert']
    
    # Memeriksa apakah data baru memiliki waktu yang lebih baru dari data terakhir
    if time_insert_value > last_time_result:
        # Menambahkan data yang belum ada ke tabel TESTKOCAK
        insert_data = {
            'h_value': row_dict['h_value'],
            'd_value': row_dict['d_value'],
            't_value': row_dict['t_value'],
            'status': row_dict['status'],
            'code_instrument': row_dict['code_instrument'],
            'time_series': row_dict['time_series'],
            'time_insert': row_dict['time_insert'],
            'created_date': datetime.now()
        }
        session_new.execute(insert(TESTKOCAK).values(insert_data))
        session_new.commit()

# Menutup sesi
session_raw.close()
session_new.close()