import logging
import mysql.connector
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Database connection setup
# PostgreSQL connection
POSTGRESQL_DB_URI = "postgresql://users_pims_engineer:Engineer_2023@10.106.1.40/pims_prod"
engine_postgresql = create_engine(POSTGRESQL_DB_URI)
SessionPostgreSQL = sessionmaker(bind=engine_postgresql)
session_postgresql = SessionPostgreSQL()

# MySQL connection
try:
    conn_mysql = mysql.connector.connect(
        host="10.126.15.138",
        user="root",
        password="s4k4f4rmA",
        database="ems_saka"
    )
    cursor_mysql = conn_mysql.cursor()
    logging.info("Connected to MySQL database.")
except mysql.connector.Error as err:
    logging.error(f"Failed to connect to MySQL: {err}")
    conn_mysql = None

# Function to send data to both databases
def kirim_data_ke_database(h_value, d_value, t_value, status, code_instrument, time_series):
    """
    Fungsi untuk mengirim data ke PostgreSQL dan MySQL.
    """
    # Kirim data ke PostgreSQL
    try:
        session_postgresql.execute(
            """
            INSERT INTO sakaplant_prod_ipc_staging (t_value, d_value, h_value, status, code_instrument, time_series)
            VALUES (:t_value, :d_value, :h_value, :status, :code_instrument, :time_series)
            """,
            {
                "t_value": t_value,
                "d_value": d_value,
                "h_value": h_value,
                "status": status,
                "code_instrument": code_instrument,
                "time_series": time_series
            }
        )
        session_postgresql.commit()
        logging.info("Data inserted into PostgreSQL.")
    except Exception as e:
        logging.error(f"Failed to insert data into PostgreSQL: {e}")
        session_postgresql.rollback()

    # Kirim data ke MySQL
    if conn_mysql:
        try:
            val = (t_value, d_value, h_value, status, code_instrument, time_series)
            sql = """
                INSERT INTO sakaplant_prod_ipc_staging (t_value, d_value, h_value, status, code_instrument, time_series)
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            cursor_mysql.execute(sql, val)
            conn_mysql.commit()
            logging.info("Data inserted into MySQL.")
        except mysql.connector.Error as err:
            logging.error(f"Failed to insert data into MySQL: {err}")

# Example data parsing and sending
def process_data():
    """
    Simulasi pembacaan data dan pengiriman ke database.
    """
    # Contoh data yang sudah diparsing
    hardness = 75.5
    diameter = 50.2
    thickness = 10.1
    status = "N"
    code_instrument = "A20230626002"
    time_series = "2025-01-07 12:34:56"

    # Kirim data ke database
    kirim_data_ke_database(hardness, diameter, thickness, status, code_instrument, time_series)

if __name__ == "__main__":
    process_data()

    # Close MySQL connection
    if conn_mysql:
        cursor_mysql.close()
        conn_mysql.close()
        logging.info("MySQL connection closed.")

    # Close PostgreSQL session
    session_postgresql.close()
    logging.info("PostgreSQL session closed.")
