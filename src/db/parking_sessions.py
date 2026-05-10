from datetime import datetime
from mysql.connector import Error

FREE_MINUTES = 30
DAILY_PERMIT_AMOUNT = 6.00


def now_str():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def create_session_if_not_active(conn, plate):
    plate = (plate or "").strip().upper()

    if not plate:
        return False

    cur = conn.cursor()
    try:
        cur.execute(
            """
            SELECT id
            FROM parking_sessions
            WHERE plate = %s AND status = 'active'
            ORDER BY entry_time DESC
            LIMIT 1
            """,
            (plate,),
        )

        existing = cur.fetchone()
        if existing:
            return True

        cur.execute(
            """
            INSERT INTO parking_sessions (plate, entry_time, status, amount_due, created_at)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (plate, now_str(), "active", 0.00, now_str()),
        )
        conn.commit()
        return True

    except Error as e:
        print(f"Create parking session failed: {e}")
        return False
    finally:
        cur.close()


def fetch_active_session_by_plate(conn, plate):
    plate = (plate or "").strip().upper()

    if not plate:
        return None

    cur = conn.cursor()
    try:
        cur.execute(
            """
            SELECT id, plate, entry_time, status
            FROM parking_sessions
            WHERE plate = %s AND status = 'active'
            ORDER BY entry_time DESC
            LIMIT 1
            """,
            (plate,),
        )
        return cur.fetchone()
    finally:
        cur.close()


def close_session(conn, session_id, amount_due):
    cur = conn.cursor()
    try:
        cur.execute(
            """
            UPDATE parking_sessions
            SET exit_time = %s,
                status = 'closed',
                amount_due = %s
            WHERE id = %s
            """,
            (now_str(), amount_due, session_id),
        )
        conn.commit()
        return cur.rowcount > 0
    except Error as e:
        print(f"Close parking session failed: {e}")
        return False
    finally:
        cur.close()