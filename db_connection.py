import os
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv

# Load .env file
load_dotenv()


def create_db_connection():
    """
    Creates a connection to the MySQL database.
    Returns the connection object if successful, None otherwise.
    """
    try:
        connection = mysql.connector.connect(
            host=os.getenv('DB_HOST'),
            database=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD')
        )
        if connection.is_connected():
            print("Connected to MySQL database")
            return connection
    except Error as e:
        print(f"Error while connecting to MySQL: {e}")
    return None
