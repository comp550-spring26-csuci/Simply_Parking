import tkinter as tk
from tkinter import messagebox
from datetime import datetime


FREE_MINUTES = 30
DAILY_PERMIT_AMOUNT = 6.00


def dark_entry(parent):
    return tk.Entry(
        parent,
        width=30,
        bg="#1f1f1f",
        fg="white",
        insertbackground="white",
        relief="solid",
        highlightthickness=1,
        highlightbackground="#777777",
        highlightcolor="#aaaaaa",
    )


def format_duration(minutes):
    hours = minutes // 60
    mins = minutes % 60

    if hours > 0:
        return f"{hours} hour(s), {mins} minute(s)"
    return f"{mins} minute(s)"


def build_guest_session_lookup_screen(app):
    app.clear_content()

    frame = tk.Frame(app.content_frame, padx=20, pady=20)
    frame.pack(anchor="nw")

    tk.Label(
        frame,
        text="Guest Parking Time Lookup",
        font=("Arial", 16, "bold")
    ).grid(row=0, column=0, columnspan=2, pady=10)

    tk.Label(frame, text="License Plate").grid(row=1, column=0, sticky="e", pady=5)

    plate_entry = dark_entry(frame)
    plate_entry.grid(row=1, column=1, padx=5, pady=5)

    result_label = tk.Label(frame, text="", justify="left")
    result_label.grid(row=3, column=0, columnspan=2, sticky="w", pady=15)

    def lookup_plate():
        plate = plate_entry.get().strip().upper()

        if not plate:
            messagebox.showwarning("Input Error", "License plate is required.")
            return

        row = app.db.fetch_latest_plate_session(plate)

        if not row:
            result_label.config(
                text=f"No active record found for plate {plate}."
            )
            return

        record_id, found_plate, source_file, entry_time = row

        if isinstance(entry_time, str):
            entry_dt = datetime.strptime(entry_time, "%Y-%m-%d %H:%M:%S")
        else:
            entry_dt = entry_time

        now = datetime.now()
        duration_minutes = max(0, int((now - entry_dt).total_seconds() // 60))

        if duration_minutes <= FREE_MINUTES:
            amount_due = 0.00
            status = "Free session"
        else:
            amount_due = DAILY_PERMIT_AMOUNT
            status = "Daily permit required"

        result_label.config(
            text=(
                f"Plate: {found_plate}\n"
                f"Entry Time: {entry_dt.strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"Time Parked: {format_duration(duration_minutes)}\n"
                f"Status: {status}\n"
                f"Amount Due: ${amount_due:.2f}"
            )
        )

    tk.Button(
        frame,
        text="Check Time",
        command=lookup_plate
    ).grid(row=2, column=0, columnspan=2, pady=10)