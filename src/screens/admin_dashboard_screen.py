import tkinter as tk
from tkinter import messagebox

def build_admin_dashboard_screen(app):
    app.clear_content()
    tk.Label(app.content_frame, text="Admin Dashboard", font=("Arial",16,"bold")).pack(pady=(20,6))

    sf = tk.Frame(app.content_frame, padx=20); sf.pack(fill="x")

    def card(row, col, title, value, colour="#1a7a1a"):
        c = tk.Frame(sf, bd=1, relief="solid", padx=16, pady=14)
        c.grid(row=row, column=col, padx=8, pady=8, sticky="nsew")
        tk.Label(c, text=title, font=("Arial",10), fg="#555").pack()
        tk.Label(c, text=value, font=("Arial",22,"bold"), fg=colour).pack()

    try:
        active    = app.db.count_active_sessions()
        issues    = app.db.count_open_issues()
        users     = app.db.count_users()
        sem_count = app.db.count_active_semester_permits()
        today_dp  = app.db.count_today_daily_permits()
        daily_rev, payg_rev, sem_rev = app.db.fetch_today_revenue()
        total_rev = daily_rev + payg_rev + sem_rev
    except Exception as e:
        messagebox.showerror("Stats Error", str(e))
        active=issues=users=sem_count=today_dp=0; daily_rev=payg_rev=sem_rev=total_rev=0.0

    card(0,0,"Active Sessions Now",  str(active),    "#1565c0")
    card(0,1,"Open Issues",          str(issues),    "#b71c1c")
    card(0,2,"Registered Users",     str(users),     "#4a148c")
    card(0,3,"Today's Revenue",      f"${total_rev:.2f}", "#1a7a1a")
    card(1,0,"Active Sem. Permits",  str(sem_count), "#006064")
    card(1,1,"Daily Permits Today",  str(today_dp),  "#e65100")

    rev = tk.Frame(app.content_frame, padx=20, pady=10); rev.pack(fill="x")
    tk.Label(rev, text="Today's Revenue Breakdown", font=("Arial",12,"bold")).pack(anchor="w")
    tk.Label(rev, text=(
        f"  Daily Permits   : ${daily_rev:.2f}\n"
        f"  Pay-As-You-Go   : ${payg_rev:.2f}\n"
        f"  Semester Permits: ${sem_rev:.2f}\n"
        f"  ─────────────────────\n"
        f"  Total            : ${total_rev:.2f}"),
        font=("Arial",11), justify="left").pack(anchor="w", pady=6)

    tk.Button(app.content_frame, text="🔄 Refresh", command=app.show_admin_dashboard).pack(pady=10)
