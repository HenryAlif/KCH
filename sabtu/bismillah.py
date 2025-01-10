import serial
import threading
import re
import time
import logging
import sqlalchemy
import csv
# import RPi.GPIO as GPIO
from sqlalchemy import create_engine, Column, Float, Integer, String
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime


# Configure logging
logging.basicConfig(filename="cetak_serial_log.csv", level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logging.basicConfig(filename="cetak_serial_log.xlsx", level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logging.basicConfig(filename='false_log.csv', level=logging.ERROR, format='%(asctime)s [%(levelname)s] %(message)s')

# Define the ORM model
Base = declarative_base()

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

# Get the current date in the desired format
tanggal_waktu_terformat = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

# Konfigurasi koneksi ke database PostgreSQL

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

class Log(Base):
    __tablename__ = 'error_log'

    Id = Column(Integer, primary_key=True)
    error = Column(String)
    time = Column(String)

    @classmethod
    def kirim_log(cls, 
                error, 
                time):
        lognya = cls(error=error, time=time)
# Open the serial port
def open_serial_port(port, baudrate=9600, timeout=1):
    while True:
        try:
            ser = serial.Serial(
                port=port,
                baudrate=baudrate,
                bytesize=serial.SEVENBITS,
                parity=serial.PARITY_ODD,
                stopbits=serial.STOPBITS_ONE,
                xonxoff=True,
                rtscts=True,
                dsrdtr=True,
                timeout=timeout
            )
            print(f"Serial port {port} opened successfully.")
            logging.info(f"Serial port {port} opened successfully.")
            return ser
        except serial.SerialException as e:
            print(f"Error opening serial port {port}: {e}")
            logging.error(f"Error opening serial port {port}: {e}")
            time.sleep(5)

def process_data(data, session):
        global serial_port, bef, buffer, Arbffr, prevCount, tanggal_waktu_terformat, last_error_message
        while True:
            try:
                if serial_port is None:
                    open_serial_port()
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

                                #print(no, thickness, diameter, hardness, Tanggal, tanggal_waktu_terformat)
                                Data.kirim_data(hardness, diameter, thickness, "N", "A20230626002", time_series=no)
                                with open("data_log.csv", "a") as file:
                                    #file.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')}: {no, thickness, diameter, hardness, Tanggal, tanggal_waktu_terformat}\n")
                                    file.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')}: {no}, {thickness}, {diameter}, {hardness}, {Tanggal}, {tanggal_waktu_terformat}\n")


                            except (ValueError, IndexError) as conversion_error:
                                error_message = f"Data CONVERSION: {conversion_error}"
                                logging.error(error_message)
                                print(error_message)
                                
                                # Cek apakah error sama sudah dikirim sebelumnya
                                if last_error_message != error_message:
                                    Log.kirim_log(error=error_message, time=tanggal_waktu_terformat)
                                    last_error_message = error_message  # Simpan pesan error terakhir yang dikirim
                                
                                bef = 0
                                buffer = ""
                                prevCount = 0
                                count = 1
                                data = ""
                                Arbffr = [[]]
                                continue 

                        elif "No." in data and len(data) < 20:
                            #data = re.split(r"\s+|\n", buffer)
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
                                
                                #print(no, thickness, diameter, hardness, Tanggal, tanggal_waktu_terformat)
                                with open("data_log.csv", "a") as file:
                                    file.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')}: {no, thickness, diameter, hardness, Tanggal, tanggal_waktu_terformat}\n")
                                    #file.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')}: {no}, {thickness}, {diameter}, {hardness}, {Tanggal}, {tanggal_waktu_terformat}\n")
                                Data.kirim_data(hardness, diameter, thickness, "N", "A20230626002", time_series=no)
                            
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
                    Log.kirim_log(error=error_message, time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                    last_error_message = error_message  # Simpan pesan error terakhir yang dikirim
                serial_port = None
                time.sleep(5)

def main():
    # Database setup
    db_url = "postgresql://users_pims_engineer:Engineer_2023@10.106.1.40/pims_prod"
    engine = create_engine(db_url, pool_pre_ping=True)
    Base = sqlalchemy.orm.declarative_base()
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    # Serial port setup
    usb_port = "COM6"  # Adjust to your actual port
    baudrate = 9600
    timeout = 1

    ser = open_serial_port(usb_port, baudrate, timeout)

    try:
        process_data(ser, session, usb_port, baudrate, timeout)
    except KeyboardInterrupt:
        ser.close()
        logging.info("Program terminated by user.")
    except Exception as e:
        logging.exception(f"Exiting program: {e}")

if __name__ == "__main__":
    main()
