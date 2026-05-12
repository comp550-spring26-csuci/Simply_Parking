# database_manager.py — facade with Stripe-safe payment helpers
from db.connection import create_connection
from db.schema import init_schema
from db.users import (seed_default_admin, create_user, authenticate_user,
    fetch_users, reset_password, delete_user, count_users)
from db.plates import (insert_plate, fetch_all, fetch_latest_plate_session,
    update_plate_entry, delete_plate_entry)
from db.logs import add_log, fetch_logs
from db.vehicles import (register_vehicle, fetch_user_vehicles, delete_vehicle,
    user_owns_vehicle, vehicle_has_active_permit)
from db.issues import (create_issue, fetch_issues, fetch_issues_by_user,
    update_issue_status, count_open_issues)
from db.notifications import (create_notification, fetch_notifications,
    fetch_unread_count, mark_notification_read, mark_all_notifications_read,
    fetch_latest_notification_id, fetch_unread_notifications_after)
from db.daily_permits import (create_daily_permit, fetch_daily_permits_for_user,
    fetch_today_daily_permits_for_user, fetch_all_daily_permits,
    count_today_daily_permits, has_daily_permit_today, daily_payment_exists)
from db.parking_sessions import (create_session_if_not_active,
    fetch_active_session_by_plate, fetch_active_sessions, count_active_sessions,
    close_session, check_plate_access)
from db.semester_permits import (create_semester_permit,
    fetch_semester_permits_for_user, fetch_active_semester_permits_for_user,
    fetch_all_semester_permits, count_active_semester_permits,
    has_active_semester_permit_for_plate, semester_payment_exists)
from db.payg_payments import (create_payg_payment, fetch_payg_payments_for_user,
    payg_payment_exists)


class DatabaseManager:
    def __init__(self):
        print("Connecting...")
        self.conn = create_connection()
        print("Initializing schema...")
        init_schema(self.conn)
        print("Seeding admin...")
        seed_default_admin(self.conn)
        print("Database ready.")

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()
        return False

    # users
    def create_user(self, username, password, role, full_name=""):
        return create_user(self.conn, username, password, role, full_name)
    def authenticate_user(self, username, password):
        return authenticate_user(self.conn, username, password)
    def fetch_users(self):
        return fetch_users(self.conn)
    def count_users(self):
        return count_users(self.conn)
    def delete_user(self, user_id):
        return delete_user(self.conn, user_id)
    def reset_password(self, user_id, new_password):
        return reset_password(self.conn, user_id, new_password)

    # plates
    def insert_plate(self, plate, source_file, actor_user_id=None, actor_username=None):
        return insert_plate(self.conn, plate, source_file, actor_user_id, actor_username)
    def fetch_all(self, limit=None):
        return fetch_all(self.conn, limit)
    def fetch_latest_plate_session(self, plate):
        return fetch_latest_plate_session(self.conn, plate)
    def update_plate_entry(self, record_id, plate, source_file="", actor_user_id=None, actor_username=None):
        return update_plate_entry(self.conn, record_id, plate, source_file, actor_user_id, actor_username)
    def delete_plate_entry(self, record_id, actor_user_id=None, actor_username=None):
        return delete_plate_entry(self.conn, record_id, actor_user_id, actor_username)

    # logs
    def add_log(self, event_type, details="", user_id=None, username=None):
        return add_log(self.conn, event_type, details, user_id, username)
    def fetch_logs(self, limit=75):
        return fetch_logs(self.conn, limit)

    # vehicles
    def register_vehicle(self, user_id, plate, make="", model="", color=""):
        return register_vehicle(self.conn, user_id, plate, make, model, color)
    def fetch_user_vehicles(self, user_id):
        return fetch_user_vehicles(self.conn, user_id)
    def user_owns_vehicle(self, user_id, plate):
        return user_owns_vehicle(self.conn, user_id, plate)
    def vehicle_has_active_permit(self, user_id, plate):
        return vehicle_has_active_permit(self.conn, user_id, plate)
    def delete_vehicle(self, vehicle_id, user_id):
        return delete_vehicle(self.conn, vehicle_id, user_id)

    # issues
    def create_issue(self, user_id, username, location, category, priority, description):
        return create_issue(self.conn, user_id, username, location, category, priority, description)
    def fetch_issues(self, limit=75):
        return fetch_issues(self.conn, limit)
    def fetch_issues_by_user(self, user_id, limit=75):
        return fetch_issues_by_user(self.conn, user_id, limit)
    def update_issue_status(self, issue_id, status):
        return update_issue_status(self.conn, issue_id, status)
    def count_open_issues(self):
        return count_open_issues(self.conn)

    # notifications
    def create_notification(self, title, message, notification_type="general", user_id=None):
        return create_notification(self.conn, title, message, notification_type, user_id)
    def fetch_notifications(self, user_id=None, limit=75):
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

    # daily permits
    def create_daily_permit(self, user_id, plate, permit_date=None, amount=6.00,
                            stripe_session_id=None, stripe_payment_intent_id=None):
        return create_daily_permit(self.conn, user_id, plate, permit_date, amount,
                                   stripe_session_id, stripe_payment_intent_id)
    def daily_payment_exists(self, stripe_payment_intent_id):
        return daily_payment_exists(self.conn, stripe_payment_intent_id)
    def has_daily_permit_today(self, user_id, plate):
        return has_daily_permit_today(self.conn, user_id, plate)
    def fetch_daily_permits_for_user(self, user_id, limit=75):
        return fetch_daily_permits_for_user(self.conn, user_id, limit)
    def fetch_today_daily_permits_for_user(self, user_id):
        return fetch_today_daily_permits_for_user(self.conn, user_id)
    def fetch_all_daily_permits(self, limit=100):
        return fetch_all_daily_permits(self.conn, limit)
    def count_today_daily_permits(self):
        return count_today_daily_permits(self.conn)

    # parking sessions
    def create_session_if_not_active(self, plate):
        return create_session_if_not_active(self.conn, plate)
    def fetch_active_session_by_plate(self, plate):
        return fetch_active_session_by_plate(self.conn, plate)
    def fetch_active_sessions(self):
        return fetch_active_sessions(self.conn)
    def count_active_sessions(self):
        return count_active_sessions(self.conn)
    def close_session(self, session_id, amount_due):
        return close_session(self.conn, session_id, amount_due)
    def check_plate_access(self, plate):
        return check_plate_access(self.conn, plate)

    # semester permits
    def create_semester_permit(self, user_id, plate, start_date, end_date, amount=0.00,
                               stripe_session_id=None, stripe_payment_intent_id=None):
        return create_semester_permit(self.conn, user_id, plate, start_date, end_date,
                                      amount, stripe_session_id, stripe_payment_intent_id)
    def semester_payment_exists(self, stripe_payment_intent_id):
        return semester_payment_exists(self.conn, stripe_payment_intent_id)
    def has_active_semester_permit_for_plate(self, user_id, plate):
        return has_active_semester_permit_for_plate(self.conn, user_id, plate)
    def fetch_semester_permits_for_user(self, user_id):
        return fetch_semester_permits_for_user(self.conn, user_id)
    def fetch_active_semester_permits_for_user(self, user_id):
        return fetch_active_semester_permits_for_user(self.conn, user_id)
    def fetch_all_semester_permits(self, limit=100):
        return fetch_all_semester_permits(self.conn, limit)
    def count_active_semester_permits(self):
        return count_active_semester_permits(self.conn)

    # PAYG
    def create_payg_payment(self, user_id, plate, duration_minutes, amount,
                            parking_session_id=None, stripe_session_id=None,
                            stripe_payment_intent_id=None):
        return create_payg_payment(self.conn, user_id, plate, duration_minutes, amount,
                                   parking_session_id, stripe_session_id,
                                   stripe_payment_intent_id)
    def payg_payment_exists(self, stripe_payment_intent_id):
        return payg_payment_exists(self.conn, stripe_payment_intent_id)
    def fetch_payg_payments_for_user(self, user_id, limit=75):
        return fetch_payg_payments_for_user(self.conn, user_id, limit)

    # combined payment history
    def fetch_payment_history(self, user_id, limit=75):
        cur = self.conn.cursor()
        try:
            cur.execute("""
                (SELECT id, plate, 'Daily Permit' AS payment_type, amount, created_at
                 FROM daily_permits WHERE user_id=%s)
                UNION ALL
                (SELECT id, plate, 'Semester Permit', amount, created_at
                 FROM semester_permits WHERE user_id=%s)
                UNION ALL
                (SELECT id, plate, 'Pay-As-You-Go', amount, created_at
                 FROM payg_payments WHERE user_id=%s)
                ORDER BY created_at DESC LIMIT %s""",
                (user_id, user_id, user_id, limit))
            return cur.fetchall()
        finally:
            cur.close()

    # admin stats
    def fetch_today_revenue(self):
        cur = self.conn.cursor()
        try:
            cur.execute("SELECT COALESCE(SUM(amount),0) FROM daily_permits WHERE DATE(created_at)=CURDATE()")
            daily = float(cur.fetchone()[0])
            cur.execute("SELECT COALESCE(SUM(amount),0) FROM payg_payments WHERE DATE(created_at)=CURDATE()")
            payg = float(cur.fetchone()[0])
            cur.execute("SELECT COALESCE(SUM(amount),0) FROM semester_permits WHERE DATE(created_at)=CURDATE()")
            sem = float(cur.fetchone()[0])
            return daily, payg, sem
        finally:
            cur.close()

    def close(self):
        try:
            if self.conn.is_connected():
                self.conn.close()
        except Exception:
            pass
