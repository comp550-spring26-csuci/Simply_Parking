import os
import hashlib
# from dotenv import load_dotenv
import mysql.connector
from mysql.connector import Error

# load_dotenv()

#DB_HOST = "137.184.46.194"
#DB_NAME = "crsmcike_simply_park"
#DB_USER = "crsmcike_simplydb"
#DB_PASS = "COMP550SWE!"
#DB_PORT = 3306


class DatabaseManager:
    def __init__(self):
        try:
            self.conn = mysql.connector.connect(
                host="137.184.46.194",
                user="crsmcike_simplydb",
                password="COMP550SWE!",
                database="crsmcike_simply_park",
                port=3306,
#                host=os.getenv("DB_HOST"),
#                port=int(os.getenv("DB_PORT")),
#                user=os.getenv("DB_USER"),
#                password=os.getenv("DB_PASSWORD"),
#                database=os.getenv("DB_NAME"),
            ) 
            self.conn.autocommit = True

            if self.conn.is_connected():
                print("Connected to database")
                self._init_table()
                self._init_users_table()
                self._seed_default_admin()
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

    def _init_users_table(self):
        cur = self.conn.cursor()
        try:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    username VARCHAR(64) NOT NULL UNIQUE,
                    password_hash VARCHAR(128) NOT NULL,
                    role VARCHAR(32) NOT NULL,
                    full_name VARCHAR(128),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            self.conn.commit()
        finally:
            cur.close()

    def _hash_password(self, password: str) -> str:
        return hashlib.sha256(password.encode("utf-8")).hexdigest()

    def _seed_default_admin(self):
        cur = self.conn.cursor()
        try:
            cur.execute("SELECT id FROM users WHERE username = %s", ("admin",))
            row = cur.fetchone()
            if row is None:
                cur.execute(
                    """
                    INSERT INTO users (username, password_hash, role, full_name)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (
                        "admin",
                        self._hash_password("admin123"),
                        "admin",
                        "System Administrator",
                    ),
                )
                self.conn.commit()
                print("Default admin created: admin / admin123")
        finally:
            cur.close()

    def create_user(self, username: str, password: str, role: str, full_name: str = "") -> bool:
        username = (username or "").strip()
        password = (password or "").strip()
        role = (role or "").strip().lower()
        full_name = (full_name or "").strip()

        if not username or not password or not role:
            return False

        cur = self.conn.cursor()
        try:
            cur.execute(
                """
                INSERT INTO users (username, password_hash, role, full_name)
                VALUES (%s, %s, %s, %s)
                """,
                (username, self._hash_password(password), role, full_name),
            )
            self.conn.commit()
            return True
        except Error as e:
            print(f"Create user failed: {e}")
            return False
        finally:
            cur.close()

    def authenticate_user(self, username: str, password: str):
        username = (username or "").strip()
        password_hash = self._hash_password((password or "").strip())

        cur = self.conn.cursor(dictionary=True)
        try:
            cur.execute(
                """
                SELECT id, username, role, full_name
                FROM users
                WHERE username = %s AND password_hash = %s
                """,
                (username, password_hash),
            )
            return cur.fetchone()
        finally:
            cur.close()

    def fetch_users(self):
        cur = self.conn.cursor()
        try:
            cur.execute(
                """
                SELECT id, username, role, full_name, created_at
                FROM users
                ORDER BY created_at DESC
                """
            )
            return cur.fetchall()
        finally:
            cur.close()

    def reset_password(self, user_id: int, new_password: str) -> bool:
        cur = self.conn.cursor()
        try:
            cur.execute(
                "UPDATE users SET password_hash = %s WHERE id = %s",
                (self._hash_password(new_password), user_id),
            )
            self.conn.commit()
            return True
        except Error as e:
            print(f"Reset password failed: {e}")
            return False
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