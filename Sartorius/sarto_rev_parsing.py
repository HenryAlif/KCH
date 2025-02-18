import serial
import logging
import re
from sqlalchemy import create_engine, Column, Float, Integer, String, func, Date, Time
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

# Configure logging
logging.basicConfig(filename="sartorius_serial_log.txt", level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# Define the ORM model
Base = declarative_base()

class ScalesData(Base):
    __tablename__ = "sakaplant_prod_ipc_scale_staging"
    id_setup = Column(Integer, primary_key=True, autoincrement=True)
    scale_weight = Column(Float)
    created_date = Column(Date, default=func.current_date())
    created_time = Column(Time, default=func.current_time())
    instrument_code = Column(String, default='0039304643')

# Open the serial port
def open_serial_port(port, baudrate=1200, timeout=1):
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
    try:
        logging.info(f"Raw data received:\n{data}")
        with open("raw_data_log.txt", "a") as raw_file:
            raw_file.write(f"{data}\n")

        # Clean and split data
        data = re.sub(r"-{2,}", "", data).strip()
        lines = [line.strip() for line in data.split("\n") if line.strip()]

        # Extract metadata
        date, time = lines[0].split()[:2]
        mod = re.search(r"Mod\.\s+(\S+)", data).group(1)
        ser_no = re.search(r"SerNo\.\s+(\S+)", data).group(1)
        APC = re.search(r"APC:\s+([\d\-\.]+)", data).group(1)
        BAC = re.search(r"BAC:\s+([\d\-\.]+)", data).group(1)
        l_id = re.search(r"L ID\s+(\S+)", data).group(1)
        operator = re.search(r"Name:\s+([A-Za-z]+)", data).group(1)

        # Find weight entries
        weight_entries = re.findall(r"N\s+\+\s+([\d\.]+)\s+([mg|g]+)", data)
        trial_no = 1

        for weight, unit in weight_entries:
            new_entry = ScalesData(
                scale_weight=float(weight)
            )
            session.add(new_entry)
            trial_no += 1

        session.commit()
        logging.info(f"Data saved successfully. Total entries: {len(weight_entries)}")
    except Exception as e:
        logging.error(f"Error processing data: {e}")

def read_and_process_data(ser, session, port, baudrate, timeout):
    buffer = ""
    while True:
        try:
            line = ser.readline().decode("utf-8", errors="replace").strip()
            if line:
                buffer += line + "\n"
                if "Name:" in line:  # Assuming "Name" indicates the end of a batch
                    process_data(buffer, session)
                    buffer = ""
        except serial.SerialException as e:
            logging.error(f"Serial exception occurred: {e}")
            ser.close()
            ser = open_serial_port(port, baudrate, timeout)
        except Exception as e:
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
    usb_port = "/dev/ttyUSB0"  # Adjust to your actual port
    baudrate = 1200
    timeout = 1

    ser = open_serial_port(usb_port, baudrate, timeout)

    try:
        read_and_process_data(ser, session, usb_port, baudrate, timeout)
    except KeyboardInterrupt:
        ser.close()
        logging.info("Program terminated by user.")
    except Exception as e:
        logging.exception(f"Exiting program: {e}")

if __name__ == "__main__":
    main()
