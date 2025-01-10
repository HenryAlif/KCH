import time
import requests
from sqlalchemy import create_engine, Column, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Konfigurasi database
DATABASE_URL = 'mysql+mysqlconnector://root:s4k4f4rmA@10.126.15.138:3306/ems_saka' # Ganti dengan database pilihan Anda
engine = create_engine(DATABASE_URL)
Base = declarative_base()

# Definisi tabel menggunakan SQLAlchemy dengan semua kolom bertipe String
class DataAPI(Base):
    __tablename__ = "data_api"
    
    id = Column(String, primary_key=True)
    recipe_name = Column(String)
    recipe_description = Column(String)
    created_by = Column(String)
    created_date = Column(String)
    modified_by = Column(String)
    modified_date = Column(String)
    description = Column(String)
    loading_control = Column(String)
    loading_operation = Column(String)
    exhaust_fan_motor_speed = Column(String)
    endpoint_control = Column(String)
    operator_trip = Column(String)
    fbd_dishcharge_complete_trip = Column(String)
    process_time_trip = Column(String)
    process_time_trip_min = Column(String)
    process_time_trip_sec = Column(String)
    operation_alarmtime = Column(String)
    end_of_operation_prompt_control = Column(String)
    hold_at_end_of_operation = Column(String)

# Membuat tabel di database
Base.metadata.create_all(engine)

# Membuat sesi untuk operasi database
Session = sessionmaker(bind=engine)
session = Session()

# URL API
API_URL = "http://10.126.15.25:3000/recipe-eph"  # Ganti dengan URL API Anda

def fetch_and_store_data():
    try:
        response = requests.get(API_URL)
        response.raise_for_status()  # Memastikan request berhasil
        data = response.json()

        # Memasukkan data ke database
        new_record = DataAPI(
            id=str(time.time()),  # Menggunakan timestamp sebagai ID unik
            recipe_name=str(data["EPH-RecipeName"][0]),
            recipe_description=str(data["EPH-RecipeDescription"][0]),
            created_by=str(data["EPH-CreatedBy"][0]),
            created_date=str(data["EPH-CreatedDate"][0]),
            modified_by=str(data["EPH-ModifiedBy"][0]),
            modified_date=str(data["EPH-ModifiedDate"][0]),
            description=str(data["EPH-Description"][0]),
            loading_control=str(data["EPH-LoadingControl"][0]),
            loading_operation=str(data["EPH-LoadingOperation"][0]),
            exhaust_fan_motor_speed=str(data["EPH-ExhaustFanMotorSpeed"][0]),
            endpoint_control=str(data["EPH-EndpointControl"][0]),
            operator_trip=str(data["EPH-OpratorTrip"][0]),
            fbd_dishcharge_complete_trip=str(data["EPH-FbdDishchargeCompleteTrip"][0]),
            process_time_trip=str(data["EPH-ProcessTimeTrip"][0]),
            process_time_trip_min=str(data["EPH-ProcessTimeTripMin"][0]),
            process_time_trip_sec=str(data["EPH-ProcessTimeTripSec"][0]),
            operation_alarmtime=str(data["EPH-OperationAlarmtime"][0]),
            end_of_operation_prompt_control=str(data["EPH-EndOfOprationPromptControl"][0]),
            hold_at_end_of_operation=str(data["EPH-HoldAtEndOfOpration"][0]),
        )

        session.add(new_record)
        session.commit()
        print("Data berhasil disimpan!")
    except Exception as e:
        print(f"Terjadi kesalahan: {e}")

if __name__ == "__main__":
    while True:
        fetch_and_store_data()
        time.sleep(60)  # Tunggu 1 menit sebelum request berikutnya
