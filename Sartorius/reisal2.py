import serial
import time

# Set the serial port according to your system
SERIAL_PORT = 'COM6'  # Update this to the correct COM port (e.g., /dev/ttyUSB0 for Linux)
SERIAL_RATE = 9600  # Baudrate (as per Sartorius manual)
TIMEOUT = 5  # Set a timeout for reading

def clean_data(raw_data):
    # Remove null bytes and filter out garbage data
    return raw_data.replace(b'\x00', b'').decode('ascii', errors='ignore').strip()

def read_serial_data():
    try:
        # Open the serial port
        ser = serial.Serial(SERIAL_PORT, SERIAL_RATE, timeout=TIMEOUT)
        
        # Flush input buffer to avoid stale data
        ser.flushInput()

        while True:
            # Read the data from the scale as raw bytes
            if ser.in_waiting > 0:  # Check if data is available
                raw_data = ser.read(ser.in_waiting)  # Read raw bytes
                cleaned_data = clean_data(raw_data)
                
                if cleaned_data:
                    print(f"Cleaned Weight data: {cleaned_data}")
                else:
                    print("Received data contains only null or invalid bytes.")

            else:
                print("No data available, waiting...")
            time.sleep(10)  # Wait for a second before reading again

    except serial.SerialException as e:
        print(f"Error: {e}")
    finally:
        if ser.is_open:
            ser.close()

if __name__ == "__main__":
    read_serial_data()
