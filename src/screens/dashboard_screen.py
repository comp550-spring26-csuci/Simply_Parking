import tkinter as tk
from utils.constants import ROLE_LABELS

BG = "#F7F7F7"
CARD_BG = "#FFFFFF"
PRIMARY = "#C8102E"
PRIMARY_DARK = "#A00D25"
TEXT = "#1F1F1F"
MUTED = "#6B7280"
BORDER = "#D9D9D9"


def add_nav_button(parent, text, command):
    btn = tk.Label(
        parent,
        text=text,
        bg="white",
        fg=PRIMARY,
        font=("Arial", 12, "bold"),
        padx=14,
        pady=10,
        cursor="hand2",
        relief="solid",
        bd=1,
    )
    btn.pack(pady=6, padx=18, fill="x")
    btn.bind("<Button-1>", lambda e: command())
    btn.bind("<Enter>", lambda e: btn.config(bg="#FDECEF"))
    btn.bind("<Leave>", lambda e: btn.config(bg="white"))
    return btn


def show_home(app):
    for widget in app.content_frame.winfo_children():
        widget.destroy()

    tk.Label(
        app.content_frame,
        text="Dashboard",
        font=("Arial", 24, "bold"),
        bg=CARD_BG,
        fg=PRIMARY,
    ).pack(pady=(35, 12))

    tk.Label(
        app.content_frame,
        text=f"Role: {ROLE_LABELS.get(app.current_user['role'], app.current_user['role'])}",
        font=("Arial", 14),
        bg=CARD_BG,
        fg=TEXT,
    ).pack()


def build_dashboard_screen(app):
    app.notifications_button = None
    app.main_frame.configure(bg=BG)

    top = tk.Frame(app.main_frame, bg=PRIMARY, padx=14, pady=14)
    top.pack(fill="x")

    role_name = ROLE_LABELS.get(app.current_user["role"], app.current_user["role"])

    tk.Label(
        top,
        text=f"Welcome, {app.current_user.get('full_name') or app.current_user['username']} ({role_name})",
        font=("Arial", 14, "bold"),
        bg=PRIMARY,
        fg="white",
    ).pack(side="left")

    logout_btn = tk.Label(
        top,
        text="Logout",
        bg="white",
        fg=PRIMARY,
        font=("Arial", 12, "bold"),
        padx=20,
        pady=6,
        cursor="hand2",
    )
    logout_btn.pack(side="right")
    logout_btn.bind("<Button-1>", lambda e: app.logout())
    logout_btn.bind("<Enter>", lambda e: logout_btn.config(bg="#FDECEF"))
    logout_btn.bind("<Leave>", lambda e: logout_btn.config(bg="white"))

    body = tk.Frame(app.main_frame, bg=BG, padx=14, pady=14)
    body.pack(fill="both", expand=True)

    nav = tk.Frame(
        body,
        width=230,
        bg=CARD_BG,
        highlightbackground=BORDER,
        highlightthickness=1,
    )
    nav.pack(side="left", fill="y", padx=(0, 14))

    content = tk.Frame(
        body,
        bg=CARD_BG,
        highlightbackground=BORDER,
        highlightthickness=1,
    )
    content.pack(side="right", fill="both", expand=True)

    app.content_frame = content

    role = app.current_user["role"]

    if role == "admin":
        add_nav_button(nav, "Admin Dashboard", app.show_admin_dashboard)
        add_nav_button(nav, "Active Sessions", app.show_active_sessions)
        add_nav_button(nav, "Plate Records", app.show_plate_records)
        add_nav_button(nav, "Add Plate", app.show_add_plate)
        add_nav_button(nav, "Manage Users", app.show_manage_users)
        add_nav_button(nav, "Manage Issues", app.show_manage_issues)
        add_nav_button(nav, "Logs & Reports", app.show_logs_reports)
        add_nav_button(nav, "Report Issue", app.show_report_issue)
        app.notifications_button = add_nav_button(nav, "Notifications", app.show_notifications)

    elif role == "support_agent":
        add_nav_button(nav, "Active Sessions", app.show_active_sessions)
        add_nav_button(nav, "Customer History", app.show_plate_records)
        add_nav_button(nav, "Add Plate", app.show_add_plate)
        add_nav_button(nav, "Manage Accounts", app.show_manage_users_readonly)
        add_nav_button(nav, "Manage Issues", app.show_manage_issues)
        add_nav_button(nav, "Reset Password", app.show_reset_password)
        add_nav_button(nav, "Logs", app.show_logs_reports)
        add_nav_button(nav, "Report Issue", app.show_report_issue)
        app.notifications_button = add_nav_button(nav, "Notifications", app.show_notifications)

    elif role == "user":
        add_nav_button(nav, "My Vehicle", app.show_my_vehicle)
        add_nav_button(nav, "Register Vehicle", app.show_register_vehicle)
        add_nav_button(nav, "Buy Daily Permit", app.show_buy_daily_permit)
        add_nav_button(nav, "My Daily Permit", app.show_my_daily_permit)
        add_nav_button(nav, "Current Session", app.show_current_session)
        add_nav_button(nav, "Payment History", app.show_payment_history)
        add_nav_button(nav, "Pay On Exit", app.show_pay_exit)
        add_nav_button(nav, "Report Issue", app.show_report_issue)
        app.notifications_button = add_nav_button(nav, "Notifications", app.show_notifications)

    elif role == "guest":
        add_nav_button(nav, "Check Parking Time", app.show_guest_session_lookup)
        add_nav_button(nav, "Pay On Exit", app.show_pay_exit)

    show_home(app)