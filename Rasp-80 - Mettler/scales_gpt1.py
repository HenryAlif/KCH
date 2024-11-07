import re
import logging
import serial
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
    n = Column(Float)  # Change to Float since you want n as a float value
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
    engine = create_engine('mysql+mysqlconnector://ems_saka:s4k4f4rmA@10.126.15.138:3306/ems_saka', echo=False)  # Set a valid database URL
    
    # Create all tables in the database (if not exist)
    Base.metadata.create_all(engine)
    
    # Create a session to interact with the database
    Session = sessionmaker(bind=engine)
    return Session()


# Function to clean and convert numeric values, removing units and unwanted characters
def clean_numeric_value(value):
    # Remove units like "g" and unwanted text, and convert to float if possible
    cleaned_value = re.sub(r'[^\d.-]', '', value)
    try:
        return float(cleaned_value)
    except ValueError:
        return 0  # Return 0 if it's not a valid number

# Function to process the input data and add to the database
def process_and_store_data(data, session):
    # Splitting the data based on newline
    Data_split = data.strip().split('\n')
    
    # Ensure Data_split has enough elements
    if len(Data_split) < 10:
        logging.error(f"Data split is too short: {Data_split}")
        return
    
    try:
        # Extract the relevant values dynamically
        operator = None
        n = x = s_dev = s_rel = min_value = max_value = diff = sum_value = None
        date = None

        for line in Data_split:
            line = line.strip()
            logging.info(f"Processing line: {line}")  # Log setiap baris yang diproses
            if "n" in line:
                n_value = line.split("n")[-1].strip()
                logging.info(f"Raw n value extracted: '{n_value}'")  # Log nilai mentah
                n = clean_numeric_value(n_value)
                logging.info(f"Extracted n value: {n}")  # Log nilai n setelah diproses

            # Extract operator (User name)
            if "User name" in line:
                operator = line.split("User name")[-1].strip()

            # Extract date
            if re.match(r'\d{2}\.\d{2}\.\d{4}', line):
                date = line.strip()

            if "x" in line:
                # Extract 'x' and convert it to float
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

        # Default values for missing numeric fields
        s_dev = s_dev if s_dev is not None else 0
        s_rel = s_rel if s_rel is not None else 0
        
        # Create a new ScalesData object
        Datab = ScalesData(
            operator=operator,
            n=n,  # Store n as float now
            x=x,
            s_dev=s_dev,
            s_rel=s_rel,
            min_value=min_value,
            max_value=max_value,
            diff=diff,
            sum_value=sum_value,
            date=date
        )

        # Logging the object that will be saved to the database
        logging.info(f"Data to be saved: Operator: {operator}, n: {n}, x: {x}, s_dev: {s_dev}, s_rel: {s_rel}, min_value: {min_value}, max_value: {max_value}, diff: {diff}, sum_value: {sum_value}, date: {date}")

        # Add the new instance to the session and commit to the database
        session.add(Datab)
        session.commit()
        logging.info("Data successfully added to the database.")
    except (IndexError, ValueError) as e:
        logging.error(f"Error processing data: {e}")

# Main function
if __name__ == "__main__":
    # Setup database session
    session = setup_database()

    # Setup serial port configuration
    ser = serial.Serial(
        port='COM5',  # Sesuaikan dengan port serial Anda /dev/ttyACM0
        baudrate=9600,      # Sesuaikan dengan baudrate perangkat Anda
        timeout=1
    )

    try:
        print("Menunggu data serial masuk...")
        buffer = ''
        while True:
            if ser.in_waiting > 0:
                # Read incoming data
                data_bytes = ser.read(ser.in_waiting)
                buffer += data_bytes.decode('utf-8', errors='ignore')
                
                # Check if end of message (e.g., by looking for specific delimiter)
                if '========================' in buffer:
                    # Process complete message
                    logging.info("Data lengkap diterima dari port serial.")
                    process_and_store_data(buffer, session)
                    # Clear buffer for next message
                    buffer = ''
            time.sleep(0.1)  # Jeda kecil untuk mencegah penggunaan CPU yang tinggi
    except KeyboardInterrupt:
        print("Program dihentikan oleh pengguna.")
    except Exception as e:
        logging.error(f"Terjadi kesalahan: {e}")
    finally:
        if ser.is_open:
            ser.close()
