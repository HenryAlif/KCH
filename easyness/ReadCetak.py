import serial
import threading
import re
import time
import logging
import json
from datetime import datetime

logging.basicConfig(filename='info_log.txt', level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

# Initialize global variables
bef = 0
count = 1
prevCount = 0
buffer = ""
Arbffr = []
thickness = ""
diameter = ""
hardness = ""
time_series = ""

# Variabel untuk menyimpan error terakhir
last_error_message = None

# Get the current date in the desired format
tanggal_waktu_terformat = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

def initialize_serial():
    global serial_port, tanggal_waktu_terformat, last_error_message
    while True:
        try:
            serial_port = serial.Serial(port="COM3", baudrate=9600, timeout=1)
            serial_port.reset_input_buffer()
            print(f"Serial connection established. {tanggal_waktu_terformat}")
            logging.info(f"Serial connection established on {serial_port.port} with baudrate {serial_port.baudrate} at {tanggal_waktu_terformat}")
            time.sleep(2)
            break
        except serial.SerialException as e:
            error_message = f"Serial FAILED: {e}"
            print(error_message)
            logging.error(error_message)
            
            # Cek apakah error sama sudah dikirim sebelumnya
            if last_error_message != error_message:
                last_error_message = error_message  # Simpan pesan error terakhir yang dikirim
            time.sleep(5)
            print(tanggal_waktu_terformat)

initialize_serial()  # Initialize the serial connection
logging.info(f"Serial connection established on {serial_port.port} with baudrate {serial_port.baudrate} at {tanggal_waktu_terformat}")

class SerialReader:

    def __init__(self):
        self.thread = threading.Thread(target=self._read_thread)
        self.thread.daemon = True

    def start(self):
        self.thread.start()

    def _read_thread(self):
        global serial_port, bef, buffer, Arbffr, prevCount, tanggal_waktu_terformat, last_error_message
        while True:
            try:
                if serial_port is None:
                    initialize_serial()
                    continue
                line = serial_port.readline().decode(encoding='UTF-8', errors='replace')
                if line:
                    buffer += line
                    if bef == 0:
                        bef = 1
                        buffer = ""
                    else:
                        bef = 1
                else:
                    if bef == 1:
                        data = re.split(r"\s+|\n", buffer)
                        if "Testing" in data:  
                            try:
                                dataindex = data.index("Results")
                                batch = data[22]
                                speed = data[24]
                                Tanggal = data[28]
                                Time = data[30]
                                no = data[48]
                                thickness = float(data[dataindex+4])
                                diameter = float(data[dataindex+7])
                                hardness = float(data[dataindex+10])
                                count = int(no)
                                
                                # Append the new entry to Arbffr
                                Arbffr.append({
                                    "no": no,
                                    "batch": batch,
                                    "speed": speed,
                                    "tanggal": Tanggal,
                                    "time": Time,
                                    "thickness": thickness,
                                    "diameter": diameter,
                                    "hardness": hardness,
                                    "created_date": tanggal_waktu_terformat
                                })
                                prevCount = count
                                buffer = ""
                                
                            except (ValueError, IndexError) as conversion_error:
                                error_message = f"Data CONVERSION: {conversion_error}"
                                logging.error(error_message)
                                # print(error_message)
                                
                                # Cek apakah error sama sudah dikirim sebelumnya
                                if last_error_message != error_message:
                                    last_error_message = error_message 
                                
                                bef = 0
                                buffer = ""
                                prevCount = 0
                                count = 1
                                data = ""
                                Arbffr = []
                                continue 

                        elif "No." in data and len(data) < 20:
                            try:
                                dataindex = data.index("mm")
                                no = data[1]
                                thickness = float(data[dataindex-1])
                                diameter = float(data[dataindex+2])
                                hardness = float(data[dataindex+5])
                                count = int(no)
                                
                                # Append the new entry to Arbffr
                                Arbffr.append({
                                    "no": no,
                                    "batch": batch,
                                    "speed": speed,
                                    "tanggal": Tanggal,
                                    "time": Time,
                                    "thickness": thickness,
                                    "diameter": diameter,
                                    "hardness": hardness,
                                    "created_date": tanggal_waktu_terformat
                                })
                                prevCount = count
                                buffer = ""
                                
                            except (ValueError, IndexError) as conversion_error:
                                bef = 0
                                buffer = ""
                                prevCount = 0
                                count = 1
                                data = ""
                                Arbffr = []
                                continue
                        
                        elif "Xm" in data or "Xmean" in data or "Released:" in data:
                            bef = 0
                            buffer = ""
                            prevCount = 0
                            count = 1
                            data = ""
                            time.sleep(5)
                            Arbffr = []
                            
                # Write the data to JSON file after each new entry
                self.write_to_json()
            except serial.SerialException as e:
                error_message = f"Serial exception: {e}"
                print(f"Serial exception: {e}")
                print(error_message)
                logging.error(error_message)
                
                # Cek apakah error sama sudah dikirim sebelumnya
                if last_error_message != error_message:
                    last_error_message = error_message  # Simpan pesan error terakhir yang dikirim
                serial_port = None
                time.sleep(5)

    def write_to_json(self):
        # Write the collected data to JSON file
        with open('data_cetak.json', 'w') as json_file:
            json.dump(Arbffr, json_file, indent=4)
            

if __name__ == "__main__":
    Reading = SerialReader()
    Reading.start()
    while True:
        h_value = hardness
        d_value = diameter
        t_value = thickness
        status = ""
        code_instrument = "A20230626002"
        created_date = tanggal_waktu_terformat
        time_series = time_series
