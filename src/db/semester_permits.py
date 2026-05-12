from datetime import datetime
from mysql.connector import Error


def now_str():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def create_semester_permit(conn, user_id, plate, start_date, end_date, amount=0.00,
                           stripe_session_id=None, stripe_payment_intent_id=None):
    plate = (plate or "").strip().upper()
    if not user_id or not plate or not start_date or not end_date:
        return False

    cur = conn.cursor()
    try:
        if stripe_payment_intent_id:
            cur.execute(
                "SELECT id FROM semester_permits WHERE stripe_payment_intent_id=%s LIMIT 1",
                (stripe_payment_intent_id,),
            )
            if cur.fetchone():
                return True

        # Block overlapping active semester permit for the same user's same plate.
        cur.execute(
            """SELECT id FROM semester_permits
               WHERE user_id=%s AND plate=%s
                 AND NOT (end_date < %s OR start_date > %s)
               LIMIT 1""",
            (user_id, plate, start_date, end_date),
        )
        if cur.fetchone():
            print("Create semester permit failed: overlapping permit already exists")
            return False

        cur.execute(
            """INSERT INTO semester_permits
               (user_id, plate, start_date, end_date, amount, stripe_session_id,
                stripe_payment_intent_id, created_at)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s)""",
            (user_id, plate, start_date, end_date, amount, stripe_session_id,
             stripe_payment_intent_id, now_str()),
        )
        conn.commit()
        return True
    except Error as e:
        print(f"Create semester permit failed: {e}")
        return False
    finally:
        cur.close()


def semester_payment_exists(conn, stripe_payment_intent_id):
    if not stripe_payment_intent_id:
        return False
    cur = conn.cursor()
    try:
        cur.execute(
            "SELECT id FROM semester_permits WHERE stripe_payment_intent_id=%s LIMIT 1",
            (stripe_payment_intent_id,),
        )
        return cur.fetchone() is not None
    finally:
        cur.close()


def has_active_semester_permit_for_plate(conn, user_id, plate):
    plate = (plate or "").strip().upper()
    cur = conn.cursor()
    try:
        cur.execute(
            """SELECT id FROM semester_permits
               WHERE user_id=%s AND plate=%s AND CURDATE() BETWEEN start_date AND end_date
               LIMIT 1""",
            (user_id, plate),
        )
        return cur.fetchone() is not None
    finally:
        cur.close()


def fetch_semester_permits_for_user(conn, user_id):
    cur = conn.cursor()
    try:
        cur.execute(
            """SELECT id, plate, start_date, end_date, amount, created_at
               FROM semester_permits
               WHERE user_id=%s ORDER BY end_date DESC""",
            (user_id,),
        )
        return cur.fetchall()
    finally:
        cur.close()


def fetch_active_semester_permits_for_user(conn, user_id):
    cur = conn.cursor()
    try:
        cur.execute(
            """SELECT id, plate, start_date, end_date, amount, created_at
               FROM semester_permits
               WHERE user_id=%s AND CURDATE() BETWEEN start_date AND end_date
               ORDER BY end_date DESC""",
            (user_id,),
        )
        return cur.fetchall()
    finally:
        cur.close()


def fetch_all_semester_permits(conn, limit=100):
    cur = conn.cursor()
    try:
        cur.execute(
            """SELECT sp.id, u.username, sp.plate, sp.start_date, sp.end_date,
                      sp.amount, sp.created_at,
                      CASE WHEN CURDATE() BETWEEN sp.start_date AND sp.end_date
                           THEN 'Active' ELSE 'Expired' END AS status
               FROM semester_permits sp JOIN users u ON sp.user_id=u.id
               ORDER BY sp.created_at DESC LIMIT %s""",
            (limit,),
        )
        return cur.fetchall()
    finally:
        cur.close()


def count_active_semester_permits(conn):
    cur = conn.cursor()
    try:
        cur.execute("SELECT COUNT(*) FROM semester_permits WHERE CURDATE() BETWEEN start_date AND end_date")
        row = cur.fetchone()
        return row[0] if row else 0
    finally:
        cur.close()
