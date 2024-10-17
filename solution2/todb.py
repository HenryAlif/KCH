import json
import mysql.connector
from mysql.connector import Error

# Fungsi untuk memasukkan data ke database
def insert_data_to_db(data):
    try:
        connection = mysql.connector.connect(
            user="root",
            password="",
            host="localhost",
            port="3306",
            database="kalbe"
        )
        cursor = connection.cursor()
        query = "INSERT INTO machine_1(no, batch, speed, Tanggal, thickness, diameter, hardness) VALUES (%s, %s, %s, %s, %s, %s, %s)"
        cursor.execute(query, (data['no'], data['batch'], data['speed'], data['Tanggal'], data['thickness'], data['diameter'], data['hardness']))
        connection.commit()
    except Error as e:
        print(f"Error: {e}")
        return False
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
    return True

# Fungsi untuk mengupload data dari JSON ke database
def upload_json_to_db():
    try:
        with open('failed_data.json', 'r') as f:
            lines = f.readlines()
    except Exception as e:
        print(f"Failed to read JSON file: {e}")
        return

    new_lines = []
    for line in lines:
        data = json.loads(line)
        if insert_data_to_db(data):
            print(f"Data uploaded successfully: {data}")
        else:
            print(f"Failed to upload data: {data}")
            new_lines.append(line)

    # Overwrite file JSON dengan data yang belum berhasil di-upload
    with open('failed_data.json', 'w') as f:
        f.writelines(new_lines)

# Jalankan fungsi untuk mengupload data dari JSON ke database
upload_json_to_db()
