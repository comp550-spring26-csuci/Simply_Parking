import mysql.connector
from mysql.connector import Error
from datetime import datetime, timedelta


VALID_ROLES = [
    "ADMIN",
    "SUPPORT_AGENT",
    "PARKING_OFFICER",
    "SEMESTER_USER",
    "DAILY_USER",
    "PAY_AS_YOU_GO"
]

## Admin Role

class AdminService:
    def __init__(self, host, user, password, database):
        self.connection = None
        try:
            self.connection = mysql.connector.connect(
                host=host,
                user=user,
                password=password,
                database=database
            )
            print("Connected to MySQL")
        except Error as e:
            print("Database connection error:", e)

    def create_user(self, current_user_role, username, password, role):
        if current_user_role != "ADMIN":
            return "Access denied"

        if role not in VALID_ROLES:
            return "Invalid role"

        try:
            cursor = self.connection.cursor()

            cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
            if cursor.fetchone():
                cursor.close()
                return "User already exists"

            cursor.execute(
                "INSERT INTO users (username, password, role) VALUES (%s, %s, %s)",
                (username, password, role)
            )
            self.connection.commit()
            cursor.close()

            return "User created successfully"

        except Error as e:
            return f"Error: {e}"

    def update_user_role(self, current_user_role, username, new_role):
        if current_user_role != "ADMIN":
            return "Access denied"

        if new_role not in VALID_ROLES:
            return "Invalid role"

        try:
            cursor = self.connection.cursor()

            cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
            if not cursor.fetchone():
                cursor.close()
                return "User not found"

            cursor.execute(
                "UPDATE users SET role = %s WHERE username = %s",
                (new_role, username)
            )
            self.connection.commit()
            cursor.close()

            return "User role updated"

        except Error as e:
            return f"Error: {e}"

    def view_all_users(self, current_user_role):
        if current_user_role != "ADMIN":
            return "Access denied"

        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT id, username, role FROM users")
            users = cursor.fetchall()
            cursor.close()
            return users

        except Error as e:
            return f"Error: {e}"

 ##  // Support Agent

    def reset_password(self, current_user_role, username, new_password):
        if current_user_role != "SUPPORT_AGENT":
            return "Access denied"

        try:
            cursor = self.connection.cursor()

            cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
            if not cursor.fetchone():
                cursor.close()
                return "User not found"

            cursor.execute(
                "UPDATE users SET password = %s WHERE username = %s",
                (new_password, username)
            )
            self.connection.commit()
            cursor.close()

            return "Password reset successfully"

        except Error as e:
            return f"Error: {e}"

    def update_user_info(self, current_user_role, username, new_username):
        if current_user_role != "SUPPORT_AGENT":
            return "Access denied"

        try:
            cursor = self.connection.cursor()

            cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
            if not cursor.fetchone():
                cursor.close()
                return "User not found"

            cursor.execute(
                "UPDATE users SET username = %s WHERE username = %s",
                (new_username, username)
            )
            self.connection.commit()
            cursor.close()

            return "User info updated"

        except Error as e:
            return f"Error: {e}"

    def view_user(self, current_user_role, username):
        if current_user_role != "SUPPORT_AGENT":
            return "Access denied"

        try:
            cursor = self.connection.cursor()
            cursor.execute(
                "SELECT id, username, role FROM users WHERE username = %s",
                (username,)
            )
            user = cursor.fetchone()
            cursor.close()

            if not user:
                return "User not found"

            return user

        except Error as e:
            return f"Error: {e}"

   ## // Parking Officer

    def monitor_parking_structure(self, current_user_role):
        if current_user_role != "PARKING_OFFICER":
            return "Access denied"

        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT id, license_plate, entry_time, exit_time, status
                FROM parking_sessions
                ORDER BY entry_time DESC
            """)
            sessions = cursor.fetchall()
            cursor.close()
            return sessions

        except Error as e:
            return f"Error: {e}"

    def report_issue(self, current_user_role, issue_text):
        if current_user_role != "PARKING_OFFICER":
            return "Access denied"

        try:
            cursor = self.connection.cursor()
            cursor.execute(
                "INSERT INTO parking_issues (issue_text) VALUES (%s)",
                (issue_text,)
            )
            self.connection.commit()
            cursor.close()
            return "Issue reported successfully"

        except Error as e:
            return f"Error: {e}"

 ## // Semester User

    def register_vehicle(self, current_user_role, username, license_plate):
        if current_user_role not in ["SEMESTER_USER", "DAILY_USER"]:
            return "Access denied"

        try:
            cursor = self.connection.cursor()

            cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
            user = cursor.fetchone()

            if not user:
                cursor.close()
                return "User not found"

            user_id = user[0]

            cursor.execute("SELECT * FROM vehicles WHERE license_plate = %s", (license_plate,))
            if cursor.fetchone():
                cursor.close()
                return "License plate already registered"

            cursor.execute(
                "INSERT INTO vehicles (user_id, license_plate) VALUES (%s, %s)",
                (user_id, license_plate)
            )
            self.connection.commit()
            cursor.close()

            return "Vehicle registered successfully"

        except Error as e:
            return f"Error: {e}"

    def buy_semester_permit(self, current_user_role, username):
        if current_user_role != "SEMESTER_USER":
            return "Access denied"

        try:
            cursor = self.connection.cursor()

            cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
            user = cursor.fetchone()

            if not user:
                cursor.close()
                return "User not found"

            user_id = user[0]
            start_date = datetime.now()
            end_date = start_date + timedelta(days=120)

            cursor.execute("""
                INSERT INTO permits (user_id, permit_type, start_date, end_date, active)
                VALUES (%s, %s, %s, %s, %s)
            """, (user_id, "SEMESTER", start_date, end_date, True))

            self.connection.commit()
            cursor.close()

            return "Semester permit purchased successfully"

        except Error as e:
            return f"Error: {e}"

    def semester_entry(self, current_user_role, license_plate):
        if current_user_role != "SEMESTER_USER":
            return "Access denied"

        try:
            cursor = self.connection.cursor()

            cursor.execute("""
                SELECT p.id
                FROM permits p
                JOIN vehicles v ON p.user_id = v.user_id
                WHERE v.license_plate = %s
                AND p.permit_type = 'SEMESTER'
                AND p.active = TRUE
                AND NOW() BETWEEN p.start_date AND p.end_date
            """, (license_plate,))

            permit = cursor.fetchone()

            if not permit:
                cursor.close()
                return "No valid semester permit"

            cursor.execute("""
                INSERT INTO parking_sessions (license_plate, entry_time, status)
                VALUES (%s, NOW(), %s)
            """, (license_plate, "ACTIVE"))

            self.connection.commit()
            cursor.close()

            return "Semester user entered parking structure"

        except Error as e:
            return f"Error: {e}"

 ## // Daily User

    def buy_daily_permit(self, current_user_role, username):
        if current_user_role != "DAILY_USER":
            return "Access denied"

        try:
            cursor = self.connection.cursor()

            cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
            user = cursor.fetchone()

            if not user:
                cursor.close()
                return "User not found"

            user_id = user[0]
            start_date = datetime.now()
            end_date = start_date + timedelta(days=1)

            cursor.execute("""
                INSERT INTO permits (user_id, permit_type, start_date, end_date, active)
                VALUES (%s, %s, %s, %s, %s)
            """, (user_id, "DAILY", start_date, end_date, True))

            self.connection.commit()
            cursor.close()

            return "Daily permit purchased successfully"

        except Error as e:
            return f"Error: {e}"

    def daily_entry(self, current_user_role, license_plate):
        if current_user_role != "DAILY_USER":
            return "Access denied"

        try:
            cursor = self.connection.cursor()

            cursor.execute("""
                SELECT p.id
                FROM permits p
                JOIN vehicles v ON p.user_id = v.user_id
                WHERE v.license_plate = %s
                AND p.permit_type = 'DAILY'
                AND p.active = TRUE
                AND NOW() BETWEEN p.start_date AND p.end_date
            """, (license_plate,))

            permit = cursor.fetchone()

            if not permit:
                cursor.close()
                return "No valid daily permit"

            cursor.execute("""
                INSERT INTO parking_sessions (license_plate, entry_time, status)
                VALUES (%s, NOW(), %s)
            """, (license_plate, "ACTIVE"))

            self.connection.commit()
            cursor.close()

            return "Daily user entered parking structure"

        except Error as e:
            return f"Error: {e}"

   ## // Pay As YOU Go

    def pay_as_you_go_entry(self, current_user_role, license_plate):
        if current_user_role != "PAY_AS_YOU_GO":
            return "Access denied"

        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                INSERT INTO parking_sessions (license_plate, entry_time, status)
                VALUES (%s, NOW(), %s)
            """, (license_plate, "ACTIVE"))
            self.connection.commit()
            cursor.close()

            return "Pay-as-you-go user entered parking structure"

        except Error as e:
            return f"Error: {e}"

    def pay_as_you_go_exit(self, current_user_role, license_plate):
        if current_user_role != "PAY_AS_YOU_GO":
            return "Access denied"

        try:
            cursor = self.connection.cursor()

            cursor.execute("""
                SELECT id, entry_time
                FROM parking_sessions
                WHERE license_plate = %s AND status = 'ACTIVE'
                ORDER BY entry_time DESC
                LIMIT 1
            """, (license_plate,))

            session = cursor.fetchone()

            if not session:
                cursor.close()
                return "No active parking session found"

            session_id = session[0]
            entry_time = session[1]
            exit_time = datetime.now()

            duration = exit_time - entry_time
            hours = max(1, int(duration.total_seconds() / 3600))
            fee = hours * 5

            cursor.execute("""
                UPDATE parking_sessions
                SET exit_time = %s, fee = %s, status = %s
                WHERE id = %s
            """, (exit_time, fee, "CLOSED", session_id))

            self.connection.commit()
            cursor.close()

            return f"Exit processed. Parking fee: ${fee}"

        except Error as e:
            return f"Error: {e}"

  
    def close_connection(self):
        if self.connection and self.connection.is_connected():
            self.connection.close()
            print("Connection closed")
