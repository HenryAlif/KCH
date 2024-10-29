import paho.mqtt.client as mqtt

# Fungsi callback ketika client terhubung ke broker
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Terhubung ke broker, berhasil subscribe ke topik")
        client.subscribe("test/publish")  # Berlangganan ke topik tertentu
    else:
        print(f"Gagal terhubung, kode: {rc}")

# Fungsi callback ketika pesan diterima dari broker
def on_message(client, userdata, message):
    print(f"Data '{message.topic}': {message.payload.decode()}")

# Membuat instance client MQTT
client = mqtt.Client()

# Menetapkan callback untuk koneksi dan penerimaan pesan
client.on_connect = on_connect
client.on_message = on_message

# Menghubungkan ke broker MQTT
broker = "10.126.15.7"  # Kamu bisa ganti dengan broker lain
port = 1883
client.connect(broker, port)

# Mulai loop jaringan client
client.loop_start()

# Tunggu hingga ada pesan diterima
import time
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("Berhenti berlangganan...")

# Stop loop dan disconnect dari broker
client.loop_stop()
client.disconnect()
