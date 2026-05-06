import tkinter as tk
from tkinter import messagebox

from notifier import Notifier
from screens.notifications_screen import build_notifications_screen

from database_manager import DatabaseManager
from utils.constants import ROLE_LABELS

from screens.login_screen import build_login_screen
from screens.dashboard_screen import build_dashboard_screen
from screens.plate_records_screen import build_plate_records_screen
from screens.add_plate_screen import build_add_plate_screen
from screens.users_screen import build_manage_users_screen, build_manage_users_readonly_screen
from screens.reset_password_screen import build_reset_password_screen
from screens.logs_screen import build_logs_screen
from screens.report_issue_screen import build_report_issue_screen
from screens.manage_issues_screen import build_manage_issues_screen
from screens.vehicles_screen import build_my_vehicle_screen, build_register_vehicle_screen
from screens.daily_permit_screen import build_buy_daily_permit_screen, build_my_daily_permit_screen
from screens.payg_screen import build_current_session_screen, build_pay_exit_screen


class PlateApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Parking System")
        self.root.geometry("1000x600")

        try:
            self.db = DatabaseManager()
        except Exception as e:
            messagebox.showerror("Database Error", str(e))
            self.root.after(100, self.root.destroy)
            return

        self.current_user = None
        self.preview_image_ref = None

        self.main_frame = tk.Frame(self.root)
        self.main_frame.pack(fill="both", expand=True)

        self.content_frame = None

        # notifications
        self.notifier = Notifier("Parking System")
        self.notifications_button = None
        self.last_seen_notification_id = 0
        self.notification_poll_job = None

        self.show_login()

    def clear_main(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy()

    def clear_content(self):
        if self.content_frame:
            for widget in self.content_frame.winfo_children():
                widget.destroy()

    def login(self, username, password):
        user = self.db.authenticate_user(username, password)
        if not user:
            self.db.add_log(
                event_type="login_failed",
                details="Incorrect username or password",
                username=username,
            )
            messagebox.showerror("Login Failed", "Invalid username or password")
            return

        self.current_user = user
        self.db.add_log(
            event_type="login_success",
            details=f"Role={user['role']}",
            user_id=user["id"],
            username=user["username"],
        )

        self.show_dashboard()
        self.refresh_notification_badge()
        self.start_notification_polling()

    def logout(self):
        if self.current_user:
            self.db.add_log(
                event_type="logout",
                details=f"Role={self.current_user['role']}",
                user_id=self.current_user["id"],
                username=self.current_user["username"],
            )

        self.stop_notification_polling()

        self.current_user = None
        self.notifications_button = None
        self.last_seen_notification_id = 0

        self.show_login()

    def show_login(self):
        self.clear_main()
        build_login_screen(self)

    def show_dashboard(self):
        self.clear_main()
        build_dashboard_screen(self)

    def show_plate_records(self):
        self.clear_content()
        build_plate_records_screen(self)

    def show_add_plate(self):
        self.clear_content()
        build_add_plate_screen(self)

    def show_manage_users(self):
        self.clear_content()
        build_manage_users_screen(self)

    def show_manage_users_readonly(self):
        self.clear_content()
        build_manage_users_readonly_screen(self)

    def show_reset_password(self):
        self.clear_content()
        build_reset_password_screen(self)

    def show_logs_reports(self):
        self.clear_content()
        build_logs_screen(self)

    def show_report_issue(self):
        self.clear_content()
        build_report_issue_screen(self)

    def show_manage_issues(self):
        self.clear_content()
        build_manage_issues_screen(self)

    def show_my_vehicle(self):
        self.clear_content()
        build_my_vehicle_screen(self)

    def show_register_vehicle(self):
        self.clear_content()
        build_register_vehicle_screen(self)

    def show_buy_daily_permit(self):
        self.clear_content()
        build_buy_daily_permit_screen(self)

    def show_my_daily_permit(self):
        self.clear_content()
        build_my_daily_permit_screen(self)

    def show_current_session(self):
        self.clear_content()
        build_current_session_screen(self)

    def show_pay_exit(self):
        self.clear_content()
        build_pay_exit_screen(self)

    def show_notifications(self):
        self.clear_content()
        build_notifications_screen(self)

    def refresh_notification_badge(self):
        if not self.current_user:
            return

        try:
            unread = self.db.fetch_unread_count(user_id=self.current_user["id"])
        except Exception as e:
            print(f"Unread badge refresh failed: {e}")
            unread = 0

        if self.notifications_button:
            if unread > 0:
                self.notifications_button.config(text=f"Notifications ({unread})")
            else:
                self.notifications_button.config(text="Notifications")

    def start_notification_polling(self):
        if not self.current_user:
            return

        try:
            self.last_seen_notification_id = self.db.fetch_latest_notification_id(
                user_id=self.current_user["id"]
            )
        except Exception as e:
            print(f"Failed to initialize notification polling: {e}")
            self.last_seen_notification_id = 0

        self.stop_notification_polling()
        self.poll_notifications()
    
    def stop_notification_polling(self):
        if self.notification_poll_job is not None:
            try:
                self.root.after_cancel(self.notification_poll_job)
            except Exception:
                pass
            self.notification_poll_job = None
    
    def poll_notifications(self):
        if not self.current_user:
            return

        try:
            rows = self.db.fetch_unread_notifications_after(
                self.last_seen_notification_id,
                user_id=self.current_user["id"],
            )

            for row in rows:
                notification_id, _user_id, title, message, notification_type, is_read, created_at = row

                self.notifier.alert(
                    title=title,
                    message=message,
                    popup=True,
                    desktop=False,
                )

                if notification_id > self.last_seen_notification_id:
                    self.last_seen_notification_id = notification_id

            self.refresh_notification_badge()

        except Exception as e:
            print(f"Notification polling error: {e}")

        self.notification_poll_job = self.root.after(4000, self.poll_notifications)

    def on_close(self):
        self.stop_notification_polling()
        self.db.close()
        self.root.destroy()

if __name__ == "__main__":
    print("Starting GUI...")
    root = tk.Tk()
    root.lift()
    root.attributes("-topmost", True)
    root.after(200, lambda: root.attributes("-topmost", False))
    app = PlateApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()