import serial

def process_scale_data(raw_data):
    """Process the raw data received from the scale"""
    try:
        # Decode the raw data to ASCII format
        data = raw_data.decode('ascii').strip()

        # Perform any data validation or extraction (e.g., extract the weight)
        if data:
            print(f"Received Data: {data}")
            # Example: If the data starts with "S" (Stable weight indicator), extract weight
            if data.startswith("S"):
                weight = data.split()[1]  # Assuming weight is the second value
                print(f"Stable Weight: {weight}")
            else:
                print("Unstable or other data received")
        else:
            print("Empty data received")
    
    except UnicodeDecodeError:
        print(f"Received invalid data: {raw_data}")

def read_scale_data():
    """Read data from the Sartorius scale"""
    try:
        # Configure the serial connection
        ser = serial.Serial(
            port='COM6',         # Replace with your actual COM port
            baudrate=1200,       # Sartorius standard baud rate
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_ODD,   # Change if your model uses different parity
            stopbits=serial.STOPBITS_ONE,
            timeout=1            # Timeout to ensure we don't block indefinitely
        )

        # Ensure the serial port is open
        if not ser.is_open:
            ser.open()

        # Flush the input buffer to avoid reading stale data
        ser.flushInput()

        # Continuously read data from the scale
        while True:
            if ser.in_waiting > 0:  # Check if data is available
                raw_data = ser.readline()  # Read data until newline character
                process_scale_data(raw_data)  # Process the received data
            else:
                print("No data available, waiting...")
        
    except serial.SerialException as e:
        print(f"Error: {e}")
    
    finally:
        # Close the connection when done
        if ser.is_open:
            ser.close()

if __name__ == "__main__":
    read_scale_data()
