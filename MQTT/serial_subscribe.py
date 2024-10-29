import paho.mqtt.client as mqtt
import json
from sqlalchemy import create_engine, Column, Float, String, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import ast

# SQLAlchemy setup
Base = declarative_base()

class MeasurementData(Base):
    __tablename__ = 'hardness'
    id = Column(Integer, primary_key=True, autoincrement=True)
    h_value = Column(Float)
    d_value = Column(Float)
    t_value = Column(Float)
    status = Column(String)
    code_instrument = Column(String)
    time_series = Column(String)

# Replace with your actual database URL
DATABASE_URL = "mysql+mysqlconnector://root@localhost:3306/kalbe"  # You can switch this to any other database like PostgreSQL, MySQL, etc.
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()

# Create the table if it doesn't exist
Base.metadata.create_all(engine)

# MQTT configurations
MQTT_BROKER = '10.126.15.7'  # Replace with your MQTT broker address
MQTT_PORT = 1883  # Default port
MQTT_TOPIC = 'test/publish'  # Replace with your actual topic

# Define the on_message callback for MQTT
def on_message(client, userdata, msg):
    try:
        # Decode the incoming MQTT message
        message = msg.payload.decode()

        # Use ast.literal_eval to convert the string with single quotes to a Python dictionary
        # If the message is in a proper JSON format, this will handle it correctly
        data = ast.literal_eval(message)  # Handle single quotes to dict conversion

        print(f"Received data: {data}")

        # Use slice to get the last element of the array
        if isinstance(data, list):  # Check if data is a list (array)
            last_data = data[-1:]  # Slice to get only the last element
            print(f"Last data slice: {last_data}")
        else:
            last_data = [data]  # If it's a single dictionary, wrap it in a list

        # Insert the sliced data into the database
        insert_data_into_db(last_data)

    except (ValueError, SyntaxError) as e:
        print(f"Error processing message: {e}")

# Insert data into the database using SQLAlchemy
def insert_data_into_db(data):
    try:
        for record in data:
            new_record = MeasurementData(
                h_value=record['h_value'],
                d_value=record['d_value'],
                t_value=record['t_value'],
                status=record['status'],
                code_instrument=record['code_instrument'],
                time_series=record['time_series']
            )
            session.add(new_record)
        
        # Commit all records
        session.commit()
        print("Data inserted into the database.")
    except Exception as e:
        session.rollback()  # Rollback in case of an error
        print(f"Error inserting data into the database: {e}")

# MQTT Client setup
client = mqtt.Client()
client.on_message = on_message  # Assign the on_message function

# Connect to the MQTT broker
client.connect(MQTT_BROKER, MQTT_PORT, 60)

# Subscribe to the topic
client.subscribe(MQTT_TOPIC)

# Start the MQTT loop
client.loop_forever()
