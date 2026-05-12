from datetime import datetime
from mysql.connector import Error


def now_str():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def create_payg_payment(conn, user_id, plate, duration_minutes, amount,
                        parking_session_id=None, stripe_session_id=None,
                        stripe_payment_intent_id=None):
    plate = (plate or "").strip().upper()
    if not plate or duration_minutes is None or amount is None:
        return False

    cur = conn.cursor()
    try:
        if stripe_payment_intent_id:
            cur.execute(
                "SELECT id FROM payg_payments WHERE stripe_payment_intent_id=%s LIMIT 1",
                (stripe_payment_intent_id,),
            )
            if cur.fetchone():
                return True

        cur.execute(
            """INSERT INTO payg_payments
               (user_id, plate, parking_session_id, duration_minutes, amount,
                stripe_session_id, stripe_payment_intent_id, created_at)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s)""",
            (user_id, plate, parking_session_id, duration_minutes, amount,
             stripe_session_id, stripe_payment_intent_id, now_str()),
        )
        conn.commit()
        return True
    except Error as e:
        print(f"Create PAYG payment failed: {e}")
        return False
    finally:
        cur.close()


def payg_payment_exists(conn, stripe_payment_intent_id):
    if not stripe_payment_intent_id:
        return False
    cur = conn.cursor()
    try:
        cur.execute(
            "SELECT id FROM payg_payments WHERE stripe_payment_intent_id=%s LIMIT 1",
            (stripe_payment_intent_id,),
        )
        return cur.fetchone() is not None
    finally:
        cur.close()


def fetch_payg_payments_for_user(conn, user_id, limit=100):
    cur = conn.cursor()
    try:
        cur.execute(
            """SELECT id, plate, duration_minutes, amount, created_at
               FROM payg_payments
               WHERE user_id=%s ORDER BY created_at DESC LIMIT %s""",
            (user_id, limit),
        )
        return cur.fetchall()
    finally:
        cur.close()
