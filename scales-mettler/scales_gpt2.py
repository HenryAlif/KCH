import re
import logging
import serial  # Untuk komunikasi serial
import time
from sqlalchemy import create_engine, Column, Float, Integer, String
from sqlalchemy.orm import sessionmaker, declarative_base

# Setup logging for errors
logging.basicConfig(level=logging.INFO)

# Base class for SQLAlchemy using declarative_base from sqlalchemy.orm
Base = declarative_base()

# Define the ScalesData class for the Mettler_Scales table
class ScalesData(Base):
    __tablename__ = "Mettler_Scales"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    operator = Column(String)
    n = Column(Float)
    x = Column(Float)
    s_dev = Column(Float)
    s_rel = Column(Float)
    min_value = Column(Float)
    max_value = Column(Float)
    diff = Column(Float)
    sum_value = Column(Float)
    date = Column(String)

# Setup the database connection
def setup_database():
    # Create an SQLite database (or connect to one)
    engine = create_engine('mysql+mysqlconnector://ems_saka:s4k4f4rmA@10.126.15.138:3306/ems_saka', echo=False)
    
    # Create all tables in the database (if not exist)
    Base.metadata.create_all(engine)
    
    # Create a session to interact with the database
    Session = sessionmaker(bind=engine)
    return Session()

# Function to clean and convert numeric values, removing units and unwanted characters
def clean_numeric_value(value):
    cleaned_value = re.sub(r'[^\d.-]', '', value)
    try:
        return float(cleaned_value)
    except ValueError:
        return 0  # Return 0 if it's not a valid number

# Function to process the input data and add to the database
def process_and_store_data(data, session):
    Data_split = data.strip().split('\n')
    
    if len(Data_split) < 10:
        logging.error(f"Data split is too short: {Data_split}")
        return
    
    try:
        operator = None
        n = x = s_dev = s_rel = min_value = max_value = diff = sum_value = None
        date = None

        for line in Data_split:
            line = line.strip()
            logging.info(f"Processing line: {line}")
            if "n" in line:
                n_value = line.split("n")[-1].strip()
                n = clean_numeric_value(n_value)
                logging.info(f"Extracted n value: {n}")

            if "User name" in line:
                operator = line.split("User name")[-1].strip()

            if re.match(r'\d{2}\.\d{2}\.\d{4}', line):
                date = line.strip()

            if "x" in line:
                x_value = line.split("x")[-1].strip()
                x = clean_numeric_value(x_value)

            if "s dev" in line:
                s_dev = clean_numeric_value(line.split("s dev")[-1].strip())
            if "s rel" in line:
                s_rel = clean_numeric_value(line.split("s rel")[-1].strip())
            if "Min." in line:
                min_value = clean_numeric_value(line.split("Min.")[-1].strip())
            if "Max." in line:
                max_value = clean_numeric_value(line.split("Max.")[-1].strip())
            if "Diff." in line:
                diff = clean_numeric_value(line.split("Diff.")[-1].strip())
            if "Sum" in line:
                sum_value = clean_numeric_value(line.split("Sum")[-1].strip())

        s_dev = s_dev if s_dev is not None else 0
        s_rel = s_rel if s_rel is not None else 0

        # Create a new ScalesData object
        Datab = ScalesData(
            operator=operator,
            n=n,
            x=x,
            s_dev=s_dev,
            s_rel=s_rel,
            min_value=min_value,
            max_value=max_value,
            diff=diff,
            sum_value=sum_value,
            date=date
        )

        logging.info(f"Data to be saved: Operator: {operator}, n: {n}, x: {x}, s_dev: {s_dev}, s_rel: {s_rel}, min_value: {min_value}, max_value: {max_value}, diff: {diff}, sum_value: {sum_value}, date: {date}")

        # Add the new instance to the session and commit to the database
        session.add(Datab)
        session.commit()
        logging.info("Data successfully added to the database.")
    except (IndexError, ValueError) as e:
        logging.error(f"Error processing data: {e}")

# Function to read data from serial port
def read_serial_data():
    ser = serial.Serial(
        port='/dev/ttyACM0',  # Adjust the port based on your Raspberry Pi setup
        baudrate=9600,
        timeout=1  # Timeout after 1 second if no data is received
    )
    while True:
        if ser.in_waiting > 0:
            try:
                line = ser.readline().decode('utf-8').strip()  # Read a line from the serial port
                logging.info(f"Serial data received: {line}")
                yield line  # Return the line read from the serial port
            except Exception as e:
                logging.error(f"Error reading from serial port: {e}")
        time.sleep(1)

# Main function
if __name__ == "__main__":
    session = setup_database()

    # Read data from serial and process it dynamically
    buffer = ""
    for serial_data in read_serial_data():
        buffer += serial_data + "\n"
        if "Signature" in serial_data:  # Assume 'Signature' indicates the end of the data block
            process_and_store_data(buffer, session)
            buffer = ""  # Reset buffer after processing a block of data
