import socket
import json
import time
from sqlalchemy import create_engine, Column, Integer, String, Float, Date, Time
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# Konfigurasi untuk SQLAlchemy
DATABASE_URL = "sqlite:///raw_data.db"
engine = create_engine(DATABASE_URL)
Base = declarative_base()

# Definisi tabel untuk menyimpan data yang diterima
class ReceivedData(Base):
    __tablename__ = 'received_data'

    id = Column(Integer, primary_key=True, autoincrement=True)
    h_value = Column(Float, nullable=False)
    d_value = Column(Float, nullable=False)
    t_value = Column(Float, nullable=False)
    status = Column(String, nullable=False)
    code_instrument = Column(String, nullable=False)
    time_series = Column(String, nullable=False)
    time_insert = Column(Time, nullable=False)
    created_date = Column(Date, nullable=False)

# Buat tabel di database
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()

def save_to_database(data):
    """Menyimpan data JSON ke database."""
    try:
        new_data = ReceivedData(
            h_value=float(data['h_value']),
            d_value=float(data['d_value']),
            t_value=float(data['t_value']),
            status=data['status'],
            code_instrument=data['code_instrument'],
            time_series=data['time_series'],
            time_insert=datetime.strptime(data['time_insert'], '%H:%M:%S').time(),  # Extract time part
            created_date=datetime.strptime(data['created_date'], '%Y-%m-%d').date()  # Extract date part
        )
        session.add(new_data)
        session.commit()
        print(f"Data disimpan ke database: {data}")
        with open("log_servertrigger.txt", "a") as file:
            file.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')}: {data}\n")
        send_status(data)  # Kirim data yang disimpan ke client
    except Exception as e:
        session.rollback()
        print(f"Gagal menyimpan data: {e}")
        send_status(None)  # Kirim status gagal

def send_status(data):
    """Mengirim data yang disimpan ke client lain."""
    client_address = ('localhost', 65433)  # Alamat dan port client untuk status
    try:
        # Membuat socket dan mengirim data
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect(client_address)
            if data is not None:
                message = json.dumps(data).encode('utf-8')
            else:
                message = json.dumps({"status": 0}).encode('utf-8')
            sock.sendall(message)
            print(f"Data dikirim ke client: {data}")
    except Exception as e:
        print(f"Gagal mengirim data: {e}")

def start_server():
    server_address = ('localhost', 65432)  # Alamat dan port server
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    # Mengaktifkan opsi SO_REUSEADDR
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    sock.bind(server_address)
    sock.listen(1)
    
    print("Server berjalan dan mendengarkan pada port 65432")

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