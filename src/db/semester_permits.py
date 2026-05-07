from datetime import datetime
from mysql.connector import Error

def now_str():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def create_semester_permit(conn, user_id, plate, start_date, end_date, amount=0.00):
    plate = (plate or "").strip().upper()

    if not user_id or not plate or not start_date or not end_date:
        return False

    cur = conn.cursor()
    try:
        cur.execute(
            """
            INSERT INTO semester_permits (user_id, plate, start_date, end_date, amount, created_at)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (user_id, plate, start_date, end_date, amount, now_str()),
        )
        conn.commit()
        return True
    except Error as e:
        print(f"Create semester permit failed: {e}")
        return False
    finally:
        cur.close()

def fetch_semester_permits_for_user(conn, user_id):
    cur = conn.cursor()
    try:
        cur.execute(
            """
            SELECT id, plate, start_date, end_date, amount, created_at
            FROM semester_permits
            WHERE user_id = %s
            ORDER BY end_date DESC
            """,
            (user_id,),
        )
        return cur.fetchall()
    finally:
        cur.close()

def fetch_active_semester_permits_for_user(conn, user_id):
    cur = conn.cursor()
    try:
        cur.execute(
            """
            SELECT id, plate, start_date, end_date, amount, created_at
            FROM semester_permits
            WHERE user_id = %s
              AND CURDATE() BETWEEN start_date AND end_date
            ORDER BY end_date DESC
            """,
            (user_id,),
        )
        return cur.fetchall()
    finally:
        cur.close()