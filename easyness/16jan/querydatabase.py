import socket
import logging
import json
import time
from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# Konfigurasi untuk SQLAlchemy
db_url = 'postgresql://users_pims_engineer:Engineer_2023@10.106.1.40/pims_prod'
engine = create_engine(db_url, pool_pre_ping=True)
Base = declarative_base()

# Definisi tabel untuk menyimpan data yang diterima
class SakaplantProdIpcStaging(Base):
    __tablename__ = 'sakaplant_prod_ipc_staging'
    
    id_setup = Column(Integer, primary_key=True)
    h_value = Column(Float)
    d_value = Column(Float)
    t_value = Column(Float)
    status = Column(String)
    code_instrument = Column(String)
    time_series = Column(Integer)

# Buat tabel di database jika belum ada
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()

def save_to_database(data):
    """Menyimpan data JSON ke database."""
    try:
        new_data = SakaplantProdIpcStaging(
            h_value=float(data['h_value']),
            d_value=float(data['d_value']),
            t_value=float(data['t_value']),
            status=data['status'],
            code_instrument=data['code_instrument'],
            time_series=int(data['time_series'])
        )
        session.add(new_data)
        session.commit()
        print(f"Data disimpan ke database: {data}")
        with open("log_querydatabase.txt", "a") as file:
            file.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')}: {data}\n")
        
    except Exception as e:
        session.rollback()
        print(f"Gagal menyimpan data: {e}")

def start_server():
    server_address = ('localhost', 65433)  # Alamat dan port server
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    # Mengaktifkan opsi SO_REUSEADDR
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    sock.bind(server_address)
    sock.listen(1)
    
    print("Server berjalan dan mendengarkan pada port 65433")

    while True:
        connection, client_address = sock.accept()
        try:
            print(f"Koneksi dari {client_address}")
            while True:
                data = connection.recv(1024)
                if data:
                    # Decode and load the JSON data
                    decoded_data = data.decode('utf-8')
                    json_data = json.loads(decoded_data)
                    print(f"Data diterima: {json.dumps(json_data, indent=4)}")
                    
                    # Simpan data ke database
                    save_to_database(json_data)
                    
                    # Optionally, send a response back to the client
                    response = {'status': 'success', 'received_data': json_data}
                    response_message = json.dumps(response)
                    connection.sendall(response_message.encode('utf-8'))
                else:
                    break
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON: {e}")
        except Exception as e:
            print(f"Terjadi kesalahan: {e}")
        finally:
            connection.close()
            print("Koneksi ditutup")

if __name__ == "__main__":
    start_server()