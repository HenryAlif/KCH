import serial
# import threading
# import re
# import time
# import json
from datetime import datetime

tanggal_waktu_terformat = datetime.now().strftime('%Y-%m-%d')

bef = 0
count = 1
prevCount = 0
buffer = ""
Arbffr = [[]]
thickness = ""
diameter = ""
hardness = ""

def initialize_serial():
        global serial_port
        while True:
            try:
                serial_port = serial.Serial(port="/dev/ttyUSB0", baudrate=9600, timeout=1)
                serial_port.reset_input_buffer()
                print("Serial connection established.")
                break
            except serial.SerialException as e:
                print(f"Serial connection failed: {e}")
                time.sleep(5)  # Wait for 5 seconds before attempting to reconnect

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

finally:
    # Tutup cursor dan koneksi setelah semua operasi selesai
    if cur:
        cur.close()
    if con.is_connected():
        con.close()
        print("Database connection closed")