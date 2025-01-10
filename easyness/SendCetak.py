import json
import os
import time
import logging
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from sqlalchemy import create_engine, Column, Integer, Float, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

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
DATABASE_URL = "postgresql://users_pims_engineer:Engineer_2023@10.106.1.40/pims_prod" # Change to your database URL
engine = create_engine(DATABASE_URL)
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()

# Path to the JSON file
json_file_path = r'D:\Source Code\Magang Kalbe\Raspberry Pi\data_cetak.json'
# Keep track of the last processed time_series
last_time_insert = 0

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
        global last_time_series
        if event.is_directory:
            return None
        elif event.event_type == 'modified' and event.src_path == json_file_path:
            try:
                with open(json_file_path, 'r') as file:
                    data = json.load(file)
                
                for entry in data:
                    # Validate that all required keys are present
                    required_keys = ['h_value', 'd_value', 't_value', 'status', 'code_instrument', 'time_series', 'time_insert', 'created_date']
                    if not all(key in entry for key in required_keys):
                        missing_keys = [key for key in required_keys if key not in entry]
                        raise KeyError(f"Missing keys in JSON data: {missing_keys}")

                    if entry['time_series'] > last_time_series:
                        Data.kirim_data(session,
                                        entry['h_value'],
                                        entry['d_value'],
                                        entry['t_value'],
                                        entry['status'],
                                        entry['code_instrument'],
                                        entry['time_series'],
                                        entry['time_insert'],
                                        entry['created_date'])
                        last_time_series = entry['time_series']

            except KeyError as e:
                logger.error('Data terbaru gagal: %s', e)
                Log.kirim_log(session, f"Data terbaru gagal: {e}", time.strftime("%Y-%m-%d %H:%M:%S"))
            except sqlalchemy.exc.SQLAlchemyError as e:
                logger.error('Upload data ke database gagal: %s', e)
                Log.kirim_log(session, f"Upload data ke database gagal: {e}", time.strftime("%Y-%m-%d %H:%M:%S"))

    def on_modified(self, event):
        self.process(event)

if __name__ == '__main__':
    w = Watcher(os.path.dirname(json_file_path))
    w.run()