import tkinter as tk
from utils.constants import ROLE_LABELS

def add_nav_button(parent, text, command):
    btn = tk.Button(parent, text=text, command=command)
    btn.pack(pady=5, padx=20, fill="x")
    return btn

def show_home(app):
    for widget in app.content_frame.winfo_children():
        widget.destroy()

    tk.Label(
        app.content_frame,
        text="Dashboard",
        font=("Arial", 18, "bold")
    ).pack(pady=20)

    tk.Label(
        app.content_frame,
        text=f"Role: {ROLE_LABELS.get(app.current_user['role'], app.current_user['role'])}"
    ).pack()

def build_dashboard_screen(app):
    app.notifications_button = None

    top = tk.Frame(app.main_frame, padx=10, pady=10)
    top.pack(fill="x")

    role_name = ROLE_LABELS.get(app.current_user["role"], app.current_user["role"])

    tk.Label(
        top,
        text=f"Welcome, {app.current_user.get('full_name') or app.current_user['username']} ({role_name})",
        font=("Arial", 14, "bold")
    ).pack(side="left")

    tk.Button(top, text="Logout", command=app.logout).pack(side="right")

    body = tk.Frame(app.main_frame, padx=10, pady=10)
    body.pack(fill="both", expand=True)

    nav = tk.Frame(body, width=220, bd=1, relief="solid")
    nav.pack(side="left", fill="y", padx=(0, 10))

    content = tk.Frame(body, bd=1, relief="solid")
    content.pack(side="right", fill="both", expand=True)

    app.content_frame = content

    role = app.current_user["role"]

    if role == "admin":
        add_nav_button(nav, "Plate Records", app.show_plate_records)
        add_nav_button(nav, "Add Plate", app.show_add_plate)
        add_nav_button(nav, "Manage Users", app.show_manage_users)
        add_nav_button(nav, "Manage Issues", app.show_manage_issues)
        add_nav_button(nav, "Logs & Reports", app.show_logs_reports)
        app.notifications_button = add_nav_button(nav, "Notifications", app.show_notifications)
        add_nav_button(nav, "Report Issue", app.show_report_issue)

    elif role == "support_agent":
        add_nav_button(nav, "Customer History", app.show_plate_records)
        add_nav_button(nav, "Add Plate", app.show_add_plate)
        add_nav_button(nav, "Manage Accounts", app.show_manage_users_readonly)
        add_nav_button(nav, "Manage Issues", app.show_manage_issues)
        add_nav_button(nav, "Reset Password", app.show_reset_password)
        add_nav_button(nav, "Logs", app.show_logs_reports)
        app.notifications_button = add_nav_button(nav, "Notifications", app.show_notifications)
        add_nav_button(nav, "Report Issue", app.show_report_issue)

    elif role == "parking_officer":
        add_nav_button(nav, "Monitor Parking", app.show_plate_records)
        

    elif role == "semester_user":
        add_nav_button(nav, "My Vehicle", app.show_my_vehicle)
        add_nav_button(nav, "Register Vehicle", app.show_register_vehicle)
        add_nav_button(nav, "Report Issue", app.show_report_issue)

    elif role == "daily_user":
        add_nav_button(nav, "Buy Daily Permit", app.show_buy_daily_permit)
        add_nav_button(nav, "My Daily Permit", app.show_my_daily_permit)
        add_nav_button(nav, "Report Issue", app.show_report_issue)

    elif role == "payg_user":
        add_nav_button(nav, "Current Session", app.show_current_session)
        add_nav_button(nav, "Pay On Exit", app.show_pay_exit)
        add_nav_button(nav, "Report Issue", app.show_report_issue)

    show_home(app)