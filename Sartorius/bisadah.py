import serial
import binascii
from datetime import datetime

def read_serial_data():
    # Pastikan port serial sesuai dengan perangkat yang digunakan
    ser = serial.Serial('COM6', 9600, timeout=1)  # Sesuaikan 'COM3' dengan port yang digunakan
    print("Serial connection establi    shed. Waiting for data...")
    
    while True:
        try:
            # Baca data dari serial (jumlah byte yang sesuai dengan kebutuhan)
            raw_data = ser.read(64)  # Misalnya, baca 64 bytes dari perangkat serial
            
            if len(raw_data) > 0:
                # Konversi ke format hexadecimal untuk mempermudah parsing
                hex_data = binascii.hexlify(raw_data).decode('ascii')
                
                # Ambil timestamp dari data yang diterima, misalnya dari byte ke-0 hingga ke-7
                timestamp_data = raw_data[0:8]
                timestamp = parse_timestamp(timestamp_data)  # Parsing timestamp ke format datetime
                
                # Ambil sensor ID dari byte ke-8 hingga ke-11
                sensor_id_data = raw_data[8:12]
                sensor_id = parse_sensor_id(sensor_id_data)
                
                # Ambil measurement dari byte ke-12 dan seterusnya
                measurement_data = raw_data[12:20]
                measurement = parse_measurement(measurement_data)

                # Tampilkan data hasil parsing
                print(f"Timestamp: {timestamp}")
                print(f"Sensor ID: {sensor_id}")
                print(f"Measurement: {measurement} mg")

        except Exception as e:
            print(f"Error: {e}")
            break

def parse_timestamp(data):
    """
    Parsing timestamp dari data serial.
    """
    try:
        # Asumsikan timestamp adalah representasi hex dari datetime
        # Ubah ke format yang bisa dibaca manusia (misalnya, datetime.now() hanya untuk contoh)
        timestamp = datetime.now().strftime("%d-%b-%Y %H:%M:%S")  # Gantilah dengan decoding yang sesuai
        return timestamp
    except Exception as e:
        return f"Error parsing timestamp: {e}"

def parse_sensor_id(data):
    """
    Parsing ID sensor dari data serial.
    """
    try:
        # Ubah data binary ID ke bentuk string
        sensor_id = data.decode('ascii', errors='replace').strip()
        return sensor_id
    except Exception as e:
        return f"Error parsing sensor ID: {e}"

def parse_measurement(data):
    """
    Parsing data pengukuran dari data serial.
    """
    try:
        # Ubah data ke bentuk float atau integer sesuai data dari perangkat
        measurement = int.from_bytes(data, byteorder='big')  # Gantilah decoding ini jika format berbeda
        return measurement
    except Exception as e:
        return f"Error parsing measurement: {e}"

# Jalankan fungsi untuk membaca data serial
read_serial_data()
