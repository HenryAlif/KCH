from sqlalchemy import Column, Integer, Float, Date, Time, String, func
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class MoistureData(Base):
    __tablename__ = "sakaplant_prod_ipc_ma_staging"
    id_setup = Column(Integer, primary_key=True)
    start_weight = Column(Float)
    end_weight = Column(Float)
    created_date = Column(Date, default=func.current_date())
    created_time = Column(Time, default=func.current_time())
    instrument_code = Column(String, default='MA2025001')

# Contoh penggunaan:
# Buat engine dan session untuk menghubungkan ke database Anda
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

engine = create_engine('sqlite:///example.db')
Session = sessionmaker(bind=engine)
session = Session()

# Buat tabel jika belum ada
Base.metadata.create_all(engine)

# Buat instance dari MoistureData
new_data = MoistureData(start_weight=100.0, end_weight=80.0)

# Tambahkan dan commit ke database
session.add(new_data)
session.commit()

# Tampilkan hasil
for instance in session.query(MoistureData).all():
    print(instance.id_setup, instance.created_date, instance.created_time, instance.instrument_code)