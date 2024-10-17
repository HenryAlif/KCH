import json
import mysql.connector
import time

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
        # Buka file JSON dan cek apakah kosong
        with open('backup_data_revisi.json', 'r') as f:
            file_content = f.read().strip()  # Baca isi file dan hilangkan spasi kosong
            if not file_content:
                print("Backup file is empty. No data to upload.")
                return

            backup_data_revisi = json.loads(file_content)  # Memuat data JSON dari file

        # Untuk setiap item di backup_data_revisi, upload ke database
        for item in backup_data_revisi[:]:
            if upload_to_db(item):  # Hanya hapus jika berhasil diupload ke database
                backup_data_revisi.remove(item)

        # Simpan ulang data yang belum terupload (jika ada) ke file JSON
        with open('backup_data_revisi.json', 'w') as f:
            json.dump(backup_data_revisi, f, indent=4)

    except FileNotFoundError:
        print("No backup file found.")
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
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
            print("Connected to database.")
            cur = con.cursor()
            val = (item['no'], item['batch'], item['speed'], item['Tanggal'], item['thickness'], item['diameter'], item['hardness'])
            sql = "INSERT INTO machine_1(no, batch, speed, Tanggal, thickness, diameter, hardness) VALUES (%s, %s, %s, %s, %s, %s, %s)"
            cur.execute(sql, val)
            con.commit()
            print(cur.rowcount, "rows inserted.")
            cur.close()
            con.close()
            return True  # Return True jika berhasil diupload
    except mysql.connector.Error as err:
        print(f"Database error: {err}")
        return False  # Return False jika ada error
    except Exception as e:
        print(f"Unexpected error: {e}")
        return False  # Return False jika ada error lainnya

# Fungsi utama untuk memproses data dan mengupload
def main_process(new_data_list):
    for new_data in new_data_list:
        if not upload_to_db(new_data):  # Simpan ke JSON jika gagal upload
            save_to_json(new_data)
        time.sleep(1)  # Delay untuk simulasi koneksi stabil

    # Jika data disimpan ke file JSON saat koneksi terputus, coba upload lagi setelah koneksi stabil
    while True:
        try:
            upload_from_json()  # Coba upload data yang tersimpan di JSON
            break  # Keluar dari loop jika semua data berhasil diupload
        except Exception as e:
            print("Re-upload failed. Retrying in 5 seconds...")
            time.sleep(5)  # Coba upload lagi setiap 5 detik jika gagal

# Contoh data yang akan di-upload
new_data_list = [
    {"no": str(i), "batch": f"{i:03}", "speed": str(100 + i), "Tanggal": "2024-09-18",
     "thickness": f"{2.5 + i * 0.01:.2f}", "diameter": f"{5.6 + i * 0.02:.2f}", "hardness": str(80 + i)}
    for i in range(1, 20)
]

# Menjalankan proses
main_process(new_data_list)
