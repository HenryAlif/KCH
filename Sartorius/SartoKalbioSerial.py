import serial

def init_serial_connection():
    try:
        ser = serial.Serial(
            port='COM7',  # Sesuaikan dengan port serial yang sesuai
            baudrate=9600,
            bytesize=serial.SEVENBITS,
            parity=serial.PARITY_ODD,
            stopbits=serial.STOPBITS_ONE,
            xonxoff=True,
            rtscts=True,
            dsrdtr=True,
            timeout=1
        )
        print("Serial connection initialized for Sartorius.")
        return ser
    except Exception as e:
        print(f"Error initializing serial connection: {e}")
        return None

def receive_sartorius_data(serial_connection):
    if serial_connection and serial_connection.is_open:
        print("Receiving data from Sartorius...")
        data = ""
        try:
            while True:
                line = serial_connection.readline().decode('utf-8').strip()
                if line:
                    data += line + "\n"
                    print(line)  # Debug: Print each received line
                if line == "END":  # Kondisi untuk berhenti membaca, sesuaikan dengan kondisi END yang sesuai
                    break
            return data
        except Exception as e:
            print(f"Error reading from Sartorius: {e}")
            return ""
    else:
        print("Serial connection is not open.")
        return ""

# Fungsi ParseSPBHeader dan ParseSPBProcess yang diberikan
def ParseSPBHeader(serial, deviceid):
    # Parsing data header dari timbangan Sartorius
    serial = serial.split("\n")[1:-1]

    date = serial[0][:11]
    time = serial[0][-5:]
    srn = serial[3].replace("SerNo.    ", "")
    bac = serial[4][-8:]
    apc = serial[5][-8:]
    equipid = GetEquipID(srn)
    
    cols = """("equipid", "date", "time", "bac", "apc") VALUES (%s, %s, %s, %s, %s)"""
    val = (equipid, date, time, bac, apc)
    tabledest = "spb_cycles"
    send = SendData(cols, val, tabledest)
    
    # Mengirim data ke tabel staging
    stgcols = """(datatable, "key", "date", "time", equipid, data, deviceid) VALUES (%s, %s, %s, %s, %s, %s, %s)"""
    staging = (tabledest, send, val[1], val[2], val[0], "Sartorius PBE Weighing", deviceid)
    SendData(stgcols, staging, "staginginfo")
    print(send)
    
    return send

def ParseSPBProcess(serial, weighingid, deviceid):
    # Parsing data proses dari timbangan Sartorius
    serial = serial.split("\n")[:-1]
    count = int(len(serial) / 3)

    for x in range(0, count):
        date = serial[x * 3][:11]
        time = serial[x * 3][-9:]
        weight = float(serial[(x * 3) + 1].replace("G", "").replace("+", "").replace("g", "").strip())
        val = (weighingid, date, time, weight)
        print(val)
        
        cols = """("weighing_id", "date", "time", "weight") VALUES (%s, %s, %s, %s)"""
        tabledest = "spb_process"
        SendData(cols, val, tabledest)
    
    return val

# Fungsi untuk mendapatkan equipid dari srn
def GetEquipID(srn):
    # Implementasi logika untuk mendapatkan EquipID berdasarkan Serial Number (srn)
    equipid = "equip_id_placeholder"  # Sesuaikan dengan implementasi yang diinginkan
    return equipid

# Fungsi untuk mengirim data ke database
def SendData(columns, values, table):
    # Implementasi logika pengiriman data ke database atau penyimpanan data
    print(f"Data sent to {table}: {values}")
    return "send_result_placeholder"  # Placeholder untuk ID data yang dikirim

# Penggunaan program di bawah ini
serial_connection = init_serial_connection()
if serial_connection:
    serial_data = receive_sartorius_data(serial_connection)
    
    # Memproses data jika diterima
    if serial_data:
        device_id = "Device_ID"  # Sesuaikan dengan ID perangkat Anda

        # Proses Header untuk mendapatkan WeighingID
        weighing_id = ParseSPBHeader(serial_data, device_id)
        
        # Proses Data jika WeighingID berhasil didapatkan
        if weighing_id:
            ParseSPBProcess(serial_data, weighing_id, device_id)

    # Menutup koneksi serial setelah selesai
    serial_connection.close()
else:
    print("Failed to initialize serial connection for Sartorius.")
