import serial
import time

def read_serial_data():
    try:
        # Open serial port with correct settings for Sartorius balance
        ser = serial.Serial(
            port='COM6',            # Update to your actual COM port
            baudrate=1200,          # Match the baudrate with the balance setting
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            bytesize=serial.EIGHTBITS,
            timeout=1               # Non-blocking read
        )
        
        print("Listening to Sartorius balance...")
        
        while True:
            # Read available data from serial port
            if ser.in_waiting > 0:
                data = ser.read_until(b'\r')  # Reading until carriage return (CR)
                process_data(data)
                
    except serial.SerialException as e:
        print(f"Serial error: {e}")
    except Exception as e:
        print(f"General error: {e}")
    finally:
        ser.close()

def process_data(data):
    try:
        # Decode data from bytes to string
        decoded_data = data.decode('ascii', errors='ignore').strip()
        
        # Log the raw output for troubleshooting
        print(f"Raw output: {decoded_data}")
        
        # Example of basic weight data extraction (assuming mg data is sent)
        if "mg" in decoded_data:
            weight_value = decoded_data.split("mg")[0].strip() + " mg"
            print(f"Weight: {weight_value}")
        
        # Extract date and time from the incoming data (assuming it's part of the message)
        current_time = time.strftime("%d-%b-%Y %H:%M:%S", time.localtime())
        print(f"Timestamp: {current_time}")
        
    except Exception as e:
        print(f"Data parsing error: {e}")

if __name__ == "__main__":
    read_serial_data()
