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
from sqlalchemy import create_engine, Column, Integer, Float, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Database setup
DATABASE_URI = 'postgresql://users_pims_engineer:Engineer_2023@10.106.1.40/pims_prod'
engine = create_engine(DATABASE_URI)
Session = sessionmaker(bind=engine)
session = Session()
Base = declarative_base()

# Define the table model
class Data(Base):
    __tablename__ = 'sakaplant_prod_ipc_staging'

    id_setup = Column(Integer, primary_key=True)
    h_value = Column(Float)
    d_value = Column(Float)
    t_value = Column(Float)
    status = Column(String)
    code_instrument = Column(String)
    time_series = Column(Integer)

    @classmethod
    def kirim_data(cls, h_value, d_value, t_value, status, code_instrument, time_series):
        data_baru = cls(
                        h_value=h_value, 
                        d_value=d_value, 
                        t_value=t_value,
                        status=status, 
                        code_instrument=code_instrument, 
                        time_series=time_series)
        session.add(data_baru)
        session.commit()

# Create the table if it doesn't exist
Base.metadata.create_all(engine)

logging.basicConfig(filename='info_log.txt', level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

# Initialize global variables
bef = 0
count = 1
prevCount = 0
buffer = ""
Arbffr = [[]]
hardness = ""
diameter = ""
thickness = ""
time_series = ""

# Variables for storing the last error message
last_error_message = None

# Get the current date in the desired format
tanggal_waktu_terformat = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

def initialize_serial():
    global serial_port, tanggal_waktu_terformat, last_error_message
    while True:
        try:
            serial_port = serial.Serial(port="COM12", baudrate=9600, timeout=1)
            serial_port.reset_input_buffer()
            print(f"Serial connection established. {tanggal_waktu_terformat}")
            logging.info(f"Serial connection established on {serial_port.port} with baudrate {serial_port.baudrate} at {tanggal_waktu_terformat}")
            error_message = f"ESTABLISHED {serial_port.port} at {tanggal_waktu_terformat}"
            time.sleep(2)
            break
        except serial.SerialException as e:
            error_message = f"Serial FAILED: {e}"
            print(error_message)
            logging.error(error_message)
            
            # Check if the error message is the same as the previous one
            if last_error_message != error_message:
                last_error_message = error_message  # Save the last error message
            time.sleep(5)

initialize_serial()  # Initialize the serial connection
logging.info(f"Serial connection established on {serial_port.port} with baudrate {serial_port.baudrate} at {tanggal_waktu_terformat}")

class SerialReader:

    def __init__(self):
        self.thread = threading.Thread(target=self._read_thread)
        self.thread.daemon = True

    def start(self):
        self.thread.start()

    def _read_thread(self):
        global serial_port, bef, buffer, Arbffr, prevCount, tanggal_waktu_terformat, last_error_message
        while True:
            try:
                if serial_port is None:
                    initialize_serial()
                    continue
                line = serial_port.readline().decode(encoding='UTF-8', errors='replace')
                if line:
                    buffer += line
                    if bef == 0:
                        bef = 1
                        buffer = ""
                    else:
                        bef = 1
                else:
                    if bef == 1:
                        data = re.split(r"\s+|\n", buffer)
                        if "Testing" in data:
                            try:
                                dataindex = data.index("Results")
                                print('Results')
                                print('data indek')
                                batch = data[22]
                                speed = data[24]
                                Tanggal = data[28]
                                Time = data[30]
                                no = data[48]
                                thickness = float(data[dataindex+4])
                                diameter = float(data[dataindex+7])
                                hardness = float(data[dataindex+10])
                                Rev_thickness = data[38]
                                Rev_diameter = data[41]
                                Rev_hardness = data[44]
                                count = int(no)
                                Arbffr[prevCount].append(no)
                                Arbffr[prevCount].append(batch)
                                Arbffr[prevCount].append(speed)
                                Arbffr[prevCount].append(Tanggal)
                                Arbffr[prevCount].append(Time)
                                Arbffr[prevCount].append(thickness)
                                Arbffr[prevCount].append(diameter)
                                Arbffr[prevCount].append(hardness)
                                prevCount = count
                                buffer = ""
                                
                                print('test')
                                print(buffer)
                                print('print buffer')
                                print(Arbffr)
                                print('print Arfb')
                                print('test setelahnya')

                                # Save to JSON format
                                self.save_to_json(no, hardness, diameter, thickness, Tanggal, Time)
                                
                                # Send data to server
                                self.send_data_to_server(no, hardness, diameter, thickness, Tanggal, Time)
                    
                            except (ValueError, IndexError) as conversion_error:
                                error_message = f"Data CONVERSION: {conversion_error}"
                                logging.error(error_message)
                                print('test2')
                                # Check if the error message is the same as the previous one
                                if last_error_message != error_message:
                                    last_error_message = error_message 
                                
                                bef = 0
                                buffer = ""
                                prevCount = 0
                                count = 1
                                data = ""
                                Arbffr = [[]]
                                continue 

                        elif "No." in data and len(data) < 20:
                            try:
                                dataindex = data.index("mm")
                                no = data[1]
                                thickness = float(data[dataindex-1])
                                diameter = float(data[dataindex+2])
                                hardness = float(data[dataindex+5])
                                count = int(no)
                                Arbffr.append([])
                                Arbffr[prevCount].append(no)
                                Arbffr[prevCount].append(thickness)
                                Arbffr[prevCount].append(diameter)
                                Arbffr[prevCount].append(hardness)
                                prevCount = count

                                buffer = ""
                                print(Arbffr)
                                print('print arf kedua')
                                # Save to JSON format
                                self.save_to_json(no, hardness, diameter, thickness, "", "")
                                
                                # Send data to server
                                self.send_data_to_server(no, hardness, diameter, thickness, "", "")
                            except (ValueError, IndexError) as conversion_error:
                                bef = 0
                                buffer = ""
                                prevCount = 0
                                count = 1
                                data = ""
                                Arbffr = [[]]
                                continue
                        
                        elif "Xm" in data or "Xmean" in data or "Released:" in data:
                            bef = 0
                            buffer = ""
                            prevCount = 0
                            count = 1
                            data = ""
                            time.sleep(5)
                            Arbffr = [[]]
            except serial.SerialException as e:
                error_message = f"Serial exception: {e}"
                logging.error(error_message)
                
                # Check if the error message is the same as the previous one
                if last_error_message != error_message:
                    last_error_message = error_message  
                serial_port = None
                time.sleep(5)

    print(buffer)
    def save_to_json(self, no, hardness, diameter, thickness):
        # Prepare data
        data = {
            "h_value": hardness,
            "d_value": diameter,
            "t_value": thickness,
            "status": "N",
            "code_instrument": "A20230626002",
            "time_series": no,
            "time_insert": datetime.now().strftime('%H:%M:%S'),
            "created_date": datetime.now().strftime('%Y-%m-%d')
        }
        print(data)
        with open("data_log_testing.txt", "a") as file:
                file.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')}: {data}\n")

        try:
            with open('data_cetak.json', 'r') as json_file:
                existing_data = json.load(json_file)
        except (FileNotFoundError, json.JSONDecodeError):
            existing_data = []

        # Append new data to the list
        existing_data.append(data)

        # Write updated data to the JSON file
        with open('data_cetak.json', 'w') as json_file:
            json.dump(existing_data, json_file, indent=4)
        
        # Save to database
        self.save_to_database(data)

    def save_to_database(self, data):
        # Use the class method to save data to database
        Data.kirim_data(
            h_value=data["h_value"],
            d_value=data["d_value"],
            t_value=data["t_value"],
            status=data["status"],
            code_instrument=data["code_instrument"],
            time_series=data["time_series"]
        )

    def send_data_to_server(self, no, hardness, diameter, thickness, Tanggal, Time):
        id_counter_file = 'id_counter.txt'
        log_filename = 'log.json'
        
        id_counter = load_id_counter(id_counter_file)  # Load ID counter from file

        # Data object to send with incrementing ID
        data_object = {
            'id': id_counter,
            'h_value': hardness,
            'd_value': diameter,
            't_value': thickness,
            'status': "N",
            'code_instrument': "A20230626002",
            'time_series': no,
            'time_insert': datetime.now().strftime('%H:%M:%S'),
            'created_date': datetime.now().strftime('%Y-%m-%d')
        }

        # Serialize data object
        data = pickle.dumps(data_object)

        try:
            # Setup client socket
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect(('localhost', 12345))

            # Send data
            client_socket.sendall(data)
            print(f"Data sent: {data_object}")

            client_socket.close()
        except ConnectionRefusedError:
            print("Server is not running. Retrying in 5 seconds...")

        # Increment the ID counter
        id_counter += 1
        
        # Save the updated ID counter to file
        save_id_counter(id_counter_file, id_counter)

        # Append the log entry to the JSON log file
        append_log(log_filename, data_object)

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
    print(append_log)

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

if __name__ == "__main__":
    Reading = SerialReader()
    Reading.start()
    while True:
        time.sleep(1)
        print('print last')
    