import json
import mysql.connector
import time

# Fungsi untuk koneksi ke database MySQL
def connect_to_db():
    try:
        con = mysql.connector.connect(
            user="root",
            password="",
            host="localhost",
            port="3306",
            database="kalbe"
        )
        if con.is_connected():
            print("Connected to database")
        return con
    except mysql.connector.Error as e:
        print(f"Database connection failed: {e}")
        return None

# Fungsi untuk mengupload data ke database
def upload_data(con, data):
    try:
        cur = con.cursor()
        for item in data:
            val = (
                item['no'], item['batch'], item['speed'],
                item['Tanggal'], item['thickness'],
                item['diameter'], item['hardness']
            )
            sql = """
            INSERT INTO machine_1(no, batch, speed, Tanggal, thickness, diameter, hardness)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            cur.execute(sql, val)
        con.commit()
        print(f"{cur.rowcount} rows got inserted")
        cur.close()
        return True
    except mysql.connector.Error as e:
        print(f"Error during data insertion: {e}")
        return False

# Fungsi untuk menyimpan data sementara ke JSON jika koneksi terputus
def save_data_to_json(data, file_name='testobat.json'):
    with open(file_name, 'w') as f:
        json.dump(data, f, indent=4)
    print("Data saved to JSON for later upload.")

# Fungsi untuk memuat data dari JSON
def load_data_from_json(file_name='testobat.json'):
    try:
        with open(file_name, 'r') as f:
            data = json.load(f)
        print("Data loaded from JSON.")
        return data
    except FileNotFoundError:
        print("No data file found, starting fresh.")
        return []

# Main logic for data handling
def handle_data_upload():
    data_queue = load_data_from_json()  # Load any data already in JSON
    index = 0  # Index for tracking which data is being processed

    while index < len(data_queue):
        con = connect_to_db()

        if con:
            # Attempt to upload the remaining data in queue
            while index < len(data_queue):
                success = upload_data(con, [data_queue[index]])
                if success:
                    print(f"Data {index + 1} successfully uploaded.")
                    index += 1  # Move to the next data item
                else:
                    print(f"Failed to upload data {index + 1}. Pausing upload.")
                    break  # Stop if there's a failure during insertion

            con.close()
        else:
            print("Waiting for database connection to be restored...")
            time.sleep(5)  # Wait 5 seconds before trying to reconnect

    # Once all data is uploaded, clear the JSON file
    save_data_to_json([])

# Fungsi untuk memasukkan data baru ke queue dan mengupload
def new_data_entry(new_data):
    data_queue = load_data_from_json()  # Load current queue
    data_queue.append(new_data)  # Add new data to queue
    save_data_to_json(data_queue)  # Save updated queue to JSON

    handle_data_upload()  # Try to upload new data to database
    time.sleep(1)

# Contoh penggunaan
if __name__ == "__main__":
    # Simulate new data entry
    new_data = {
        "no": "6",
        "batch": "Batch_001",
        "speed": "100",
        "Tanggal": "2024-09-18",
        "thickness": "2.5",
        "diameter": "5.6",
        "hardness": "80"
    }
    
    new_data_list = [
    {"no": str(i), "batch": f"Batch_{i:03}", "speed": str(100 + i), "Tanggal": "2024-09-18",
     "thickness": f"{2.5 + i * 0.01:.2f}", "diameter": f"{5.6 + i * 0.02:.2f}", "hardness": str(80 + i)}
    for i in range(1, 101)
]

# Contoh penggunaan untuk mengupload semua data
for new_data in new_data_list:
    new_data_entry(new_data)  # Fungsi new_data_entry dari kode sebelumnya
