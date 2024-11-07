import serial
import threading
import re
import time
import sqlalchemy
import logging
from sqlalchemy import create_engine, Column, Float, Integer, String
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

# Initialize global variables
bef = 0
count = 1
prevCount = 0
buffer = ""
Arbffr = [[]]
thickness= ""
diameter = ""
hardness= ""
#time_insert = ""

# Configure logging
logging.basicConfig(filename='serial_log.txt', level=logging.ERROR, format='%(asctime)s [%(levelname)s] %(message)s')

# Get the current date in the desired format
tanggal_waktu_terformat = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

# Konfigurasi koneksi ke database PostgreSQL
db_url ="postgresql://users_pims_engineer:Engineer_2023@10.106.1.40/pims_prod"
#db_url = "mysql+mysqlconnector://ems_saka:s4k4f4rmA@10.126.15.138:3306/pims_prod"

#db_url = "mysql+mysqlconnector://ems_saka:s4k4f4rmA@10.126.15.138:3306/ems_saka"
engine = create_engine(db_url, pool_pre_ping=True)
# engine = create_engine(db_url)

# Buat kelas model untuk tabel data
Base = sqlalchemy.orm.declarative_base()
# Define the Data class
class Data(Base):
    __tablename__ = 'sakaplant_prod_ipc_staging'

    id_setup = Column(Integer, primary_key=True)
    h_value = Column(Float)
    d_value = Column(Float)
    t_value = Column(Float)
    status = Column(String)
    code_instrument = Column(String)
    #time_insert = Column(String)

    @classmethod
    def kirim_data(cls, h_value, d_value, t_value, status, code_instrument ):
        data_baru = cls(h_value=h_value,
                        d_value=d_value,
                        t_value=t_value,
                        status=status,
                        code_instrument=code_instrument)
                        #time_insert=time_date
        session.add(data_baru)
        session.commit()

Session = sessionmaker(bind=engine)
session = Session()

serial_port = None


def initialize_serial():
    global serial_port, tanggal_waktu_terformat
    while True:
        try:
            serial_port = serial.Serial(port="COM4", baudrate=9600, timeout=1)
            serial_port.reset_input_buffer()
            print(f"Serial connection established. {tanggal_waktu_terformat}")
                
            break
        except serial.SerialException as e:
            print(f"Serial connection failed: {e}")
            print(tanggal_waktu_terformat)
            


initialize_serial()  # Initialize the serial connection

class SerialReader:
    
    def init(self):
        self.thread = threading.Thread(target=self._read_thread)
        self.thread.daemon = True

    def start(self):
        self.thread.start()

    def _read_thread(self):
    global serial_port, bef, buffer, Arbffr, prevCount, tanggal_waktu_terformat
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
                            batch = data[22]
                            speed = data[24]
                            Tanggal = data[28]
                            Time = data[30]
                            no = data[48]
                            thickness = float(data[50])
                            diameter = float(data[53])
                            hardness = float(data[56])
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
                            print(thickness, diameter, hardness, Tanggal, tanggal_waktu_terformat)
                            Data.kirim_data(hardness, diameter, thickness, "N", "A20230626002")
                            
                        except (ValueError, IndexError) as conversion_error:
                            print(f"Data conversion error: {conversion_error}")
                            bef = 0
                            buffer = ""
                            prevCount = 0
                            count = 1
                            data = ""
                            Arbffr = [[]]
                            continue 

                    elif "No." in data and len(data) < 20:
                        try:
                            no = data[1]
                            thickness = float(data[3])
                            diameter = float(data[6])
                            hardness = float(data[9])
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
                            # Menyimpan data ke kolom time_series sebagai integer
                            time_series = int(no)  # Mengambil nomor 'No. x'
                            Data.kirim_data(hardness, diameter, thickness, time_series, "A20230626002")
                            print(f"Data saved: No.{time_series} - {thickness} mm, {diameter} mm, {hardness} kp")
                            
                        except (ValueError, IndexError) as conversion_error:
                            print(f"Data conversion error: {conversion_error}")
                            bef = 0
                            buffer = ""
                            prevCount = 0
                            count = 1
                            data = ""
                            Arbffr = [[]]
                            continue  # Skip the current data and continue to the next 

                    elif "Xm" in data or "Xmean" in data or "Released:" in data:
                        bef = 0
                        buffer = ""
                        prevCount = 0
                        count = 1
                        data = ""
                        Arbffr = [[]]
                        with open("data_log.txt", "a") as file:
                            file.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')}: {data}\n")


        except serial.SerialException as e:
            print(f"Serial exception: {e}")
            serial_port = None  # Set ser to None to trigger reconnection
            time.sleep(5)  # Wait for 5 seconds before attempting to reconnect

if __name__ == "__main__":
    Reading = SerialReader()
    Reading.start()

    while True:
        # Read and assign values from global variables
        h_value = hardness
        d_value = diameter
        t_value = thickness
        status = ""
        code_instrument = "A20230626002"
        created_date = tanggal_waktu_terformat
        #time_insert = time
        #print(thickness, diameter, hardness, tanggal_waktu_terformat, time)

        # Print or use the values as needed
        #if (hardness != ""):
            #print(h_value, d_value, t_value, status, code_instrument)
