from datetime import datetime
from mysql.connector import Error

def now_str():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def add_log(conn, event_type, details="", user_id=None, username=None):
    cur = conn.cursor()
    try:
        cur.execute(
            """
            INSERT INTO audit_logs (user_id, username, event_type, details, created_at)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (user_id, username, event_type, details, now_str()),
        )
        conn.commit()
        return True
    except Error as e:
        print(f"Add log failed: {e}")
        return False
    finally:
        cur.close()

def fetch_logs(conn, limit=100):
    cur = conn.cursor()
    try:
        cur.execute(
            """
            SELECT id, username, event_type, details, created_at
            FROM audit_logs
            ORDER BY created_at DESC
            LIMIT %s
            """,
            (limit,),
        )
        return cur.fetchall()
    finally:
        cur.close()