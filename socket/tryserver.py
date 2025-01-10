import socket
import pickle
from sqlalchemy import create_engine, Column, Integer, Float, String, exc
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Define the SQLAlchemy base and model
Base = declarative_base()

class SakaplantProdIPCStaging(Base):
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

# Create an engine and session
engine = create_engine('postgresql://users_pims_engineer:Engineer_2023@10.106.1.40/pims_prod')
Session = sessionmaker(bind=engine)
session = Session()

def server():
    # Setup server socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('localhost', 12345))
    server_socket.listen(1)
    print("Server ready to receive data...")

    while True:
        conn, addr = server_socket.accept()
        print(f"Connected by {addr}")

        # Receive data
        data = conn.recv(4096)
        if not data:
            break
        obj = pickle.loads(data)
        print(f"Received object: {obj}")

        # Push the object to the database
        try:
            # Create an instance of the model
            record = SakaplantProdIPCStaging(
                h_value=obj['h_value'],
                d_value=obj['d_value'],
                t_value=obj['t_value'],
                status=obj['status'],
                code_instrument=obj['code_instrument'],
                time_series=int(obj['time_series']),
                time_insert=obj['time_insert'],
                created_date=obj['created_date']
            )
            # Add the record to the session and commit
            session.add(record)
            session.commit()
            print("Record inserted successfully")
        except exc.SQLAlchemyError as e:
            session.rollback()
            print(f"Error inserting record: {e}")

        conn.close()

if __name__ == "__main__":
    # Create the database and table if they don't exist
    Base.metadata.create_all(engine)
    server()