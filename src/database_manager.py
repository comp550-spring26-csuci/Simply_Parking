# import os
# import hashlib
# from datetime import datetime
# from dotenv import load_dotenv
# import mysql.connector
# from mysql.connector import Error

# load_dotenv()

# class DatabaseManager:
#     def __init__(self):
#         try:
#             self.conn = mysql.connector.connect(
#                 host=os.getenv("DB_HOST"),
#                 port=int(os.getenv("DB_PORT")),
#                 user=os.getenv("DB_USER"),
#                 password=os.getenv("DB_PASSWORD"),
#                 database=os.getenv("DB_NAME"),
#             )
#             self.conn.autocommit = True

#             if self.conn.is_connected():
#                 print("Connected to database")
#                 self._init_table()
#                 self._init_users_table()
#                 self._init_audit_logs_table()
#                 self._init_vehicles_table()
#                 self._init_issues_table()
#                 self._seed_default_admin()
#             else:
#                 raise Exception("Connection failed")

#         except Error as e:
#             raise Exception(f"Database connection failed: {e}")

#     def _now_str(self) -> str:
#         return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

#     def update_plate_entry(self, record_id: int, plate: str, source_file: str = "", actor_user_id=None, actor_username=None) -> bool:
#         plate = (plate or "").strip().upper()
#         source_file = (source_file or "").strip()

#         if not record_id or not plate:
#             return False

#         cur = self.conn.cursor()
#         try:
#             cur.execute(
#                 """
#                 UPDATE plates
#                 SET plate = %s, source_file = %s
#                 WHERE id = %s
#                 """,
#                 (plate, source_file, record_id),
#             )

#             if cur.rowcount > 0:
#                 self.add_log(
#                     event_type="plate_entry_updated",
#                     details=f"Record ID={record_id}, plate={plate}, source_file={source_file}",
#                     user_id=actor_user_id,
#                     username=actor_username,
#                 )
#                 return True
#             return False
#         except Error as e:
#             print(f"Update plate failed: {e}")
#             return False
#         finally:
#             cur.close()

#     def delete_plate_entry(self, record_id: int, actor_user_id=None, actor_username=None) -> bool:
#         cur = self.conn.cursor()
#         try:
#             cur.execute(
#                 "DELETE FROM plates WHERE id = %s",
#                 (record_id,),
#             )

#             if cur.rowcount > 0:
#                 self.add_log(
#                     event_type="plate_entry_deleted",
#                     details=f"Record ID={record_id}",
#                     user_id=actor_user_id,
#                     username=actor_username,
#                 )
#                 return True
#             return False
#         except Error as e:
#             print(f"Delete plate failed: {e}")
#             return False
#         finally:
#             cur.close()

#     def _init_table(self):
#         cur = self.conn.cursor()
#         try:
#             cur.execute(
#                 """
#                 CREATE TABLE IF NOT EXISTS plates (
#                     id INT AUTO_INCREMENT PRIMARY KEY,
#                     plate VARCHAR(32) NOT NULL,
#                     source_file VARCHAR(512),
#                     timestamp DATETIME NOT NULL
#                 )
#                 """
#             )
#             self.conn.commit()
#         finally:
#             cur.close()

#     def _init_users_table(self):
#         cur = self.conn.cursor()
#         try:
#             cur.execute(
#                 """
#                 CREATE TABLE IF NOT EXISTS users (
#                     id INT AUTO_INCREMENT PRIMARY KEY,
#                     username VARCHAR(64) NOT NULL UNIQUE,
#                     password_hash VARCHAR(128) NOT NULL,
#                     role VARCHAR(32) NOT NULL,
#                     full_name VARCHAR(128),
#                     created_at DATETIME NOT NULL
#                 )
#                 """
#             )
#             self.conn.commit()
#         finally:
#             cur.close()

#     def _init_audit_logs_table(self):
#         cur = self.conn.cursor()
#         try:
#             cur.execute(
#                 """
#                 CREATE TABLE IF NOT EXISTS audit_logs (
#                     id INT AUTO_INCREMENT PRIMARY KEY,
#                     user_id INT NULL,
#                     username VARCHAR(64),
#                     event_type VARCHAR(64) NOT NULL,
#                     details TEXT,
#                     created_at DATETIME NOT NULL,
#                     INDEX idx_event_type (event_type),
#                     INDEX idx_created_at (created_at)
#                 )
#                 """
#             )
#             self.conn.commit()
#         finally:
#             cur.close()

#     def add_log(self, event_type: str, details: str = "", user_id=None, username: str = None) -> bool:
#         cur = self.conn.cursor()
#         try:
#             cur.execute(
#                 """
#                 INSERT INTO audit_logs (user_id, username, event_type, details, created_at)
#                 VALUES (%s, %s, %s, %s, %s)
#                 """,
#                 (user_id, username, event_type, details, self._now_str()),
#             )
#             self.conn.commit()
#             return True
#         except Error as e:
#             print(f"Add log failed: {e}")
#             return False
#         finally:
#             cur.close()

#     def fetch_logs(self, limit=200):
#         cur = self.conn.cursor()
#         try:
#             cur.execute(
#                 """
#                 SELECT id, username, event_type, details, created_at
#                 FROM audit_logs
#                 ORDER BY created_at DESC
#                 LIMIT %s
#                 """,
#                 (limit,),
#             )
#             return cur.fetchall()
#         finally:
#             cur.close()

#     def _hash_password(self, password: str) -> str:
#         return hashlib.sha256(password.encode("utf-8")).hexdigest()

#     def _seed_default_admin(self):
#         cur = self.conn.cursor()
#         try:
#             cur.execute("SELECT id FROM users WHERE username = %s", ("admin",))
#             row = cur.fetchone()
#             if row is None:
#                 cur.execute(
#                     """
#                     INSERT INTO users (username, password_hash, role, full_name, created_at)
#                     VALUES (%s, %s, %s, %s, %s)
#                     """,
#                     (
#                         "admin",
#                         self._hash_password("admin123"),
#                         "admin",
#                         "System Administrator",
#                         self._now_str(),
#                     ),
#                 )
#                 self.conn.commit()
#                 print("Default admin created: admin / admin123")
#         finally:
#             cur.close()

#     def create_user(self, username: str, password: str, role: str, full_name: str = "") -> bool:
#         username = (username or "").strip()
#         password = (password or "").strip()
#         role = (role or "").strip().lower()
#         full_name = (full_name or "").strip()

#         if not username or not password or not role:
#             return False

#         cur = self.conn.cursor()
#         try:
#             cur.execute(
#                 """
#                 INSERT INTO users (username, password_hash, role, full_name, created_at)
#                 VALUES (%s, %s, %s, %s, %s)
#                 """,
#                 (username, self._hash_password(password), role, full_name, self._now_str()),
#             )
#             self.conn.commit()
#             return True
#         except Error as e:
#             print(f"Create user failed: {e}")
#             return False
#         finally:
#             cur.close()

#     def authenticate_user(self, username: str, password: str):
#         username = (username or "").strip()
#         password_hash = self._hash_password((password or "").strip())

#         cur = self.conn.cursor(dictionary=True)
#         try:
#             cur.execute(
#                 """
#                 SELECT id, username, role, full_name
#                 FROM users
#                 WHERE username = %s AND password_hash = %s
#                 """,
#                 (username, password_hash),
#             )
#             return cur.fetchone()
#         finally:
#             cur.close()

#     def fetch_users(self):
#         cur = self.conn.cursor()
#         try:
#             cur.execute(
#                 """
#                 SELECT id, username, role, full_name, created_at
#                 FROM users
#                 ORDER BY created_at DESC
#                 """
#             )
#             return cur.fetchall()
#         finally:
#             cur.close()

#     def reset_password(self, user_id: int, new_password: str) -> bool:
#         cur = self.conn.cursor()
#         try:
#             cur.execute(
#                 "UPDATE users SET password_hash = %s WHERE id = %s",
#                 (self._hash_password(new_password), user_id),
#             )
#             self.conn.commit()
#             return True
#         except Error as e:
#             print(f"Reset password failed: {e}")
#             return False
#         finally:
#             cur.close()

#     def insert_plate(self, plate: str, source_file: str, actor_user_id=None, actor_username=None) -> bool:
#         plate = (plate or "").strip().upper()
#         source_file = (source_file or "").strip()
#         if not plate:
#             return False

#         cur = self.conn.cursor()
#         try:
#             cur.execute(
#                 """
#                 INSERT INTO plates (plate, source_file, timestamp)
#                 VALUES (%s, %s, %s)
#                 """,
#                 (plate, source_file, self._now_str()),
#             )
#             self.conn.commit()

#             self.add_log(
#                 event_type="plate_entry_added",
#                 details=f"Plate={plate}, source_file={source_file}",
#                 user_id=actor_user_id,
#                 username=actor_username,
#             )
#             return True
#         except Error as e:
#             print(f"Insert failed: {e}")
#             return False
#         finally:
#             cur.close()

#     def _init_vehicles_table(self):
#         cur = self.conn.cursor()
#         try:
#             cur.execute(
#                 """
#                 CREATE TABLE IF NOT EXISTS vehicles (
#                     id INT AUTO_INCREMENT PRIMARY KEY,
#                     user_id INT NOT NULL,
#                     plate VARCHAR(32) NOT NULL,
#                     make VARCHAR(64),
#                     model VARCHAR(64),
#                     color VARCHAR(32),
#                     created_at DATETIME NOT NULL,
#                     UNIQUE KEY unique_user_plate (user_id, plate),
#                     CONSTRAINT fk_vehicle_user
#                         FOREIGN KEY (user_id) REFERENCES users(id)
#                         ON DELETE CASCADE
#                 )
#                 """
#             )
#             self.conn.commit()
#         finally:
#             cur.close()

#     def register_vehicle(self, user_id: int, plate: str, make: str = "", model: str = "", color: str = "") -> bool:
#         plate = (plate or "").strip().upper()
#         make = (make or "").strip()
#         model = (model or "").strip()
#         color = (color or "").strip()

#         if not user_id or not plate:
#             return False

#         cur = self.conn.cursor()
#         try:
#             cur.execute(
#                 """
#                 INSERT INTO vehicles (user_id, plate, make, model, color, created_at)
#                 VALUES (%s, %s, %s, %s, %s, %s)
#                 """,
#                 (user_id, plate, make, model, color, self._now_str()),
#             )
#             self.conn.commit()
#             return True
#         except Error as e:
#             print(f"Register vehicle failed: {e}")
#             return False
#         finally:
#             cur.close()

#     def fetch_user_vehicles(self, user_id: int):
#         cur = self.conn.cursor()
#         try:
#             cur.execute(
#                 """
#                 SELECT id, plate, make, model, color, created_at
#                 FROM vehicles
#                 WHERE user_id = %s
#                 ORDER BY created_at DESC
#                 """,
#                 (user_id,),
#             )
#             return cur.fetchall()
#         finally:
#             cur.close()

#     def delete_vehicle(self, vehicle_id: int, user_id: int) -> bool:
#         cur = self.conn.cursor()
#         try:
#             cur.execute(
#                 "DELETE FROM vehicles WHERE id = %s AND user_id = %s",
#                 (vehicle_id, user_id),
#             )
#             self.conn.commit()
#             return cur.rowcount > 0
#         except Error as e:
#             print(f"Delete vehicle failed: {e}")
#             return False
#         finally:
#             cur.close()

#     def _init_issues_table(self):
#         cur = self.conn.cursor()
#         try:
#             cur.execute(
#                 """
#                 CREATE TABLE IF NOT EXISTS issues (
#                     id INT AUTO_INCREMENT PRIMARY KEY,
#                     reported_by_user_id INT NOT NULL,
#                     reported_by_username VARCHAR(64) NOT NULL,
#                     location VARCHAR(128) NOT NULL,
#                     category VARCHAR(64) NOT NULL,
#                     priority VARCHAR(32) NOT NULL,
#                     description TEXT NOT NULL,
#                     status VARCHAR(32) NOT NULL,
#                     created_at DATETIME NOT NULL,
#                     FOREIGN KEY (reported_by_user_id) REFERENCES users(id)
#                         ON DELETE CASCADE
#                 )
#                 """
#             )
#             self.conn.commit()
#         finally:
#             cur.close()

#     def create_issue(self, user_id: int, username: str, location: str, category: str, priority: str, description: str) -> bool:
#         location = (location or "").strip()
#         category = (category or "").strip()
#         priority = (priority or "").strip()
#         description = (description or "").strip()

#         if not user_id or not username or not location or not category or not priority or not description:
#             return False

#         cur = self.conn.cursor()
#         try:
#             cur.execute(
#                 """
#                 INSERT INTO issues (
#                     reported_by_user_id,
#                     reported_by_username,
#                     location,
#                     category,
#                     priority,
#                     description,
#                     status,
#                     created_at
#                 )
#                 VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
#                 """,
#                 (
#                     user_id,
#                     username,
#                     location,
#                     category,
#                     priority,
#                     description,
#                     "Open",
#                     self._now_str(),
#                 ),
#             )
#             self.conn.commit()
#             return True
#         except Error as e:
#             print(f"Create issue failed: {e}")
#             return False
#         finally:
#             cur.close()

#     def fetch_issues(self, limit=200):
#         cur = self.conn.cursor()
#         try:
#             cur.execute(
#                 """
#                 SELECT id, reported_by_username, location, category, priority, status, description, created_at
#                 FROM issues
#                 ORDER BY created_at DESC
#                 LIMIT %s
#                 """,
#                 (limit,),
#             )
#             return cur.fetchall()
#         finally:
#             cur.close()

#     def fetch_issues_by_user(self, user_id: int, limit=200):
#         cur = self.conn.cursor()
#         try:
#             cur.execute(
#                 """
#                 SELECT id, reported_by_username, location, category, priority, status, description, created_at
#                 FROM issues
#                 WHERE reported_by_user_id = %s
#                 ORDER BY created_at DESC
#                 LIMIT %s
#                 """,
#                 (user_id, limit),
#             )
#             return cur.fetchall()
#         finally:
#             cur.close()

#     def update_issue_status(self, issue_id: int, status: str) -> bool:
#         allowed = {"Open", "In Progress", "Resolved"}
#         status = (status or "").strip()
#         if not issue_id or not status:
#             return False
#         if status not in allowed:
#             return False

#         cur = self.conn.cursor()
#         try:
#             cur.execute(
#                 "UPDATE issues SET status = %s WHERE id = %s",
#                 (status, issue_id),
#             )
#             self.conn.commit()
#             return cur.rowcount > 0
#         except Error as e:
#             print(f"Update issue status failed: {e}")
#             return False
#         finally:
#             cur.close()

#     def fetch_all(self, limit=None):
#         sql = "SELECT id, plate, source_file, timestamp FROM plates ORDER BY timestamp DESC"
#         params = ()

#         if isinstance(limit, int) and limit > 0:
#             sql += " LIMIT %s"
#             params = (limit,)

#         cur = self.conn.cursor()
#         try:
#             cur.execute(sql, params)
#             return cur.fetchall()
#         finally:
#             cur.close()

#     def close(self):
#         try:
#             if self.conn.is_connected():
#                 self.conn.close()
#         except Exception:
#             pass

#     def __enter__(self):
#         return self

#     def __exit__(self, exc_type, exc, tb):
#         self.close()

from db.connection import create_connection
from db.schema import init_schema
from db.users import (
    seed_default_admin,
    create_user,
    authenticate_user,
    fetch_users,
    reset_password,
    delete_user,
)
from db.plates import (
    insert_plate,
    fetch_all,
    update_plate_entry,
    delete_plate_entry,
)
from db.logs import add_log, fetch_logs
from db.vehicles import (
    register_vehicle,
    fetch_user_vehicles,
    delete_vehicle,
)
from db.issues import (
    create_issue,
    fetch_issues,
    fetch_issues_by_user,
    update_issue_status,
)
from db.notifications import (
    create_notification,
    fetch_notifications,
    fetch_unread_count,
    mark_notification_read,
    mark_all_notifications_read,
    fetch_latest_notification_id,
    fetch_unread_notifications_after,
)


class DatabaseManager:
    def __init__(self):
        self.conn = create_connection()
        init_schema(self.conn)
        seed_default_admin(self.conn)

    def create_user(self, username, password, role, full_name=""):
        return create_user(self.conn, username, password, role, full_name)

    def authenticate_user(self, username, password):
        return authenticate_user(self.conn, username, password)

    def fetch_users(self):
        return fetch_users(self.conn)

    def delete_user(self, user_id):
        return delete_user(self.conn, user_id)

    def reset_password(self, user_id, new_password):
        return reset_password(self.conn, user_id, new_password)

    def insert_plate(self, plate, source_file, actor_user_id=None, actor_username=None):
        return insert_plate(self.conn, plate, source_file, actor_user_id, actor_username)

    def fetch_all(self, limit=None):
        return fetch_all(self.conn, limit)

    def update_plate_entry(self, record_id, plate, source_file="", actor_user_id=None, actor_username=None):
        return update_plate_entry(self.conn, record_id, plate, source_file, actor_user_id, actor_username)

    def delete_plate_entry(self, record_id, actor_user_id=None, actor_username=None):
        return delete_plate_entry(self.conn, record_id, actor_user_id, actor_username)

    def add_log(self, event_type, details="", user_id=None, username=None):
        return add_log(self.conn, event_type, details, user_id, username)

    def fetch_logs(self, limit=200):
        return fetch_logs(self.conn, limit)

    def register_vehicle(self, user_id, plate, make="", model="", color=""):
        return register_vehicle(self.conn, user_id, plate, make, model, color)

    def fetch_user_vehicles(self, user_id):
        return fetch_user_vehicles(self.conn, user_id)

    def delete_vehicle(self, vehicle_id, user_id):
        return delete_vehicle(self.conn, vehicle_id, user_id)

    def create_issue(self, user_id, username, location, category, priority, description):
        return create_issue(self.conn, user_id, username, location, category, priority, description)

    def fetch_issues(self, limit=200):
        return fetch_issues(self.conn, limit)

    def fetch_issues_by_user(self, user_id, limit=200):
        return fetch_issues_by_user(self.conn, user_id, limit)

    def update_issue_status(self, issue_id, status):
        return update_issue_status(self.conn, issue_id, status)

    def create_notification(self, title, message, notification_type="general", user_id=None):
        return create_notification(self.conn, title, message, notification_type, user_id)

    def fetch_notifications(self, user_id=None, limit=100):
        return fetch_notifications(self.conn, user_id, limit)

    def fetch_unread_count(self, user_id=None):
        return fetch_unread_count(self.conn, user_id)

    def mark_notification_read(self, notification_id):
        return mark_notification_read(self.conn, notification_id)

    def mark_all_notifications_read(self, user_id=None):
        return mark_all_notifications_read(self.conn, user_id)

    def fetch_latest_notification_id(self, user_id=None):
        return fetch_latest_notification_id(self.conn, user_id)

    def fetch_unread_notifications_after(self, last_seen_id, user_id=None):
        return fetch_unread_notifications_after(self.conn, last_seen_id, user_id)

    def close(self):
        try:
            if self.conn.is_connected():
                self.conn.close()
        except Exception:
            pass