from datetime import datetime
from mysql.connector import Error
from utils.hashing import hash_password

def now_str():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def seed_default_admin(conn):
    cur = conn.cursor()
    try:
        cur.execute("SELECT id FROM users WHERE username = %s", ("admin",))
        row = cur.fetchone()
        if row is None:
            cur.execute(
                """
                INSERT INTO users (username, password_hash, role, full_name, created_at)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (
                    "admin",
                    hash_password("admin123"),
                    "admin",
                    "System Administrator",
                    now_str(),
                ),
            )
            conn.commit()
            print("Default admin created: admin / admin123")
    finally:
        cur.close()

def create_user(conn, username, password, role, full_name=""):
    username = (username or "").strip()
    password = (password or "").strip()
    role = (role or "").strip().lower()
    full_name = (full_name or "").strip()

    if not username or not password or not role:
        return False

    cur = conn.cursor()
    try:
        cur.execute(
            """
            INSERT INTO users (username, password_hash, role, full_name, created_at)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (username, hash_password(password), role, full_name, now_str()),
        )
        conn.commit()
        return True
    except Error as e:
        print(f"Create user failed: {e}")
        return False
    finally:
        cur.close()

def authenticate_user(conn, username, password):
    username = (username or "").strip()
    password_hash = hash_password((password or "").strip())

    cur = conn.cursor(dictionary=True)
    try:
        cur.execute(
            """
            SELECT id, username, role, full_name
            FROM users
            WHERE username = %s AND password_hash = %s
            """,
            (username, password_hash),
        )
        return cur.fetchone()
    finally:
        cur.close()

def fetch_users(conn):
    cur = conn.cursor()
    try:
        cur.execute(
            """
            SELECT id, username, role, full_name, created_at
            FROM users
            ORDER BY created_at DESC
            """
        )
        return cur.fetchall()
    finally:
        cur.close()

def delete_user(conn, user_id):
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM users WHERE id = %s", (user_id,))
        conn.commit()
        return cur.rowcount > 0
    except Error as e:
        print(f"Delete user failed: {e}")
        return False
    finally:
        cur.close()

def reset_password(conn, user_id, new_password):
    cur = conn.cursor()
    try:
        cur.execute(
            "UPDATE users SET password_hash = %s WHERE id = %s",
            (hash_password(new_password), user_id),
        )
        conn.commit()
        return True
    except Error as e:
        print(f"Reset password failed: {e}")
        return False
    finally:
        cur.close()