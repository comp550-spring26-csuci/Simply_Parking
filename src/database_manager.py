import os
from dotenv import load_dotenv
import mysql.connector
from mysql.connector import Error

load_dotenv()

class DatabaseManager:
    def __init__(self):
        try:
            self.conn = mysql.connector.connect(
                host=os.getenv("DB_HOST"),
                port=int(os.getenv("DB_PORT")),
                user=os.getenv("DB_USER"),
                password=os.getenv("DB_PASSWORD"),
                database=os.getenv("DB_NAME"),
            )

            if self.conn.is_connected():
                print("Connected to database")
                self._init_table()
            else:
                raise Exception("Connection failed")

        except Error as e:
            raise Exception(f"Database connection failed: {e}")

    def _init_table(self):
        cur = self.conn.cursor()
        try:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS plates (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    plate VARCHAR(32) NOT NULL,
                    source_file VARCHAR(512),
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            self.conn.commit()
        finally:
            cur.close()

    def insert_plate(self, plate: str, source_file: str) -> bool:
        plate = (plate or "").strip().upper()
        if not plate:
            return False

        cur = self.conn.cursor()
        try:
            cur.execute(
                "INSERT INTO plates (plate, source_file) VALUES (%s, %s)",
                (plate, source_file),
            )
            self.conn.commit()
            return True
        except Error as e:
            print(f"Insert failed: {e}")
            return False
        finally:
            cur.close()

    def fetch_all(self, limit=None):
        sql = "SELECT id, plate, source_file, timestamp FROM plates ORDER BY timestamp DESC"
        params = ()

        if isinstance(limit, int) and limit > 0:
            sql += " LIMIT %s"
            params = (limit,)

        cur = self.conn.cursor()
        try:
            cur.execute(sql, params)
            return cur.fetchall()
        finally:
            cur.close()

    def close(self):
        try:
            if self.conn.is_connected():
                self.conn.close()
        except Exception:
            pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()