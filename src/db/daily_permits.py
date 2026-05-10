from datetime import datetime, date
from mysql.connector import Error

def now_str():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def create_daily_permit(conn, user_id, plate, permit_date=None, amount=6.00):
    plate = (plate or "").strip().upper()
    permit_date = permit_date or date.today()

    if not user_id or not plate:
        return False

    cur = conn.cursor()
    try:
        cur.execute(
            """
            INSERT INTO daily_permits (user_id, plate, permit_date, amount, created_at)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (user_id, plate, permit_date, amount, now_str()),
        )
        conn.commit()
        return True
    except Error as e:
        print(f"Create daily permit failed: {e}")
        return False
    finally:
        cur.close()

def fetch_daily_permits_for_user(conn, user_id, limit=100):
    cur = conn.cursor()
    try:
        cur.execute(
            """
            SELECT id, plate, permit_date, amount, created_at
            FROM daily_permits
            WHERE user_id = %s
            ORDER BY permit_date DESC, created_at DESC
            LIMIT %s
            """,
            (user_id, limit),
        )
        return cur.fetchall()
    finally:
        cur.close()

    

def has_daily_permit_today(conn, user_id, plate):
    cur = conn.cursor()
    try:
        cur.execute(
            """
            SELECT 1
            FROM daily_permits
            WHERE user_id = %s AND plate = %s AND permit_date = CURDATE()
            LIMIT 1
            """,
            (user_id, plate),
        )
        return cur.fetchone() is not None
    finally:
        cur.close()

def fetch_today_daily_permits_for_user(conn, user_id):
    cur = conn.cursor()
    try:
        cur.execute(
            """
            SELECT id, plate, permit_date, amount, created_at
            FROM daily_permits
            WHERE user_id = %s AND permit_date = CURDATE()
            ORDER BY created_at DESC
            LIMIT 10
            """,
            (user_id,),
        )
        return cur.fetchall()
    finally:
        cur.close()