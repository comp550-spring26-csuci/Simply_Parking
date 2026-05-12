from datetime import datetime, date
from mysql.connector import Error


def now_str():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def create_daily_permit(conn, user_id, plate, permit_date=None, amount=6.00,
                        stripe_session_id=None, stripe_payment_intent_id=None):
    plate = (plate or "").strip().upper()
    permit_date = permit_date or date.today()
    if not user_id or not plate:
        return False

    cur = conn.cursor()
    try:
        if stripe_payment_intent_id:
            cur.execute(
                "SELECT id FROM daily_permits WHERE stripe_payment_intent_id=%s LIMIT 1",
                (stripe_payment_intent_id,),
            )
            if cur.fetchone():
                return True

        cur.execute(
            """INSERT INTO daily_permits
               (user_id, plate, permit_date, amount, stripe_session_id,
                stripe_payment_intent_id, created_at)
               VALUES (%s,%s,%s,%s,%s,%s,%s)""",
            (user_id, plate, permit_date, amount, stripe_session_id,
             stripe_payment_intent_id, now_str()),
        )
        conn.commit()
        return True
    except Error as e:
        print(f"Create daily permit failed: {e}")
        return False
    finally:
        cur.close()


def daily_payment_exists(conn, stripe_payment_intent_id):
    if not stripe_payment_intent_id:
        return False
    cur = conn.cursor()
    try:
        cur.execute(
            "SELECT id FROM daily_permits WHERE stripe_payment_intent_id=%s LIMIT 1",
            (stripe_payment_intent_id,),
        )
        return cur.fetchone() is not None
    finally:
        cur.close()


def fetch_daily_permits_for_user(conn, user_id, limit=100):
    cur = conn.cursor()
    try:
        cur.execute(
            """SELECT id, plate, permit_date, amount, created_at
               FROM daily_permits
               WHERE user_id=%s
               ORDER BY permit_date DESC, created_at DESC LIMIT %s""",
            (user_id, limit),
        )
        return cur.fetchall()
    finally:
        cur.close()


def fetch_today_daily_permits_for_user(conn, user_id):
    cur = conn.cursor()
    try:
        cur.execute(
            """SELECT id, plate, permit_date, amount, created_at
               FROM daily_permits
               WHERE user_id=%s AND permit_date=CURDATE()
               ORDER BY created_at DESC LIMIT 10""",
            (user_id,),
        )
        return cur.fetchall()
    finally:
        cur.close()


def has_daily_permit_today(conn, user_id, plate):
    plate = (plate or "").strip().upper()
    cur = conn.cursor()
    try:
        cur.execute(
            """SELECT id FROM daily_permits
               WHERE user_id=%s AND plate=%s AND permit_date=CURDATE()
               LIMIT 1""",
            (user_id, plate),
        )
        return cur.fetchone() is not None
    finally:
        cur.close()


def fetch_all_daily_permits(conn, limit=100):
    cur = conn.cursor()
    try:
        cur.execute(
            """SELECT dp.id, u.username, dp.plate, dp.permit_date, dp.amount, dp.created_at
               FROM daily_permits dp JOIN users u ON dp.user_id=u.id
               ORDER BY dp.created_at DESC LIMIT %s""",
            (limit,),
        )
        return cur.fetchall()
    finally:
        cur.close()


def count_today_daily_permits(conn):
    cur = conn.cursor()
    try:
        cur.execute("SELECT COUNT(*) FROM daily_permits WHERE permit_date=CURDATE()")
        row = cur.fetchone()
        return row[0] if row else 0
    finally:
        cur.close()
