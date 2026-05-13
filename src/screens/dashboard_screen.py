import tkinter as tk
from utils.constants import ROLE_LABELS

def _btn(parent, text, cmd):
    b=tk.Button(parent, text=text, command=cmd); b.pack(pady=5, padx=20, fill="x"); return b

def _home(app):
    for w in app.content_frame.winfo_children(): w.destroy()
    tk.Label(app.content_frame, text="SimplyPark Dashboard",
             font=("Arial",18,"bold")).pack(pady=20)
    role = ROLE_LABELS.get(app.current_user["role"], app.current_user["role"])
    tk.Label(app.content_frame, text=f"Logged in as: {app.current_user.get('full_name') or app.current_user['username']}",
             font=("Arial",12)).pack()
    tk.Label(app.content_frame, text=f"Role: {role}", font=("Arial",11), fg="#555").pack(pady=4)

def build_dashboard_screen(app):
    app.notifications_button = None
    top=tk.Frame(app.main_frame, padx=10, pady=10); top.pack(fill="x")
    role_name = ROLE_LABELS.get(app.current_user["role"], app.current_user["role"])
    tk.Label(top, text=f"Welcome, {app.current_user.get('full_name') or app.current_user['username']} ({role_name})",
             font=("Arial",14,"bold")).pack(side="left")
    tk.Button(top, text="Logout", command=app.logout).pack(side="right")

    body=tk.Frame(app.main_frame, padx=10, pady=10); body.pack(fill="both", expand=True)
    nav=tk.Frame(body, width=220, bd=1, relief="solid"); nav.pack(side="left", fill="y", padx=(0,10))
    content=tk.Frame(body, bd=1, relief="solid"); content.pack(side="right", fill="both", expand=True)
    app.content_frame = content
    role = app.current_user["role"]

    if role == "admin":
        _btn(nav,"Admin Dashboard",   app.show_admin_dashboard)
        _btn(nav,"Active Sessions",    app.show_active_sessions)
        _btn(nav,"All Permits",        app.show_all_permits)
        _btn(nav,"Access Check",       app.show_access_check)
        _btn(nav,"Plate Records",      app.show_plate_records)
        _btn(nav,"Add Plate",          app.show_add_plate)
        _btn(nav,"Manage Users",       app.show_manage_users)
        _btn(nav,"Manage Issues",      app.show_manage_issues)
        _btn(nav,"Logs & Reports",     app.show_logs_reports)
        _btn(nav,"Report Issue",       app.show_report_issue)
        app.notifications_button = _btn(nav,"Notifications", app.show_notifications)

    elif role == "support_agent":
        _btn(nav,"Active Sessions",    app.show_active_sessions)
        _btn(nav,"All Permits",        app.show_all_permits)
        _btn(nav,"Customer History",   app.show_plate_records)
        _btn(nav,"Manage Accounts",    app.show_manage_users_readonly)
        _btn(nav,"Manage Issues",      app.show_manage_issues)
        _btn(nav,"Reset Password",     app.show_reset_password)
        _btn(nav,"Logs",               app.show_logs_reports)
        _btn(nav,"Report Issue",       app.show_report_issue)
        app.notifications_button = _btn(nav,"Notifications", app.show_notifications)

    elif role == "parking_officer":
        _btn(nav,"Access Check",       app.show_access_check)
        _btn(nav,"Active Sessions",    app.show_active_sessions)
        _btn(nav,"Report Issue",       app.show_report_issue)
        app.notifications_button = _btn(nav,"Notifications", app.show_notifications)

    elif role in ("user", "daily_user"):
        _btn(nav,"My Vehicle",         app.show_my_vehicle)
        _btn(nav,"Register Vehicle",   app.show_register_vehicle)
        _btn(nav,"Buy Daily Permit",   app.show_buy_daily_permit)
        _btn(nav,"My Daily Permit",    app.show_my_daily_permit)
        _btn(nav,"Semester Permit",    app.show_semester_permit)
        _btn(nav,"Current Session",    app.show_current_session)
        _btn(nav,"Pay On Exit",        app.show_pay_exit)
        _btn(nav,"Payment History",    app.show_payment_history)
        _btn(nav,"Report Issue",       app.show_report_issue)
        app.notifications_button = _btn(nav,"Notifications", app.show_notifications)

    elif role == "guest":
        _btn(nav,"Check Parking Time", app.show_guest_session_lookup)
        _btn(nav,"Pay On Exit",        app.show_pay_exit)

    _home(app)
