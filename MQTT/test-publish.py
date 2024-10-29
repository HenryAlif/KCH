import paho.mqtt.client as mqtt

# Fungsi callback ketika client terhubung ke broker
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Koneksi berhasil")
    else:
        print(f"Koneksi gagal dengan kode: {rc}")

# Fungsi callback ketika message diterbitkan
def on_publish(client, userdata, mid):
    print(f"message diterbitkan dengan mid: {mid}")

# Membuat instance client MQTT versi terbaru
client = mqtt.Client()

# Menetapkan callback untuk koneksi dan publish
client.on_connect = on_connect
client.on_publish = on_publish

# Menghubungkan ke broker
broker = "10.126.15.7"
port = 1883
client.connect(broker, port)

# Mulai loop jaringan client
client.loop_start()

# Menerbitkan message ke topic
topic = "test/subscribe"
message = "test publishnya masuk ke subs gak?"
result = client.publish(topic, message)

# Tunggu hingga publish selesai
result.wait_for_publish()
print(f"message '{message}' diterbitkan ke topic '{topic}'")

# Beri waktu untuk proses sebelum menghentikan loop
import time
time.sleep(2)

# Hentikan loop dan disconnect dari broker
client.loop_stop()
client.disconnect()
