import re
import logging
import serial
import time
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker, declarative_base

logging.basicConfig(filename='serial_log.txt', level=logging.ERROR, format='%(asctime)s [%(levelname)s] %(message)s')

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

Base = declarative_base()

from sqlalchemy import Column, Integer, String, Float
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class DisinData(Base):
    __tablename__ = "DisintegrationTester"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user = Column(String)         
    product = Column(String)      
    batch = Column(String)        
    medium = Column(String)       
    max_time = Column(String)     
    bath_temp = Column(String)    
    target_temp = Column(String)  
    basket = Column(String)       
    sample_1 = Column(String)     
    sample_2 = Column(String)     
    sample_3 = Column(String)     
    sample_4 = Column(String)     
    sample_5 = Column(String)     
    sample_6 = Column(String)     
    mean_value = Column(String)   
    abs_std_dev = Column(String)  
    rel_std_dev = Column(String)  
    time = Column(String)         
    date = Column(String)         

def setup_database():
    # Create an SQLite database (or connect to one)
    engine = create_engine('mysql+mysqlconnector://ems_saka:s4k4f4rmA@10.126.15.138:3306/ems_saka', echo=False)  
    
    # Create all tables in the database (if not exist)
    Base.metadata.create_all(engine)
    
    # Create a session to interact with the database
    Session = sessionmaker(bind=engine)
    return Session()