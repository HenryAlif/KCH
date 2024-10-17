import json
import mysql.connector
import time
from datetime import datetime

tanggal_waktu_terformat = datetime.now().strftime('%Y-%m-%d')

# Fungsi untuk menyimpan data ke file JSON
def save_to_json(data, filename="backup_data_revisi.json"):
    try:
        with open(filename, 'r+') as file:
            try:
                existing_data = json.load(file)
            except json.JSONDecodeError:
                existing_data = []
            existing_data.append(data)
            file.seek(0)
            json.dump(existing_data, file, indent=4)
    except FileNotFoundError:
        with open(filename, 'w') as file:
            json.dump([data], file, indent=4)

# Fungsi untuk mengupload data dari file JSON ke database setelah koneksi pulih
def upload_from_json():
    try:
        with open('backup_data_revisi.json', 'r+') as f:
            backup_data_revisi = json.load(f)

        con = mysql.connector.connect(
            user="root",
            password="",
            host="localhost",
            port="3306",
            database="kalbe"
        )
        
        if con.is_connected():
            cur = con.cursor()
            for item in backup_data_revisi:
                val = (item['no'], item['batch'], item['speed'], item['Tanggal'], item['thickness'], item['diameter'], item['hardness'])
                sql = "INSERT INTO machine_1(no, batch, speed, Tanggal, thickness, diameter, hardness) VALUES (%s, %s, %s, %s, %s, %s, %s)"
                cur.execute(sql, val)
                con.commit()
                print(f"Data {item['no']} successfully inserted.")

            cur.close()
            con.close()
            # Hapus semua data dari file JSON setelah berhasil diupload
            open('backup_data_revisi.json', 'w').close()
            print("All backup data successfully uploaded.")
            
    except FileNotFoundError:
        print("No backup file found.")
    except Exception as e:
        print(f"Error uploading data from JSON: {e}")

# Fungsi untuk mengupload data ke database
def upload_to_db(item):
    try:
        con = mysql.connector.connect(
            user="root",
            password="",
            host="localhost",
            port="3306",
            database="kalbe"
        )
        
        if con.is_connected():
            cur = con.cursor()
            val = (item['no'], item['batch'], item['speed'], item['Tanggal'], item['thickness'], item['diameter'], item['hardness'])
            sql = "INSERT INTO machine_1(no, batch, speed, Tanggal, thickness, diameter, hardness) VALUES (%s, %s, %s, %s, %s, %s, %s)"
            cur.execute(sql, val)
            con.commit()
            print(f"Data {item['no']} successfully inserted.")
            cur.close()
            con.close()
    except mysql.connector.Error as err:
        print(f"Database error: {err}")
        save_to_json(item)  # Simpan ke JSON jika koneksi database gagal
    except Exception as e:
        print(f"Unexpected error: {e}")
        save_to_json(item)  # Simpan ke JSON jika terjadi error lainnya

# Fungsi utama untuk memproses data dan mengupload
def main_process(new_data_list):
    # Pertama, cek jika ada data yang belum terupload dari file JSON
    upload_from_json()

    # Setelah semua data dari JSON berhasil diupload, mulai upload data baru
    for new_data in new_data_list:
        upload_to_db(new_data)
        time.sleep(1)  # Delay untuk simulasi koneksi stabil

    # Jika koneksi terputus lagi, proses upload dari file JSON akan dicoba ulang setiap 5 detik
    while True:
        try:
            upload_from_json()
            break  # Keluar dari loop jika semua data berhasil diupload
        except Exception as e:
            print("Re-upload failed. Retrying in 5 seconds...")
            time.sleep(1)  # Coba upload lagi setiap 5 detik jika gagal

# Contoh data yang akan di-upload
new_data_list = [
    {"no": str(i), "batch": f"{i:03}", "speed": str(100 + i), "Tanggal": tanggal_waktu_terformat,
     "thickness": f"{2.5 + i * 0.01:.2f}", "diameter": f"{5.6 + i * 0.02:.2f}", "hardness": str(80 + i)}
    for i in range(1, 21)
]

# Menjalankan proses
main_process(new_data_list)
