
from datetime import datetime
from mysql.connector import Error


def now_str():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def create_notification(conn, title, message, notification_type="general", user_id=None):
    cur = conn.cursor()
    try:
        cur.execute(
            """
            INSERT INTO notifications (user_id, title, message, notification_type, is_read, created_at)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (user_id, title, message, notification_type, False, now_str()),
        )
        conn.commit()
        return cur.lastrowid
    except Error as e:
        print(f"Create notification failed: {e}")
        return None
    finally:
        cur.close()

def mark_notification_read(conn, notification_id):
    cur = conn.cursor()
    try:
        cur.execute(
            "UPDATE notifications SET is_read = TRUE WHERE id = %s",
            (notification_id,),
        )
        conn.commit()
        return cur.rowcount > 0
    except Error as e:
        print(f"Mark notification read failed: {e}")
        return False
    finally:
        cur.close()


def mark_all_notifications_read(conn, user_id=None):
    cur = conn.cursor()
    try:
        if user_id is None:
            cur.execute("UPDATE notifications SET is_read = TRUE WHERE is_read = FALSE")
        else:
            cur.execute(
                """
                UPDATE notifications
                SET is_read = TRUE
                WHERE is_read = FALSE
                  AND (user_id = %s OR user_id IS NULL)
                """,
                (user_id,),
            )
        conn.commit()
        return True
    except Error as e:
        print(f"Mark all notifications read failed: {e}")
        return False
    finally:
        cur.close()

def fetch_notifications(conn, user_id=None, limit=50):
    cur = conn.cursor()
    try:
        if user_id is None:
            cur.execute(
                """
                SELECT id, user_id, title, message, notification_type, is_read, created_at
                FROM notifications
                ORDER BY created_at DESC
                LIMIT %s
                """,
                (limit,),
            )
        else:
            cur.execute(
                """
                SELECT id, user_id, title, message, notification_type, is_read, created_at
                FROM notifications
                WHERE user_id = %s
                ORDER BY created_at DESC
                LIMIT %s
                """,
                (user_id, limit),
            )
        return cur.fetchall()
    finally:
        cur.close()


def fetch_unread_count(conn, user_id=None):
    cur = conn.cursor()
    try:
        if user_id is None:
            cur.execute(
                """
                SELECT COUNT(*)
                FROM notifications
                WHERE is_read = FALSE
                """
            )
        else:
            cur.execute(
                """
                SELECT COUNT(*)
                FROM notifications
                WHERE is_read = FALSE
                  AND user_id = %s
                """,
                (user_id,),
            )
        row = cur.fetchone()
        return row[0] if row else 0
    finally:
        cur.close()


def fetch_latest_notification_id(conn, user_id=None):
    cur = conn.cursor()
    try:
        if user_id is None:
            cur.execute("SELECT MAX(id) FROM notifications")
        else:
            cur.execute(
                """
                SELECT MAX(id)
                FROM notifications
                WHERE user_id = %s
                """,
                (user_id,),
            )
        row = cur.fetchone()
        return row[0] if row and row[0] is not None else 0
    finally:
        cur.close()


def fetch_unread_notifications_after(conn, last_seen_id, user_id=None):
    cur = conn.cursor()
    try:
        if user_id is None:
            cur.execute(
                """
                SELECT id, user_id, title, message, notification_type, is_read, created_at
                FROM notifications
                WHERE id > %s AND is_read = FALSE
                ORDER BY id ASC
                LIMIT 10
                """,
                (last_seen_id,),
            )
        else:
            cur.execute(
                """
                SELECT id, user_id, title, message, notification_type, is_read, created_at
                FROM notifications
                WHERE id > %s
                  AND is_read = FALSE
                  AND user_id = %s
                ORDER BY id ASC
                LIMIT 10
                """,
                (last_seen_id, user_id),
            )
        return cur.fetchall()
    finally:
        cur.close()