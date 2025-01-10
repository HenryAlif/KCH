import socket
import pickle
import time
import os
import json

def load_id_counter(filename):
    """Load the ID counter from a file."""
    if os.path.exists(filename):
        with open(filename, 'r') as file:
            return int(file.read())
    return 0

def save_id_counter(filename, counter):
    """Save the ID counter to a file."""
    with open(filename, 'w') as file:
        file.write(str(counter))

def append_log(log_filename, data_object):
    """Append a log entry to the JSON log file."""
    log_entry = {
        'id': data_object['id'],
        'key': data_object['key'],
        'number': data_object['number'],
        'timestamp': time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
    }

    # Load existing log data
    if os.path.exists(log_filename):
        with open(log_filename, 'r') as file:
            log_data = json.load(file)
    else:
        log_data = []

    # Append the new log entry
    log_data.append(log_entry)

    # Save the updated log data to the file
    with open(log_filename, 'w') as file:
        json.dump(log_data, file, indent=4)

def client():
    id_counter_file = 'id_counter.txt'
    log_filename = 'log.json'
    
    id_counter = load_id_counter(id_counter_file)  # Load ID counter from file

    while True:
        # Data object to send with incrementing ID
        data_object = {'id': id_counter, 'key': 'value', 'number': 42}

        # Serialize data object
        data = pickle.dumps(data_object)

        try:
            # Setup client socket
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect(('localhost', 12345))

            # Send data
            client_socket.sendall(data)
            print(f"Data sent: {data_object}")

            client_socket.close()
        except ConnectionRefusedError:
            print("Server is not running. Retrying in 5 seconds...")

        # Increment the ID counter
        id_counter += 1
        
        # Save the updated ID counter to file
        save_id_counter(id_counter_file, id_counter)

        # Append the log entry to the JSON log file
        append_log(log_filename, data_object)

        # Wait for 5 seconds before sending the next data
        time.sleep(5)

if __name__ == "__main__":
    client()