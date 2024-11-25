import re
import serial
import time
import logging
from datetime import datetime
from sqlalchemy import create_engine, Column, Float, Integer, String
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class ScalesData(Base):
    __tablename__ = "Sartorius_Scales"
    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(String)
    time = Column(String)
    mod = Column(String)
    ser_no = Column(String)
    APC = Column(String)
    BAC = Column(String)
    l_id = Column(String)
    l_id2 = Column(String)
    gram = Column(Float)

def open_serial_port(port, baudrate=9600, timeout=1):
    """Open a serial port and return the serial object."""
    while True:
        try:
            ser = serial.Serial(port, baudrate=baudrate, timeout=timeout)
            print(f"Serial port {port} opened successfully.")
            logging.info(f"Serial port {port} opened successfully.")
            return ser
        except serial.SerialException as e:
            error_message = f"Error opening serial port {port}: {e}"
            print(error_message)
            logging.error(error_message)
            print("Retrying in 5 seconds...")
            time.sleep(5)

def read_and_process_data(ser, encoding='utf-8'):
    """Read and process data from the serial port."""
    try:
        accumulated_data = ""
        
        while True:
            data = ser.readline().decode(encoding, errors='replace').strip()
            
            if data:
                accumulated_data += data + "  "
                
                if accumulated_data.endswith('---------  '):
                    process_data(accumulated_data)
                    accumulated_data = ""
        
    except serial.SerialException as e:
        error_message = f"Error reading data from serial port: {e}"
        print(error_message)
        logging.error(error_message)
        print("Attempting to reconnect...")
        ser = open_serial_port(usb_port)  # Reopen the serial port
        read_and_process_data(ser, encoding)  # Continue reading and processing data with the same encoding

def clean_numeric_value(value):
    cleaned_value = re.sub(r'[^\d.-]', '', value)  # Menghapus karakter selain angka, minus, dan titik
    return cleaned_value

def process_data(data):
    """Process the received data."""
    
    db_url = "mysql+mysqlconnector://ems_saka:s4k4f4rmA@10.126.15.138:3306/ems_saka"  # Database URL harus disesuaikan
    engine = create_engine(db_url, pool_pre_ping=True)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    Data_split = re.split(r'\s{2,}', data)
    Data_length = len(Data_split)
    
    if Data_length == 69:
        Datab = ScalesData(
            date=Data_split[0],
            time=Data_split[1],
            mod=Data_split[2],
            ser_no=Data_split[3],
            APC=Data_split[4],
            BAC=Data_split[5],
            l_id=Data_split[6],
            l_id2=Data_split[7],
            gram=float(clean_numeric_value(Data_split[8]))  # Konversi ke float
        )
        session.add(Datab)
        session.commit()

    elif Data_length == 68:
        Datab = ScalesData(
            date=Data_split[0],
            time=Data_split[1],
            mod=Data_split[2],
            ser_no=Data_split[3],
            APC=Data_split[4],
            BAC=Data_split[5],
            l_id=Data_split[6],
            l_id2=Data_split[7],
            gram=float(clean_numeric_value(Data_split[8]))  # Konversi ke float
        )
        session.add(Datab)
        session.commit()

    else:
        print("Data tidak di parsing")
    
    with open("data_log.txt", "a") as file:
        file.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')}: {data}\n")

def close_serial_port(ser):
    """Close the serial port."""
    try:
        ser.close()
        print("Serial port closed.")
        logging.info("Serial port closed.")
    except serial.SerialException as e:
        error_message = f"Error closing serial port: {e}"
        print(error_message)
        logging.error(error_message)

def main():
    # Replace '/dev/ttyUSB0' with the actual USB port
    usb_port = 'COM3'

    try:
        # Open the serial port
        ser = open_serial_port(usb_port)

        try:
            # Read and process data
            read_and_process_data(ser, encoding='latin-1')

        except KeyboardInterrupt:
            # Close the serial port on keyboard interrupt
            close_serial_port(ser)

    except Exception as e:
        print(f"Exiting program: {e}")
        logging.exception(f"Exiting program: {e}")

if __name__ == "__main__":
    
    main()
