import socket
import pickle



def server():
    # Setup server socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('localhost', 12345))
    server_socket.listen(1)
    print("Server ready to receive data...")

    while True:
        conn, addr = server_socket.accept()
        print(f"Connected by {addr}")

        # Receive data
        data = conn.recv(4096)
        if not data:
            break
        obj = pickle.loads(data)
        print(f"Received object: {obj}")

        conn.close()

if __name__ == "__main__":
    server()

