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