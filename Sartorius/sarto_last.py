import serial
import time
import logging
import re
from sqlalchemy import create_engine, Column, Float, Integer, String
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

# Configure logging
logging.basicConfig(filename='sartorius_serial_log.txt', level=logging.ERROR, format='%(asctime)s [%(levelname)s] %(message)s')

# Define the ORM model
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
    gram = Column(Float)

def open_serial_port(port, baudrate=1200, timeout=1):
    """Open the serial port with specific settings."""
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

def close_serial_port(ser):
    """Close the serial port."""
    try:
        ser.close()
        print("Serial port closed.")
        logging.info("Serial port closed.")
    except serial.SerialException as e:
        print(f"Error closing serial port: {e}")
        logging.error(f"Error closing serial port: {e}")

def process_data(data, session):
    """Process the received data and store it in the database."""
    try:
        logging.info(f"Raw data received:\n{data}")
        with open("raw_data_log.txt", "a") as raw_file:
            raw_file.write(f"{data}\n")

        # Clean up unnecessary lines
        data = re.sub(r'-{2,}', '', data).strip()
        lines = [line.strip() for line in data.split('\n') if line.strip()]

        # Validate data format
        if len(lines) < 8:
            logging.warning(f"Data format error: Insufficient lines in data. Received {len(lines)} lines.")
            return

        # Extract details
        date, time = lines[0].split()[:2]
        ser_no = lines[3].split()[-1]
        mod = lines[2].split()[-1]
        APC = lines[4].split(':', 1)[-1].strip()
        BAC = lines[5].split(':', 1)[-1].strip()
        l_id = None
        gram = None

        # Find L ID
        for line in lines:
            if line.startswith("L ID"):
                l_id = line.split()[-1]
                break

        if not l_id:
            logging.warning(f"Failed to extract L ID from data: {data}")
            return

        # Find the line containing gram value
        gram_line = next((line for line in lines if re.search(r'[+-]?\d+\.\d+\s*g', line)), None)
        if not gram_line:
            logging.warning(f"Gram value not found in data: {data}")
            return

        # Extract gram value
        gram_match = re.search(r'[+-]?\d+\.\d+', gram_line)
        if gram_match:
            gram = float(gram_match.group())
        else:
            logging.warning(f"Failed to extract gram value from line: {gram_line}")
            return

        # Save to database
        new_entry = ScalesData(
            date=date,
            time=time,
            mod=mod,
            ser_no=ser_no,
            APC=APC,
            BAC=BAC,
            l_id=l_id,
            l_id2=None,  # You can add logic here if l_id2 is provided
            gram=gram
        )
        session.add(new_entry)
        session.commit()
        logging.info(f"Data saved: {new_entry}")
    except ValueError as ve:
        logging.error(f"Data validation error: {ve}")
    except Exception as e:
        logging.error(f"Error processing data: {e}")

# def read_serial_data():
#     """Read data from the serial port and process it."""
#     try:
#         with serial.Serial(usb_port, baudrate, timeout=1) as ser:
#             logging.info(f"Serial port {usb_port} opened successfully.")
#             while True:
#                 raw_data = ser.read_until(b"\n\n").decode("utf-8", errors="ignore").strip()
#                 if raw_data:
#                     process_data(raw_data, session)
#     except serial.SerialException as e:
#         logging.error(f"Error opening or using the serial port: {e}")
#     except KeyboardInterrupt:
#         logging.info("Program terminated by user.")


def read_and_process_data(ser, session, port, baudrate, timeout):
    """Read and process data from the serial port."""
    buffer = ""
    while True:
        try:
            # Attempt to read a line of data
            line = ser.readline().decode('utf-8', errors='replace').strip()
            if line:
                buffer += line + "\n"
                if "g" in line:  # End of a reading
                    process_data(buffer, session)
                    buffer = ""
        except serial.SerialException as e:
            print(f"Serial exception occurred: {e}")
            logging.error(f"Serial exception occurred: {e}")
            ser.close()  # Close the port safely
            print("Attempting to reconnect...")
            ser = open_serial_port(port, baudrate, timeout)  # Attempt to reconnect
        except Exception as e:
            print(f"Error reading data: {e}")
            logging.error(f"Error reading data: {e}")
            break

def main():
    # Database setup
    db_url = "mysql+mysqlconnector://ems_saka:s4k4f4rmA@10.126.15.138:3306/ems_saka"
    engine = create_engine(db_url, pool_pre_ping=True)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    # Serial port setup
    usb_port = "/dev/ttyUSB0"  # Replace with your port
    baudrate = 1200
    timeout = 1

    ser = open_serial_port(usb_port, baudrate, timeout)

    try:
        read_and_process_data(ser, session, usb_port, baudrate, timeout)
        # read_serial_data(usb_port, baudrate, session, ser, timeout)
    except KeyboardInterrupt:
        close_serial_port(ser)
    except Exception as e:
        print(f"Exiting program: {e}")
        logging.exception(f"Exiting program: {e}")

if __name__ == "__main__":
    main()
