import serial
import time
import logging
import re
import sqlalchemy
from sqlalchemy import create_engine, Column, Float, Integer, String
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

# Configure logging
logging.basicConfig(filename='serial_log.txt', level=logging.ERROR, format='%(asctime)s [%(levelname)s] %(message)s')

# Buat kelas model untuk tabel data
Base = declarative_base()

class MoistureData(Base):
    __tablename__ = "newmoist"
    
    id = Column(Integer, primary_key=True)
    Operator = Column(String)
    Batch = Column(String)
    Limit_atas = Column(Float)
    Limit_bawah = Column(Float)
    Berat_awal = Column(Float)
    Berat_kering = Column(Float)
    Moisture = Column(Float)
    Result = Column(Float)
    Status = Column(String)
    Date = Column(String)

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

def process_data(data):
    """Process the received data."""
    # Add your data processing logic here
    # For example, you might parse the data and extract relevant information
    db_url = "mysql+mysqlconnector://ems_saka:s4k4f4rmA@10.126.15.138:3306/ems_saka"
    engine = create_engine(db_url, pool_pre_ping=True)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    Data_split = re.split(r'\s{2,}',data)
    Data_length = len(Data_split)
    #print(Data_split)
    print(Data_length)
    
    if Data_length == 69:
        Datab = MoistureData(Operator = Data_split[9],
                            Batch = Data_split[46],
                            Limit_atas=float(Data_split[35]),   
                            Limit_bawah=float(Data_split[41]),  
                            Berat_awal=float(Data_split[50]),   
                            Berat_kering=float(Data_split[54]), 
                            Moisture=float(Data_split[56]),     
                            Result=float(Data_split[58]),       
                            Status = Data_split[60],
                            Date = Data_split[66])
        
        print(Data_split[66])
        print("data parsing normal")
        session.add(Datab)
        session.commit()
        
    elif Data_length == 68:
        Datab = MoistureData(Operator = Data_split[9],
                        Batch = Data_split[45],
                        Limit_atas=float(Data_split[35]),   
                        Limit_bawah=float(Data_split[41]),  
                        Berat_awal=float(Data_split[49]),   
                        Berat_kering=float(Data_split[53]), 
                        Moisture=float(Data_split[55]),     
                        Result=float(Data_split[57]),       
                        Status = Data_split[59],
                        Date = Data_split[65])
        
        print(Data_split[65])
        #print(Data_split)
        print("data parsing kurang 1")
        session.add(Datab)
        session.commit()
    else:
        print("Data tidak di parsing")
                
    #value =int(Data_split[0])
    #session = Session()
    #moisture_data = MoistureData (value=value)
    #session.add(moisture_data)
    #session.commit()
    #session.close()

    # Example: Write data to a file
    with open("data_log.txt", "a") as file:
        file.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')}: {data}\n")

def main():
    # Replace '/dev/ttyUSB0' with the actual USB port
    usb_port = 'COM3'

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
