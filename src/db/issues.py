from datetime import datetime
from mysql.connector import Error

def now_str():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def create_issue(conn, user_id, username, location, category, priority, description):
    location = (location or "").strip()
    category = (category or "").strip()
    priority = (priority or "").strip()
    description = (description or "").strip()

    if not user_id or not username or not location or not category or not priority or not description:
        return False

    cur = conn.cursor()
    try:
        cur.execute(
            """
            INSERT INTO issues (
                reported_by_user_id,
                reported_by_username,
                location,
                category,
                priority,
                description,
                status,
                created_at
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                user_id,
                username,
                location,
                category,
                priority,
                description,
                "Open",
                now_str(),
            ),
        )
        conn.commit()
        return True
    except Error as e:
        print(f"Create issue failed: {e}")
        return False
    finally:
        cur.close()

def fetch_issues(conn, limit=200):
    cur = conn.cursor()
    try:
        cur.execute(
            """
            SELECT id, reported_by_username, location, category, priority, status, description, created_at
            FROM issues
            ORDER BY created_at DESC
            LIMIT %s
            """,
            (limit,),
        )
        return cur.fetchall()
    finally:
        cur.close()

def fetch_issues_by_user(conn, user_id, limit=200):
    cur = conn.cursor()
    try:
        cur.execute(
            """
            SELECT id, reported_by_username, location, category, priority, status, description, created_at
            FROM issues
            WHERE reported_by_user_id = %s
            ORDER BY created_at DESC
            LIMIT %s
            """,
            (user_id, limit),
        )
        return cur.fetchall()
    finally:
        cur.close()

def update_issue_status(conn, issue_id, status):
    allowed = {"Open", "In Progress", "Resolved"}
    status = (status or "").strip()

    if not issue_id or not status or status not in allowed:
        return False

    cur = conn.cursor()
    try:
        cur.execute(
            "UPDATE issues SET status = %s WHERE id = %s",
            (status, issue_id),
        )
        conn.commit()
        return cur.rowcount > 0
    except Error as e:
        print(f"Update issue status failed: {e}")
        return False
    finally:
        cur.close()