import re
import logging
from sqlalchemy import create_engine, Column, Float, Integer, String
from sqlalchemy.orm import sessionmaker, declarative_base
from datetime import datetime

# Setup logging for errors
logging.basicConfig(level=logging.INFO)

# Base class for SQLAlchemy using declarative_base from sqlalchemy.orm
Base = declarative_base()

# Define the ScalesData class for the Mettler_Scales table
class ScalesData(Base):
    __tablename__ = "Mettler_Scales"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    operator = Column(String)
    x = Column(Float)
    s_dev = Column(String)
    s_rel = Column(String)
    min_value = Column(Float)
    max_value = Column(Float)
    diff = Column(Float)
    sum_value = Column(Float)
    date = Column(String)

# Function to clean and convert numeric values, removing units and unwanted characters
def clean_numeric_value(value):
    # Remove units like "g" and unwanted text, and convert to float if possible
    cleaned_value = re.sub(r'[^\d.-]', '', value)
    try:
        return float(cleaned_value)
    except ValueError:
        return None

# Sample input data
data = """
------ Statistics ------
n                 1
x           0.65420 g
s dev           --------
s rel           --------
Min.         0.6542 g
Max.         0.6542 g
Diff.        0.0000 g
Sum          0.6542 g
------------------------
08.10.2024 11:26
User name            MAY
------------------------
Signature
========================
"""

# Function to process the input data and add to the database
def process_and_store_data(data):
    # Splitting the data based on newline
    Data_split = data.strip().split('\n')
    
    # Debugging: Print the result of Data_split to understand its structure
    print(f"Data split result (length {len(Data_split)}): {Data_split}")
    
    # Ensure Data_split has enough elements
    if len(Data_split) < 10:
        logging.error(f"Data split is too short: {Data_split}")
        return
    
    try:
        # Extract the relevant values
        operator = Data_split[-3].split('User name')[-1].strip()  # Extracting operator (MAY)
        x = clean_numeric_value(Data_split[2].split('x')[1].strip())    # Extract value of "x"
        s_dev = Data_split[3].split('s dev')[1].strip()                 # Extract s_dev (string)
        s_rel = Data_split[4].split('s rel')[1].strip()                 # Extract s_rel (string)
        min_value = clean_numeric_value(Data_split[5].split('Min.')[1].strip())  # Min value
        max_value = clean_numeric_value(Data_split[6].split('Max.')[1].strip())  # Max value
        diff = clean_numeric_value(Data_split[7].split('Diff.')[1].strip())      # Diff value
        sum_value = clean_numeric_value(Data_split[8].split('Sum')[1].strip())   # Sum value
        date = Data_split[-4].strip()  # Extracting date
        
        # Create a new ScalesData object
        Datab = ScalesData(
            operator=operator,
            x=x,
            s_dev=s_dev,
            s_rel=s_rel,
            min_value=min_value,
            max_value=max_value,
            diff=diff,
            sum_value=sum_value,
            date=date
        )
        
        # Add the new instance to the session and commit to the database
        session.add(Datab)
        session.commit()
        logging.info("Data successfully added to the database.")
    except (IndexError, ValueError) as e:
        logging.error(f"Error processing data: {e}")

# Setup the database connection
def setup_database():
    # Create an SQLite database (or connect to one)
    engine = create_engine('mysql+mysqlconnector://ems_saka:s4k4f4rmA@10.126.15.138:3306/ems_saka', echo=False)
    
    # Create all tables in the database (if not exist)
    Base.metadata.create_all(engine)
    
    # Create a session to interact with the database
    Session = sessionmaker(bind=engine)
    return Session()

# Main function
if __name__ == "__main__":
    # Setup database session
    session = setup_database()

    # Process the input data and store it in the database
    process_and_store_data(data)
