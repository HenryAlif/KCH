import subprocess
import threading
import signal
import sys
import logging

# Konfigurasi logging
logging.basicConfig(
    filename="autorun.log",  # Nama file log
    level=logging.INFO,      # Level log
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Global untuk proses
processes = []

# Fungsi untuk menjalankan program
def run_program(name, command):
    try:
        logging.info(f"Starting {name}...")
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        processes.append(process)

        # Baca output program dan log-nya
        for line in process.stdout:
            logging.info(f"{name}: {line.strip()}")
        for line in process.stderr:
            logging.error(f"{name} [ERROR]: {line.strip()}")
    except Exception as e:
        logging.error(f"Error in {name}: {e}")

# Fungsi untuk menangani sinyal stop
def stop_all_processes(signal_received, frame):
    logging.info("Stopping all processes...")
    for process in processes:
        process.terminate()  # Berhenti dengan graceful termination
    sys.exit(0)

# Tangani CTRL+C untuk menghentikan
signal.signal(signal.SIGINT, stop_all_processes)

# Main program
if __name__ == "__main__":
    # Jalankan server dan client dalam thread

    server_thread = threading.Thread(
        target=run_program, 
        args=("Server", ["python", "D:\\Source Code\\Magang Kalbe\\Raspberry Pi\\socket\\tryserver.py"])
    )
    client_thread = threading.Thread(
        target=run_program, 
        args=("Client", ["python", "D:\\Source Code\\Magang Kalbe\\Raspberry Pi\\socket\\tryclientdb.py"])
    )

    server_thread.start()
    client_thread.start()

    # Tunggu hingga thread selesai (program terus berjalan hingga dihentikan)
    server_thread.join()
    client_thread.join()
