import json
import mysql.connector
from mysql.connector import Error

def insert_data_to_db(data):
    try:
        connection = mysql.connector.connect(
            host='localhost',
            database='your_database',
            user='your_username',
            password='your_password'
        )
        cursor = connection.cursor()
        query = "INSERT INTO your_table (column1, column2) VALUES (%s, %s)"
        cursor.execute(query, (data['field1'], data['field2']))
        connection.commit()
    except Error as e:
        print(f"Error: {e}")
        return False
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
    return True

def save_to_json(data):
    try:
        with open('failed_data.json', 'a') as f:
            json.dump(data, f)
            f.write("\n")
    except Exception as e:
        print(f"Failed to write to JSON file: {e}")

# Contoh data yang diterima dari sensor atau sumber lain
data = {'field1': 'value1', 'field2': 'value2'}

if not insert_data_to_db(data):
    print("Data failed to be inserted into the database, saving to JSON.")
    save_to_json(data)
else:
    print("Data inserted successfully into the database.")
