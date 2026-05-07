import os
from dotenv import load_dotenv
import mysql.connector
from mysql.connector import Error

load_dotenv()

def create_connection():
    try:
        conn = mysql.connector.connect(
            host=os.getenv("DB_HOST"),
            port=int(os.getenv("DB_PORT")),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME"),
        )
        conn.autocommit = True

        if conn.is_connected():
            print("Connected to database")
            return conn

        raise Exception("Connection failed")

    except Error as e:
        raise Exception(f"Database connection failed: {e}")