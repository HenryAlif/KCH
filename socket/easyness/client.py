import serial
import threading
import re
import time
import logging
from datetime import datetime
import json
import socket
import pickle
import os
from sqlalchemy import create_engine, Column, Integer, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Database setup
DATABASE_URI = "sqlite:///raw_data.db"
engine = create_engine(DATABASE_URI)
Session = sessionmaker(bind=engine)
session = Session()
Base = declarative_base()

# Define the table model
class Data(Base):
    __tablename__ = 'raw_data_table'

    id = Column(Integer, primary_key=True, autoincrement=True)
    raw_data = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(engine)

logging.basicConfig(filename='info_log.txt', level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

def save_to_database(raw_data):
    """Save raw data to the database."""
    new_entry = Data(raw_data=raw_data)
    session.add(new_entry)
    session.commit()

def parse_data(raw_data):
    """Parse the raw data into structured format."""
    raw_data = re.sub(r"-{2,}", "", raw_data).strip()
    lines = [line.strip() for line in raw_data.split("\n") if line.strip()]

    # Extract entries
    entries = []
    for line in lines:
        if line.startswith("No."):
            match = re.match(r'No\.\s*(\d+)\s*:\s*([\d.]+) mm\s*:\s*([\d.]+) mm\s*:\s*([\d.]+) kp', line)
            if match:
                time_series = int(match.group(1))
                t_value = float(match.group(2))
                d_value = float(match.group(3))
                h_value = float(match.group(4))
                entries.append((time_series, t_value, d_value, h_value))
    return entries

def load_id_counter(filename):
    """Load the ID counter from a file."""
    if os.path.exists(filename):
        with open(filename, 'r') as file:
            return int(file.read())
    return 0

def save_id_counter(filename, counter):
    """Save the ID counter to a file."""
    with open(filename, 'w') as file:
        file.write(str(counter))

def append_log(log_filename, data_object):
    """Append a log entry to the JSON log file."""
    log_entry = {
        "id": data_object['id'],
        "h_value": data_object['h_value'],
        "d_value": data_object['d_value'],
        "t_value": data_object['t_value'],
        "status": data_object['status'],
        "code_instrument": data_object['code_instrument'],
        "time_series": data_object['time_series'],
        "time_insert": data_object['time_insert'],
        "created_date": data_object['created_date']
    }

    # Load existing log data
    if os.path.exists(log_filename):
        with open(log_filename, 'r') as file:
            log_data = json.load(file)
    else:
        log_data = []

    # Append the new log entry
    log_data.append(log_entry)

    # Save the updated log data to the file
    with open(log_filename, 'w') as file:
        json.dump(log_data, file, indent=4)

def send_data_to_server(data_object):
    """Send parsed data to the server."""
    id_counter_file = 'id_counter.txt'
    log_filename = 'log.json'

    # Increment the ID counter
    id_counter = load_id_counter(id_counter_file)
    data_object['id'] = id_counter
    id_counter += 1
    save_id_counter(id_counter_file, id_counter)

    try:
        # Setup client socket
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect(('localhost', 12345))

        # Serialize data object
        data = pickle.dumps(data_object)

        # Send data
        client_socket.sendall(data)
        print(f"Data sent: {data_object}")

        client_socket.close()
    except ConnectionRefusedError:
        print("Server is not running. Retrying in 5 seconds...")

    # Append the log entry to the JSON log file
    append_log(log_filename, data_object)

def serial_reader():
    """Read data from the serial port."""
    port = "COM3"
    baudrate = 9600

    buffer = ""
    is_recording = False

    try:
        ser = serial.Serial(port, baudrate, timeout=1)
        ser.reset_input_buffer()
        print(f"Serial connection established on {port} with baudrate {baudrate}.")
        logging.info(f"Serial connection established on {port} with baudrate {baudrate}.")

        while True:
            data = ser.readline().decode('utf-8', errors='replace').strip()
            if data:
                print(f"Data diterima: {data}")

                # Deteksi awal data
                if "Tablet Testing System PTB311E V01.11 E" in data:
                    if is_recording:
                        # Simpan data sebelumnya jika ada
                        save_to_database(buffer.strip())
                        parsed_entries = parse_data(buffer)
                        for entry in parsed_entries:
                            time_series, t_value, d_value, h_value = entry
                            data_object = {
                                "h_value": h_value,
                                "d_value": d_value,
                                "t_value": t_value,
                                "status": "N",
                                "code_instrument": "A20230626002",
                                "time_series": time_series,
                                "time_insert": datetime.now().strftime('%H:%M:%S'),
                                "created_date": datetime.now().strftime('%Y-%m-%d')
                            }
                            send_data_to_server(data_object)
                    is_recording = True  # Mulai merekam data
                    buffer = data + "\n"  # Reset buffer dan tambahkan baris pertama

                elif is_recording:
                    buffer += data + "\n"  # Tambahkan data ke buffer

                    # Jika mendeteksi baris dengan "No." dan "kp"
                    if "No." in data and "kp" in data:
                        # Cek jika ada nomor baru di data
                        match = re.match(r"No\.\s*(\d+)", data)
                        if match:
                            current_no = int(match.group(1))
                            # Simpan data dan reset buffer untuk data baru
                            save_to_database(buffer.strip())
                            parsed_entries = parse_data(buffer)
                            for entry in parsed_entries:
                                time_series, t_value, d_value, h_value = entry
                                data_object = {
                                    "h_value": h_value,
                                    "d_value": d_value,
                                    "t_value": t_value,
                                    "status": "N",
                                    "code_instrument": "A20230626002",
                                    "time_series": time_series,
                                    "time_insert": datetime.now().strftime('%H:%M:%S'),
                                    "created_date": datetime.now().strftime('%Y-%m-%d')
                                }
                                send_data_to_server(data_object)
                            buffer = buffer.strip()  # Pertahankan buffer untuk data berikutnya

    except serial.SerialException as e:
        logging.error(f"Serial exception: {e}")
        print(f"Serial exception: {e}")
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        print(f"Unexpected error: {e}")

if __name__ == "__main__":
    reader_thread = threading.Thread(target=serial_reader)
    reader_thread.daemon = True
    reader_thread.start()

    while True:
        time.sleep(1)