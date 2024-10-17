import json
import mysql.connector

# Buka file JSON
with open('testobat.json', 'r') as f:
    data = json.load(f)

print(data)

try:
    # Hubungkan ke database MySQL
    con = mysql.connector.connect(
        user="root",
        password="",
        host="localhost",
        port="3306",
        database="kalbe"
    )

    if con.is_connected():
        print("Connected to database")

    # Buat cursor di luar loop agar hanya dibuat sekali
    cur = con.cursor()

    # Loop untuk memasukkan setiap item di file JSON
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

    # Commit semua perubahan setelah loop selesai
    con.commit()
    print(cur.rowcount, "rows got inserted")

except mysql.connector.Error as e:
    print(f"Database error: {e}")

finally:
    # Tutup cursor dan koneksi setelah semua operasi selesai
    if cur:
        cur.close()
    if con.is_connected():
        con.close()
        print("Database connection closed")
