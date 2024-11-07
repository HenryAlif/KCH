import serial
import threading
import time
import re

# Fungsi untuk membaca dan memproses data dari port serial
def read_serial_data(serial_port, printer_name):
    ser = serial.Serial(serial_port, 9600, timeout=1)  # Ganti 9600 dengan baudrate yang sesuai
    while True:
        if ser.in_waiting > 0:
            data = ser.readline().decode('utf-8').strip()
            process_data(data, printer_name)

# Fungsi untuk memproses data yang diterima
def process_data(data, printer_name):
    # Simpan data ke file teks dengan nama printer_name.txt
    filename = f"{printer_name}.txt"
    with open(filename, 'a') as file:
        file.write(data + '\n')
    print(f"Data dari {printer_name}: {data}")
    if printer_name == "Printer 1":
        parsed_data = parse_data_printer_1(data)
        print(f"Data dari {printer_name} (parsed): {parsed_data}")
    elif printer_name == "Printer 2":
        parsed_data = parse_data_printer_2(data)
        print(f"Data dari {printer_name} (parsed): {parsed_data}")
    else:
        print(f"Data dari {printer_name} (tidak dikenal): {data}")

def parse_data_printer_1(data):
    Data_split = re.split(r'\s{2,}',data)
    Data_length = len(Data_split)

def parse_data_printer_2(data):
    Data_split = re.split(r'\s{2,}',data)
    Data_length = len(Data_split)

if __name__ == "__main__":
    # Ganti '/dev/ttyUSB0' dan '/dev/ttyUSB1' dengan port serial yang sesuai
    port1 = 'COM6'  # Contoh port untuk printer pertama
    port2 = 'COM6'  # Contoh port untuk printer kedua

    # Buat thread untuk membaca dari masing-masing port serial
    thread1 = threading.Thread(target=read_serial_data, args=(port1, "Printer 1"))
    thread2 = threading.Thread(target=read_serial_data, args=(port2, "Printer 2"))

    # Mulai kedua thread
    thread1.start()
    thread2.start()

    try:
        # Tunggu kedua thread selesai
        thread1.join()
        thread2.join()
    except KeyboardInterrupt:
        # Tangani jika user menekan Ctrl+C untuk keluar
        print("\nKeyboardInterrupt: Stopping threads...")

    print("Exiting main program")
