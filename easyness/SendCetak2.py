import json
import os
import time
import logging
import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from sqlalchemy import create_engine, Column, Integer, Float, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import sqlalchemy.exc  # Pastikan Anda mengimpor sqlalchemy.exc untuk menangani pengecualian SQLAlchemy

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Create the Base class
Base = declarative_base()

# Define the database models
class Data(Base):
    __tablename__ = 'sakaplant_prod_ipc_staging'

    id_setup = Column(Integer, primary_key=True)
    h_value = Column(Float)
    d_value = Column(Float)
    t_value = Column(Float)
    status = Column(String)
    code_instrument = Column(String)
    time_series = Column(Integer)
    time_insert = Column(String)
    created_date = Column(String)

    @classmethod
    def kirim_data(cls, session, h_value, d_value, t_value, status, code_instrument, time_series, time_insert, created_date):
        data_baru = cls(
            h_value=h_value, 
            d_value=d_value, 
            t_value=t_value,
            status=status, 
            code_instrument=code_instrument, 
            time_series=time_series,
            time_insert=time_insert,
            created_date=created_date
        )
        session.add(data_baru)
        session.commit()

class Log(Base):
    __tablename__ = 'error_log'

    Id = Column(Integer, primary_key=True)
    error = Column(String)
    time = Column(String)

    @classmethod
    def kirim_log(cls, session, error, time):
        lognya = cls(error=error, time=time)
        session.add(lognya)
        session.commit()

# Database connection setup
DATABASE_URL = 'postgresql://users_pims_engineer:Engineer_2023@10.106.1.40/pims_prod' # Change to your database URL
engine = create_engine(DATABASE_URL)
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()

# Path to the JSON file
json_file_path = r'D:\Source Code\Magang Kalbe\Raspberry Pi\data_cetak.json'

# Set last_time_insert to midnight (00:00) of the current day
last_time_insert = "00:00:00"  # or you can use datetime.datetime.combine(datetime.date.today(), datetime.time.min) if you need a datetime object

def load_and_process_data(session, json_file_path, last_time_insert):
    try:
        if os.path.getsize(json_file_path) == 0:
            raise ValueError("File is empty")
        
        with open(json_file_path, 'r') as file:
            data = json.load(file)
        
        # Log the content of the JSON file for debugging
        logger.info(f"Loaded JSON data: {data}")

        for entry in data:
            # Validate that all required keys are present
            required_keys = ['h_value', 'd_value', 't_value', 'status', 'code_instrument', 'time_series', 'time_insert', 'created_date']
            if not all(key in entry for key in required_keys):
                missing_keys = [key for key in required_keys if key not in entry]
                logger.error(f"Skipping entry due to missing keys: {missing_keys}")
                continue  # Skip to the next entry

            if entry['time_insert'] > last_time_insert:
                # Print the entry to the terminal
                print("Data to be uploaded:", entry)
                logger.info(f"Data to be uploaded: {entry}")
                
                Data.kirim_data(session,
                                entry['h_value'],
                                entry['d_value'],
                                entry['t_value'],
                                entry['status'],
                                entry['code_instrument'],
                                entry['time_series'],
                                entry['time_insert'],
                                entry['created_date'])
                last_time_insert = entry['time_insert']
    except ValueError as e:
        logger.error('Data terbaru gagal: %s', e)
        Log.kirim_log(session, f"Data terbaru gagal: {e}", time.strftime("%Y-%m-%d %H:%M:%S"))
    except json.JSONDecodeError as e:
        logger.error('Data terbaru gagal: %s', e)
        Log.kirim_log(session, f"Data terbaru gagal: {e}", time.strftime("%Y-%m-%d %H:%M:%S"))
    except KeyError as e:
        logger.error('Data terbaru gagal: %s', e)
        Log.kirim_log(session, f"Data terbaru gagal: {e}", time.strftime("%Y-%m-%d %H:%M:%S"))
    except sqlalchemy.exc.SQLAlchemyError as e:
        logger.error('Upload data ke database gagal: %s', e)
        Log.kirim_log(session, f"Upload data ke database gagal: {e}", time.strftime("%Y-%m-%d %H:%M:%S"))

    return last_time_insert

class Watcher:
    def __init__(self, directory):
        self.observer = Observer()
        self.directory = directory

    def run(self):
        event_handler = Handler()
        self.observer.schedule(event_handler, self.directory, recursive=False)
        self.observer.start()
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.observer.stop()
        self.observer.join()

class Handler(FileSystemEventHandler):
    @staticmethod
    def process(event):
        global last_time_insert
        if event.is_directory:
            return None
        elif event.event_type == 'modified' and event.src_path == json_file_path:
            last_time_insert = load_and_process_data(session, json_file_path, last_time_insert)

    def on_modified(self, event):
        self.process(event)

if __name__ == '__main__':
    # Load and process data at the start
    last_time_insert = load_and_process_data(session, json_file_path, last_time_insert)
    # Start the watcher to monitor for changes
    w = Watcher(os.path.dirname(json_file_path))
    w.run()