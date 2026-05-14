"""User's personal permits — show both daily and semester permits."""
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date


def build_my_permits_screen(app):
    app.clear_content()
    f = tk.Frame(app.content_frame, padx=20, pady=20)
    f.pack(anchor="nw", fill="both", expand=True)

    tk.Label(f, text="My Parking Permits",
             font=("Arial", 16, "bold")).pack(pady=10)

    # Create a tabbed interface
    nb = ttk.Notebook(f)
    nb.pack(fill="both", expand=True, pady=10)

    # ── Tab 1: Daily Permits ─────────────────────────────────────────────────
    daily_tab = tk.Frame(nb)
    nb.add(daily_tab, text="Daily Permits")

    daily_content = tk.Frame(daily_tab, padx=10, pady=10)
    daily_content.pack(fill="both", expand=True)

    def load_daily():
        for widget in daily_content.winfo_children():
            widget.destroy()

        try:
            rows = app.db.fetch_today_daily_permits_for_user(app.current_user["id"])
            if not rows:
                tk.Label(daily_content, text="No active daily permits for today.",
                         fg="#666", font=("Arial", 11)).pack(pady=20)
                tk.Button(daily_content, text="Buy Daily Permit",
                          command=app.show_buy_permit_choice).pack(pady=5)
                return

            for pid, plate, pdate, amount, created in rows:
                card = tk.Frame(daily_content, bd=1, relief="solid", padx=12, pady=10, bg="#e8f5e9")
                card.pack(anchor="w", fill="x", pady=6)
                tk.Label(card, text="✓ ACTIVE", font=("Arial", 10, "bold"), 
                         fg="#1a7a1a", bg="#e8f5e9").pack(anchor="w")
                tk.Label(card, text=(
                    f"Permit ID  : {pid}\n"
                    f"Plate      : {plate}\n"
                    f"Valid Date : {pdate}\n"
                    f"Amount     : ${float(amount):.2f}\n"
                    f"Purchased  : {str(created)[:16]}"),
                    justify="left", font=("Arial", 10), bg="#e8f5e9").pack(anchor="w", pady=4)

        except Exception as e:
            tk.Label(daily_content, text=f"Error loading daily permits: {e}",
                     fg="red").pack(pady=10)

    # ── Tab 2: Semester Permits ──────────────────────────────────────────────
    semester_tab = tk.Frame(nb)
    nb.add(semester_tab, text="Semester Permits")

    semester_content = tk.Frame(semester_tab, padx=10, pady=10)
    semester_content.pack(fill="both", expand=True)

    def load_semester():
        for widget in semester_content.winfo_children():
            widget.destroy()

        try:
            rows = app.db.fetch_active_semester_permits_for_user(app.current_user["id"])
            if not rows:
                tk.Label(semester_content, text="No active semester permits.",
                         fg="#666", font=("Arial", 11)).pack(pady=20)
                tk.Button(semester_content, text="Buy Semester Permit",
                          command=app.show_buy_permit_choice).pack(pady=5)
                return

            for pid, plate, start, end, amount, created in rows:
                days_left = (date.fromisoformat(str(end)) - date.today()).days
                card = tk.Frame(semester_content, bd=1, relief="solid", padx=12, pady=10, bg="#e8f5e9")
                card.pack(anchor="w", fill="x", pady=6)
                tk.Label(card, text="✓ ACTIVE", font=("Arial", 10, "bold"),
                         fg="#1a7a1a", bg="#e8f5e9").pack(anchor="w")
                tk.Label(card, text=(
                    f"Permit ID  : {pid}\n"
                    f"Plate      : {plate}\n"
                    f"Valid From : {start} to {end}\n"
                    f"Days Left  : {days_left}\n"
                    f"Amount     : ${float(amount):.2f}\n"
                    f"Purchased  : {str(created)[:16]}"),
                    justify="left", font=("Arial", 10), bg="#e8f5e9").pack(anchor="w", pady=4)

        except Exception as e:
            tk.Label(semester_content, text=f"Error loading semester permits: {e}",
                     fg="red").pack(pady=10)

    app.root.after_idle(load_daily)
    app.root.after_idle(load_semester)
