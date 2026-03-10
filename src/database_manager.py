# database_manager.py
import mysql.connector


class DatabaseManager:
    def __init__(
        self,
        host="127.0.0.1",
        user="simplydb",
        password="Comp550SWE!",
        database="simply_park",
        port=3306,
    ):
        self.conn = mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            database=database,
            port=port,
            ssl_disabled=True,  # avoid SSL.wrap_socket issues on this setup
        )
        self._init_table()

    def _init_table(self):
        cur = self.conn.cursor()
        # NOTE: plate is NOT UNIQUE so duplicates are allowed
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
        finally:
            cur.close()

    def fetch_all(self, limit=None):
        sql = "SELECT id, plate, source_file, timestamp FROM plates ORDER BY timestamp DESC"
        params = ()
        if isinstance(limit, int) and limit > 0:
            sql += " LIMIT %s"
            params = (limit,)

        cur = self.conn.cursor()
        cur.execute(sql, params)
        rows = cur.fetchall()
        cur.close()
        return rows

    def close(self):
        try:
            self.conn.close()
        except Exception:
            pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()
