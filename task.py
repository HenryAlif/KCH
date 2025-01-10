import logging
import time

# Konfigurasi logging
logging.basicConfig(filename='script_log.txt', level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

def main():
    logging.info("Script started")
    try:
        # Tambahkan logika utama script Anda di sini
        while True:
            # Contoh: tulis pesan log setiap 10 detik
            logging.info("Script is running")
            time.sleep(10)
    except Exception as e:
        logging.error(f"An error occurred: {e}")

if __name__ == "__main__":
    main()