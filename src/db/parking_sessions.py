from datetime import datetime
from mysql.connector import Error

def now_str():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def create_session_if_not_active(conn, plate):
    plate = (plate or "").strip().upper()
    if not plate:
        return False
    cur = conn.cursor()
    try:
        cur.execute(
            "SELECT id FROM parking_sessions WHERE plate=%s AND status='active' ORDER BY entry_time DESC LIMIT 1",
            (plate,))
        if cur.fetchone():
            return True
        cur.execute(
            "INSERT INTO parking_sessions (plate,entry_time,status,amount_due,created_at) VALUES (%s,%s,%s,%s,%s)",
            (plate, now_str(), "active", 0.00, now_str()))
        conn.commit(); return True
    except Error as e:
        print(f"Create session failed: {e}"); return False
    finally:
        cur.close()

def fetch_active_session_by_plate(conn, plate):
    plate = (plate or "").strip().upper()
    if not plate:
        return None
    cur = conn.cursor()
    try:
        cur.execute(
            "SELECT id,plate,entry_time,status FROM parking_sessions WHERE plate=%s AND status='active' ORDER BY entry_time DESC LIMIT 1",
            (plate,))
        return cur.fetchone()
    finally:
        cur.close()

def fetch_active_sessions(conn):
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT id, plate, entry_time,
                   TIMESTAMPDIFF(MINUTE, entry_time, NOW()) AS duration_minutes,
                   status, amount_due
            FROM parking_sessions WHERE status='active' ORDER BY entry_time DESC""")
        return cur.fetchall()
    finally:
        cur.close()

def count_active_sessions(conn):
    cur = conn.cursor()
    try:
        cur.execute("SELECT COUNT(*) FROM parking_sessions WHERE status='active'")
        row = cur.fetchone(); return row[0] if row else 0
    finally:
        cur.close()

def close_session(conn, session_id, amount_due):
    cur = conn.cursor()
    try:
        cur.execute(
            "UPDATE parking_sessions SET exit_time=%s,status='closed',amount_due=%s WHERE id=%s",
            (now_str(), amount_due, session_id))
        conn.commit(); return cur.rowcount > 0
    except Error as e:
        print(f"Close session failed: {e}"); return False
    finally:
        cur.close()

def check_plate_access(conn, plate):
    """Return dict with access_type and details. Used by parking officer."""
    plate = (plate or "").strip().upper()
    if not plate:
        return {"has_access": False, "access_type": None, "details": "No plate provided"}
    cur = conn.cursor(dictionary=True)
    try:
        # Check active semester permit
        cur.execute("""
            SELECT sp.id, sp.plate, sp.start_date, sp.end_date,
                   u.username, u.full_name
            FROM semester_permits sp
            JOIN users u ON sp.user_id = u.id
            WHERE sp.plate=%s AND CURDATE() BETWEEN sp.start_date AND sp.end_date
            LIMIT 1""", (plate,))
        sem = cur.fetchone()
        if sem:
            return {"has_access": True, "access_type": "Semester Permit",
                    "details": f"Valid until {sem['end_date']} — {sem['full_name'] or sem['username']}",
                    "row": sem}

        # Check today's daily permit
        cur.execute("""
            SELECT dp.id, dp.plate, dp.permit_date, u.username, u.full_name
            FROM daily_permits dp
            JOIN users u ON dp.user_id = u.id
            WHERE dp.plate=%s AND dp.permit_date=CURDATE()
            LIMIT 1""", (plate,))
        daily = cur.fetchone()
        if daily:
            return {"has_access": True, "access_type": "Daily Permit",
                    "details": f"Valid today — {daily['full_name'] or daily['username']}",
                    "row": daily}

        # Check active PAYG session
        cur.execute("""
            SELECT id, plate, entry_time,
                   TIMESTAMPDIFF(MINUTE, entry_time, NOW()) AS minutes
            FROM parking_sessions
            WHERE plate=%s AND status='active' LIMIT 1""", (plate,))
        payg = cur.fetchone()
        if payg:
            return {"has_access": True, "access_type": "Pay-As-You-Go",
                    "details": f"Active since {payg['entry_time']} ({payg['minutes']} min)",
                    "row": payg}

        return {"has_access": False, "access_type": None,
                "details": "No valid permit or active session found"}
    finally:
        cur.close()
