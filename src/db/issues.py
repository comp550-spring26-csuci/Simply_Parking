from datetime import datetime
from mysql.connector import Error

def now_str():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def create_issue(conn, user_id, username, location, category, priority, description):
    if not all([user_id, username, location, category, priority, description]):
        return False
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO issues (reported_by_user_id,reported_by_username,location,category,priority,description,status,created_at) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
            (user_id, username, location.strip(), category.strip(), priority.strip(), description.strip(), "Open", now_str()))
        conn.commit(); return True
    except Error as e:
        print(f"Create issue failed: {e}"); return False
    finally:
        cur.close()

def fetch_issues(conn, limit=50):
    cur = conn.cursor()
    try:
        cur.execute(
            "SELECT id,reported_by_user_id,reported_by_username,location,category,priority,status,description,created_at FROM issues ORDER BY created_at DESC LIMIT %s",
            (limit,))
        return cur.fetchall()
    finally:
        cur.close()

def fetch_issues_by_user(conn, user_id, limit=50):
    cur = conn.cursor()
    try:
        cur.execute(
            "SELECT id,reported_by_user_id,reported_by_username,location,category,priority,status,description,created_at FROM issues WHERE reported_by_user_id=%s ORDER BY created_at DESC LIMIT %s",
            (user_id, limit))
        return cur.fetchall()
    finally:
        cur.close()

def update_issue_status(conn, issue_id, status):
    if status not in {"Open","In Progress","Resolved"}:
        return False
    cur = conn.cursor()
    try:
        cur.execute("UPDATE issues SET status=%s WHERE id=%s", (status, issue_id))
        conn.commit(); return cur.rowcount > 0
    except Error as e:
        print(f"Update issue failed: {e}"); return False
    finally:
        cur.close()

def count_open_issues(conn):
    cur = conn.cursor()
    try:
        cur.execute("SELECT COUNT(*) FROM issues WHERE status='Open'")
        row = cur.fetchone(); return row[0] if row else 0
    finally:
        cur.close()
