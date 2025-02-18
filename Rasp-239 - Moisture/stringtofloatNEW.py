import re
import serial
import time
import logging
import sqlalchemy
from sqlalchemy import create_engine, Column, Float, Integer, Date, Time, String, func
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
    
Base = declarative_base()

class MoistureData(Base):
    __tablename__ = "sakaplant_prod_ipc_ma_staging"
    id_setup = Column(Integer, primary_key=True)
    start_weight = Column(Float)   
    end_weight = Column(Float) 
    created_date = Column(Date, default=func.current_date())
    created_time = Column(Time, default=func.current_time())
    instrument_code = Column(String, default='MA2025001')

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
    
    db_url = "mysql+mysqlconnector://root:s4k4f4rmA@10.126.15.138:3306/ems_saka"
    engine = create_engine(db_url, pool_pre_ping=True)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    Data_split = re.split(r'\s{2,}', data)
    Data_length = len(Data_split)
    print(Data_length)

    print(f"Data yang diterima: {Data_split}")
    print(f"Panjang data: {Data_length}")
    
    if Data_length == 69:
        Datab = MoistureData( 
        start_weight=float(clean_numeric_value(Data_split[50])),   
        end_weight=float(clean_numeric_value(Data_split[54]))
    )
        print(Data_split[66])
        print("Data parsing normal")
        session.add(Datab)
        session.commit()

    elif Data_length == 68:
        Datab = MoistureData(
            start_weight=float(clean_numeric_value(Data_split[49])),   
            end_weight=float(clean_numeric_value(Data_split[53]))
    )
        print(Data_split[65])
        print("Data parsing kurang 1")
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
    usb_port = '/dev/ttyUSB0'

    try:
        # Open the serial port
        ser = open_serial_port(usb_port)

        try:
            # Read and process data
            read_and_process_data(ser, encoding='latin-1')
            """read_and_process_data(ser)"""

        except KeyboardInterrupt:
            # Close the serial port on keyboard interrupt
            close_serial_port(ser)

    except Exception as e:
        print(f"Exiting program: {e}")
        logging.exception(f"Exiting program: {e}")

if __name__ == "__main__":
    
    main()

