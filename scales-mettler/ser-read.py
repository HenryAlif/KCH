import serial
import time

# Set the serial port according to your system
SERIAL_PORT = 'COM5'  # Update this to the correct COM port (e.g., /dev/ttyUSB0 for Linux)
SERIAL_RATE = 9600  # Baudrate sesuai yang diinginkan
TIMEOUT = 5  # Set a timeout for reading

ENCODING = 'utf-8'  # Bisa diubah ke 'utf-16' jika diperlukan

def read_serial_data():
    try:
        # Open the serial port
        ser = serial.Serial(SERIAL_PORT, SERIAL_RATE, timeout=TIMEOUT)
        
        # Flush input buffer to avoid stale data
        ser.flushInput()

        while True:
            # Check if data is available in the input buffer
            if ser.in_waiting > 0:
                raw_data = ser.read(ser.in_waiting)  # Read raw bytes available in the buffer
                try:
                    # Attempt to decode the raw data using the specified encoding
                    data = raw_data.decode(ENCODING).strip()
                    if data:
                        print(f"Weight data: {data}")
                        print(len(data))
                except UnicodeDecodeError as e:
                    # Handle decode error gracefully (skip or log the error)
                    print(f"UnicodeDecodeError: {e}. Received invalid data: {raw_data}")
            else:
                print("No data available, waiting...")
            time.sleep(1)  # Wait for a second before checking again

    except serial.SerialException as e:
        print(f"SerialException: {e}")
    finally:
        if ser.is_open:
            ser.close()

if __name__ == "__main__":
    read_serial_data()

## ------ Statistics ------
## n                 1
## x           0.65420 g
## s dev           --------
## s rel           --------
## Min.         0.6542 g
## Max.         0.6542 g
## Diff.        0.0000 g
## Sum          0.6542 g
## ------------------------
## 08.10.2024 11:26
## User name            MAY
## ------------------------
## Signature
## 
## ========================

## ------------------------
## WEIGHING
## 09.10.2024 10:35
## PT SAKAFARMA
## STMXTG45166 ST2
##   1          1.1771 g