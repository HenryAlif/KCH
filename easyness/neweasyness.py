import serial
import threading
import re
import time
import logging
import sqlalchemy
import mysql.connector
from sqlalchemy import create_engine, Column, Float, Integer, String
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

logging.basicConfig(filename='serial_log.txt', level=logging.ERROR, format='%(asctime)s [%(levelname)s] %(message)s')
logging.basicConfig(filename='info_log.txt', level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

# Initialize global variables
bef = 0
count = 1
prevCount = 0
buffer = ""
Arbffr = [[]]
thickness = ""
diameter = ""
hardness = ""
time_series = ""

# Variabel untuk menyimpan error terakhir
last_error_message = None

# Get the current date in the desired format
tanggal_waktu_terformat = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

# Konfigurasi koneksi ke database PostgreSQL menggunakan SQLAlchemy
db_url_postgresql = db_url = "postgresql://users_pims_engineer:Engineer_2023@10.106.1.40/pims_prod"
engine_postgresql = create_engine(db_url_postgresql, pool_pre_ping=True)
Base = sqlalchemy.orm.declarative_base()

# Konfigurasi koneksi ke database MySQL menggunakan mysql-connector-python
conn_mysql = mysql.connector.connect(
    host="10.126.15.138",
    user="root",
    password="s4k4f4rmA",
    database="ems_saka"
)
cursor_mysql = conn_mysql.cursor()

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
    def kirim_data(cls, session_postgresql, h_value, d_value, t_value, status, code_instrument, time_series):
        # Kirim data ke PostgreSQL
        data_baru = cls(
            h_value=h_value, 
            d_value=d_value, 
            t_value=t_value,
            status=status, 
            code_instrument=code_instrument, 
            time_series=time_series
        )
        session_postgresql.add(data_baru)
        session_postgresql.commit()

        # Kirim data ke MySQL
        query_mysql = """
            INSERT INTO sakaplant_prod_ipc_staging (h_value, d_value, t_value, status, code_instrument, time_series)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        cursor_mysql.execute(query_mysql, (h_value, d_value, t_value, status, code_instrument, time_series))
        conn_mysql.commit()

class Log(Base):
    __tablename__ = 'error_log'

    Id = Column(Integer, primary_key=True)
    error = Column(String)
    time = Column(String)

    @classmethod
    def kirim_log(cls, session_postgresql, error, time):
        # Kirim log ke PostgreSQL
        lognya = cls(error=error, time=time)
        session_postgresql.add(lognya)
        session_postgresql.commit()

        # Kirim log ke MySQL
        query_mysql = """
            INSERT INTO error_log (error, time)
            VALUES (%s, %s)
        """
        cursor_mysql.execute(query_mysql, (error, time))
        conn_mysql.commit()

Session_postgresql = sessionmaker(bind=engine_postgresql)
session_postgresql = Session_postgresql()

serial_port = None

def close_serial():
    global serial_port
    if serial_port and serial_port.is_open:
        serial_port.close()
        print("Serial port closed.")

def initialize_serial():
    global serial_port, tanggal_waktu_terformat, last_error_message
    while True:
        try:
            serial_port = serial.Serial(port="COM", baudrate=9600, timeout=1)
            serial_port.reset_input_buffer()
            print(f"Serial connection established. {tanggal_waktu_terformat}")
            logging.info(f"Serial connection established on {serial_port.port} with baudrate {serial_port.baudrate} at {tanggal_waktu_terformat}")
            error_message = f"ESTABLISHED {serial_port.port} at {tanggal_waktu_terformat}"
            Log.kirim_log(session_postgresql, error=error_message, time=tanggal_waktu_terformat)
            time.sleep(2)
            break
        except serial.SerialException as e:
            error_message = f"Serial FAILED: {e}"
            print(error_message)
            logging.error(error_message)
            
            # Cek apakah error sama sudah dikirim sebelumnya
            if last_error_message != error_message:
                Log.kirim_log(session_postgresql, error=error_message, time=tanggal_waktu_terformat)
                last_error_message = error_message  # Simpan pesan error terakhir yang dikirim
            time.sleep(5)
            print(tanggal_waktu_terformat)

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

                                Data.kirim_data(session_postgresql, hardness, diameter, thickness, "N", "A20230626002", time_series=no)
                                with open("data_log.txt", "a") as file:
                                    file.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')}: {no}, {thickness}, {diameter}, {hardness}, {Tanggal}, {tanggal_waktu_terformat}\n")

                            except (ValueError, IndexError) as conversion_error:
                                error_message = f"Data CONVERSION: {conversion_error}"
                                logging.error(error_message)
                                print(error_message)
                                
                                # Cek apakah error sama sudah dikirim sebelumnya
                                if last_error_message != error_message:
                                    Log.kirim_log(session_postgresql, error=error_message, time=tanggal_waktu_terformat)
                                    last_error_message = error_message  # Simpan pesan error terakhir yang dikirim
                                
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
                                Arbffr[prevCount].append(batch)
                                Arbffr[prevCount].append(speed)
                                Arbffr[prevCount].append(Tanggal)
                                Arbffr[prevCount].append(Time)
                                Arbffr[prevCount].append(thickness)
                                Arbffr[prevCount].append(diameter)
                                Arbffr[prevCount].append(hardness)
                                prevCount = count

                                buffer = ""
                                
                                with open("data_log.txt", "a") as file:
                                    file.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')}: {no, thickness, diameter, hardness, Tanggal, tanggal_waktu_terformat}\n")
                                Data.kirim_data(session_postgresql, hardness, diameter, thickness, "N", "A20230626002", time_series=no)
                            
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
                print(f"Serial exception: {e}")
                print(error_message)
                logging.error(error_message)
                
                # Cek apakah error sama sudah dikirim sebelumnya
                if last_error_message != error_message:
                    Log.kirim_log(session_postgresql, error=error_message, time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                    last_error_message = error_message  # Simpan pesan error terakhir yang dikirim
                serial_port = None
                time.sleep(5)

if __name__ == "__main__":
    Reading = SerialReader()
    Reading.start()
    while True:
        h_value         = hardness
        d_value         = diameter
        t_value         = thickness
        status          = ""
        code_instrument = "A20230626002"
        created_date    = tanggal_waktu_terformat
        time_series     = time_series

        if (hardness != ""):
            with open("data_log.txt", "a") as file:
                file.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')}: {Arbffr}\n")
                file.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')}: {time_series}, {thickness}, {diameter}, {hardness}, {tanggal_waktu_terformat}\n")