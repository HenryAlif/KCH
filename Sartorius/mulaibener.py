import serial
import time
import base64

# Set the serial port according to your system
SERIAL_PORT = 'COM6'  # Update this to the correct COM port
SERIAL_RATE = 1200     # Adjusted baud rate
TIMEOUT = 5            # Set a timeout for reading

def process_raw_data(raw_data):
    """Process raw binary data to extract readable information."""
    try:
        # Option 1: Decode using a specific encoding (e.g., latin-1, ascii)
        decoded_data = raw_data.decode('latin-1', errors='ignore').strip()
        
        # Print decoded data if available
        if decoded_data:
            print(f"Decoded Data: {decoded_data}")

        # Option 2: Convert raw binary to hexadecimal representation
        hex_representation = raw_data.hex()
        print(f"Hexadecimal Representation: {hex_representation}")

        # Option 3: Convert raw binary to base64
        base64_representation = base64.b64encode(raw_data).decode('utf-8')
        print(f"Base64 Representation: {base64_representation}")

    except Exception as e:
        print(f"Error processing data: {e}")

def read_serial_data():
    """Read data from the serial port and process it."""
    try:
        # Open the serial port
        ser = serial.Serial(SERIAL_PORT, SERIAL_RATE, timeout=TIMEOUT)
        
        # Flush input buffer to avoid stale data
        ser.flushInput()

        print("Listening for data...")

        while True:
            # Check if data is available in the input buffer
            if ser.in_waiting > 0:
                raw_data = ser.read(ser.in_waiting)  # Read raw bytes available in the buffer
                
                # Print the raw binary data for analysis
                print(f"Raw binary data: {raw_data}")

                # Process the raw data to extract readable information
                process_raw_data(raw_data)

                # Save raw binary data for further analysis
                with open('output_binary.txt', 'ab') as f:
                    f.write(raw_data + b'\n')

            else:
                print("No data available, waiting...")
            time.sleep(1)  # Wait for a second before checking again

    except serial.SerialException as e:
        print(f"SerialException: {e}")
    finally:
        if 'ser' in locals() and ser.is_open:
            ser.close()

if __name__ == "__main__":
    read_serial_data()
