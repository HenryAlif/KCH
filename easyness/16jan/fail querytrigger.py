import socket
import json
from sqlalchemy import create_engine, Table, Column, Integer, Float, String, MetaData, Date, Time, DateTime, select, insert, func
from sqlalchemy.orm import sessionmaker
from datetime import datetime, time
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Koneksi ke database raw_data.db
engine_raw = create_engine('sqlite:///raw_data.db')
metadata_raw = MetaData()
received_data = Table('received_data', metadata_raw, autoload_with=engine_raw)

# Koneksi ke database new_data.db
engine_new = create_engine("mysql+mysqlconnector://root:s4k4f4rmA@10.126.15.138:3306/ems_saka")
metadata_new = MetaData()
sakaplant_prod_ipc_staging = Table(
    'sakaplant_prod_ipc_staging', 
    metadata_new,
    Column('id_setup', Integer, primary_key=True, autoincrement=True),
    Column('h_value', Float, nullable=False),
    Column('d_value', Float, nullable=False),
    Column('t_value', Float, nullable=False),
    Column('status', String, nullable=False),
    Column('code_instrument', String, nullable=False),
    Column('time_series', String, nullable=False),
    Column('time_insert', Time, nullable=False),
    Column('created_date', Date, nullable=False)
)

# Membuat tabel jika belum ada
metadata_new.create_all(engine_new)

# Membuat sesi untuk kedua database
SessionRaw = sessionmaker(bind=engine_raw)
session_raw = SessionRaw()

SessionNew = sessionmaker(bind=engine_new)
session_new = SessionNew()

def process_data():
    try:
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

        # Mengambil waktu data terakhir yang ada di tabel sakaplant_prod_ipc_staging
        query_last_time = select(func.max(sakaplant_prod_ipc_staging.c.time_insert))
        last_time_result = session_new.execute(query_last_time).scalar()

        # Jika tidak ada data di sakaplant_prod_ipc_staging, set waktu terakhir ke waktu sangat lama
        if last_time_result is None:
            last_time_result = datetime.min

        for row in result_received_data:
            # Mengonversi row ke dictionary
            row_dict = dict(zip(columns, row))
            time_series_value = row_dict['time_series']
            time_insert_value = row_dict['time_insert']
            
            # Memeriksa apakah data baru memiliki waktu yang lebih baru dari data terakhir
            if time_insert_value > last_time_result:
                # Menambahkan data yang belum ada ke tabel sakaplant_prod_ipc_staging
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
                session_new.execute(insert(sakaplant_prod_ipc_staging).values(insert_data))
                session_new.commit()
                logger.info(f"Data inserted: {insert_data}")
        logger.info("Data telah berhasil diproses dan dimasukkan ke database MySQL")
    except Exception as e:
        logger.error(f"Terjadi kesalahan saat memproses data: {e}")
        session_new.rollback()

def start_server():
    server_address = ('localhost', 65433)  # Alamat dan port server
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    # Mengaktifkan opsi SO_REUSEADDR
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    sock.bind(server_address)
    sock.listen(1)
    
    logger.info("Server status berjalan dan mendengarkan pada port 65433")

    while True:
        connection, client_address = sock.accept()
        try:
            logger.info(f"Koneksi dari {client_address}")
            while True:
                data = connection.recv(1024)
                if data:
                    # Decode and load the JSON data
                    decoded_data = data.decode('utf-8')
                    json_data = json.loads(decoded_data)
                    logger.info(f"Status diterima: {json.dumps(json_data, indent=4)}")
                    
                    status = json_data.get('status')
                    if status == 1:
                        process_data()
                        
                        # Mengirim respon balik ke client dengan status 0
                        response = {'status': 0}
                        response_message = json.dumps(response)
                        connection.sendall(response_message.encode('utf-8'))
                else:
                    break
        except Exception as e:
            logger.error(f"Terjadi kesalahan: {e}")
        finally:
            connection.close()
            logger.info("Koneksi ditutup")

if __name__ == "__main__":
    start_server()