import serial

def read_from_scale():
    # Configure the serial connection (adjust the parameters as needed)
    ser = serial.Serial(
        port='COM6',      # Replace with the correct COM port for your setup
        baudrate=9600,     # Baud rate for Sartorius scale (check the scale's manual)
        timeout=1,         # Read timeout in seconds
        parity=serial.PARITY_NONE,
        stopbits=serial.STOPBITS_ONE,
        bytesize=serial.EIGHTBITS
    )

    if ser.is_open:
        print("Listening to serial port...")

    try:
        while True:
            # Read from the serial port
            data = ser.readline()  # Read until newline or timeout

            if data:
                # Decode the data (assuming it's ASCII text)
                decoded_data = data.decode('ascii', errors='replace').strip()
                print(f"Data from scale: {decoded_data}")

                # Here, you can also add logic to handle/store/process the data as needed

    except KeyboardInterrupt:
        print("Stopping serial listener.")
    finally:
        ser.close()

if __name__ == "__main__":
    read_from_scale()
