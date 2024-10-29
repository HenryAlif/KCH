import serial
import threading
import re
import time
import logging
import paho.mqtt.client as mqtt
from datetime import datetime

logging.basicConfig(filename='serial_log.txt', level=logging.ERROR, format='%(asctime)s [%(levelname)s] %(message)s')
logging.basicConfig(filename='info_log.txt', level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

# Initialize global variables
all_data = []
bef = 0
count = 1
prevCount = 0
buffer = ""
Arbffr = [[]]
thickness = ""
diameter = ""
hardness = ""
time_series = ""

# Variabel untuk menyimpan error terakhir
last_error_message = None

# Get the current date in the desired format
tanggal_waktu_terformat = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

# Konfigurasi koneksi ke database PostgreSQL
broker_address = "10.126.15.7"  # Pastikan alamat ini valid dan dapat dijangkau
mqtt_topic = "test/publish"

# Buat client MQTT dan tambahkan callback
client = mqtt.Client(protocol=mqtt.MQTTv311)

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected successfully to MQTT broker.")
        client.subscribe("topic/test")
    else:
        print(f"Failed to connect with result code {rc}")

def on_message(client, userdata, msg):
    print(f"{msg.topic}")

client.on_connect = on_connect
client.on_message = on_message
# Fungsi mqtt_send_data yang sudah dimodifikasi untuk menggunakan slice()
def mqtt_send_data(h_value, d_value, t_value, status, code_instrument, time_series):
    try:
        # Create the payload
        payload = {
            "h_value": h_value,
            "d_value": d_value,
            "t_value": t_value,
            "status": status,
            "code_instrument": code_instrument,
            "time_series": time_series
        }

        # Append the payload to all_data array
        all_data.append(payload)

        # Ambil elemen terakhir dari all_data menggunakan slice()
        # last_data = all_data[-1:]  # Mengambil data terakhir

        # Jika perlu, kirim atau proses hanya data terbaru
        client.publish(mqtt_topic, str(all_data))  # Hanya kirim data terbaru
        logging.info(f"Data terbaru dikirim ke MQTT broker: {all_data}")
        print(f"Data terbaru diproses dan dikirim: {all_data}")

    except Exception as e:
        logging.error(f"Gagal mengirim data ke MQTT broker: {e}")
        print(f"Error: {e}")

serial_port = None

def close_serial():
    global serial_port
    if serial_port and serial_port.is_open:
        serial_port.close()
        print("Serial port closed.")

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

            if last_error_message != error_message:
                last_error_message = error_message
            time.sleep(5)

initialize_serial()  # Initialize the serial connection

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
                                batch = data[22]
                                speed = data[24]
                                Tanggal = data[28]
                                Time = data[30]
                                no = data[48]
                                thickness = float(data[50])
                                diameter = float(data[53])
                                hardness = float(data[56])
                                Rev_thickness = data[38]
                                Rev_diameter = data[41]
                                Rev_hardness = data[44]
                                count = int(no)

                                # new_data= {
                                #     "no" : no,
                                #     "hardness": hardness,
                                #     "thickness": thickness,
                                #     "diameter": diameter,
                                # }
                                # all_data.append(new_data)
                                # print(f"Data appended: {new_data}")  # Debugging output

                                Arbffr[prevCount].append(no)
                                Arbffr[prevCount].append(batch)
                                Arbffr[prevCount].append(speed)
                                Arbffr[prevCount].append(Tanggal)
                                Arbffr[prevCount].append(Time)
                                Arbffr[prevCount].append(thickness)
                                Arbffr[prevCount].append(diameter)
                                Arbffr[prevCount].append(hardness)
                                prevCount = count
                                buffer = ""
                                mqtt_send_data(hardness, diameter, thickness, "N", "A20230626002", time_series=no)
                            except (ValueError, IndexError) as conversion_error:
                                bef = 0
                                buffer = ""
                                prevCount = 0
                                count = 1
                                data = ""
                                Arbffr = [[]]
                                continue

                        elif "No." in data and len(data) < 20:
                            data = re.split(r"\s+|\n", buffer)
                            try:
                                no = data[1]
                                thickness = float(data[3])
                                diameter = float(data[6])
                                hardness = float(data[9])
                                count = int(no)

                                # new_data= {
                                #     "no" : no,
                                #     "hardness": hardness,
                                #     "thickness": thickness,
                                #     "diameter": diameter,
                                # }
                                # all_data.append(new_data)
                                # print(f"Data appended: {new_data}") 

                                Arbffr.append([])
                                Arbffr[prevCount].append(no)
                                Arbffr[prevCount].append(batch)
                                Arbffr[prevCount].append(speed)
                                Arbffr[prevCount].append(Tanggal)
                                Arbffr[prevCount].append(Time)
                                Arbffr[prevCount].append(thickness)
                                Arbffr[prevCount].append(diameter)
                                Arbffr[prevCount].append(hardness)
                                prevCount = count
                                buffer = ""
                                #print(no, thickness, diameter, hardness, Tanggal, tanggal_waktu_terformat)
                                with open("data_log.txt", "a") as file:
                                    file.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')}: {no, thickness, diameter, hardness, Tanggal, tanggal_waktu_terformat}\n")
                                mqtt_send_data(hardness, diameter, thickness, "N", "A20230626002", time_series=no)
                            
                            except (ValueError, IndexError) as conversion_error:
                                bef = 0
                                buffer = ""
                                prevCount = 0
                                count = 1
                                data = ""
                                Arbffr = [[]]
                                continue
                            
                        elif "Xm" in data or "Xmean" in data or "Released:" in data:
                            bef = 0
                            buffer = ""
                            prevCount = 0
                            count = 1
                            data = ""
                            Arbffr = [[]]
            except serial.SerialException as e:
                serial_port = None
                time.sleep(5)

# print(Arbffr.append)
# print(all_data.append)


if __name__ == "__main__":
    Reading = SerialReader()
    Reading.start()
    if str(time_series) == 10:
            all_data.clear()  # Clear the array when time_series reaches 10
            print("Resetting array as time_series reached 10.")
    try:
        client.connect(broker_address, 1883, 60)  # Koneksi ke broker MQTT
        client.loop_forever()
    except Exception as e:
        logging.error(f"MQTT connection error: {e}")
