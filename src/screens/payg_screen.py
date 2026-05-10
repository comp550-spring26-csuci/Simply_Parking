import tkinter as tk
from tkinter import messagebox
from datetime import datetime


FREE_MINUTES = 30
DAILY_PERMIT_AMOUNT = 6.00


def format_duration(minutes):
    hours = minutes // 60
    mins = minutes % 60

    if hours > 0:
        return f"{hours} hour(s), {mins} minute(s)"
    return f"{mins} minute(s)"


def calculate_session_amount(entry_time):
    if isinstance(entry_time, str):
        entry_dt = datetime.strptime(entry_time, "%Y-%m-%d %H:%M:%S")
    else:
        entry_dt = entry_time

    now = datetime.now()
    minutes = max(0, int((now - entry_dt).total_seconds() // 60))

    amount = 0.00 if minutes <= FREE_MINUTES else DAILY_PERMIT_AMOUNT

    return entry_dt, minutes, amount


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


def build_current_session_screen(app):
    app.clear_content()

    frame = tk.Frame(app.content_frame, padx=20, pady=20)
    frame.pack(anchor="nw")

    tk.Label(
        frame,
        text="Current Parking Session",
        font=("Arial", 16, "bold")
    ).grid(row=0, column=0, columnspan=2, pady=10)

    tk.Label(frame, text="License Plate").grid(row=1, column=0, sticky="e", pady=5)
    plate_entry = dark_entry(frame)
    plate_entry.grid(row=1, column=1, padx=5, pady=5)

    result_label = tk.Label(
        frame,
        text="Enter your plate to view your active session.",
        justify="left",
    )
    result_label.grid(row=3, column=0, columnspan=2, sticky="w", pady=15)

    refresh_job = {"id": None}

    def stop_timer():
        if refresh_job["id"] is not None:
            try:
                app.root.after_cancel(refresh_job["id"])
            except Exception:
                pass
            refresh_job["id"] = None

    def refresh_session(plate):
        row = app.db.fetch_active_session_by_plate(plate)

        if not row:
            result_label.config(text=f"No active session found for plate {plate}.")
            return

        session_id, found_plate, entry_time, status = row
        entry_dt, minutes, amount = calculate_session_amount(entry_time)

        status_text = "Free session" if amount == 0 else "Daily permit required"

        result_label.config(
            text=(
                f"Plate: {found_plate}\n"
                f"Entry Time: {entry_dt.strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"Time Parked: {format_duration(minutes)}\n"
                f"Status: {status_text}\n"
                f"Amount Due: ${amount:.2f}"
            )
        )

        refresh_job["id"] = app.root.after(3000, lambda: refresh_session(plate))

    def lookup_plate():
        plate = plate_entry.get().strip().upper()

        if not plate:
            messagebox.showwarning("Input Error", "License plate is required.")
            return

        stop_timer()
        refresh_session(plate)

    tk.Button(frame, text="Check Time", command=lookup_plate).grid(
        row=2, column=0, columnspan=2, pady=10
    )


def build_pay_exit_screen(app):
    app.clear_content()

    frame = tk.Frame(app.content_frame, padx=20, pady=20)
    frame.pack(anchor="nw")

    tk.Label(frame, text="Pay On Exit", font=("Arial", 16, "bold")).grid(
        row=0, column=0, columnspan=2, pady=10
    )

    tk.Label(frame, text="License Plate").grid(row=1, column=0, sticky="e", pady=5)
    plate_entry = dark_entry(frame)
    plate_entry.grid(row=1, column=1, pady=5, padx=5)

    amount_label = tk.Label(
        frame,
        text="Enter plate to calculate time automatically.",
        justify="left",
    )
    amount_label.grid(row=3, column=0, columnspan=2, pady=10)

    refresh_job = {"id": None}
    current_session = {
        "session_id": None,
        "plate": None,
        "entry_time": None,
        "minutes": 0,
        "amount": 0.00,
    }

    def stop_timer():
        if refresh_job["id"] is not None:
            try:
                app.root.after_cancel(refresh_job["id"])
            except Exception:
                pass
            refresh_job["id"] = None

    def refresh_amount(plate):
        row = app.db.fetch_active_session_by_plate(plate)

        if not row:
            amount_label.config(text=f"No active session found for plate {plate}.")
            current_session["session_id"] = None
            return

        session_id, found_plate, entry_time, status = row
        entry_dt, minutes, amount = calculate_session_amount(entry_time)

        current_session["session_id"] = session_id
        current_session["plate"] = found_plate
        current_session["entry_time"] = entry_dt
        current_session["minutes"] = minutes
        current_session["amount"] = amount

        status_text = "Free session" if amount == 0 else "Daily permit required"

        amount_label.config(
            text=(
                f"Plate: {found_plate}\n"
                f"Entry: {entry_dt.strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"Duration: {format_duration(minutes)}\n"
                f"Status: {status_text}\n"
                f"Amount Due: ${amount:.2f}"
            )
        )

        refresh_job["id"] = app.root.after(3000, lambda: refresh_amount(plate))

    def preview_amount():
        plate = plate_entry.get().strip().upper()

        if not plate:
            messagebox.showwarning("Input Error", "License plate is required.")
            return

        stop_timer()
        refresh_amount(plate)

    def pay_now():
        plate = plate_entry.get().strip().upper()

        if not plate:
            messagebox.showwarning("Input Error", "License plate is required.")
            return

        row = app.db.fetch_active_session_by_plate(plate)

        if not row:
            messagebox.showerror("Error", f"No active session found for plate {plate}.")
            return

        session_id, found_plate, entry_time, status = row
        entry_dt, minutes, amount = calculate_session_amount(entry_time)

        user_id = app.current_user.get("id") if app.current_user else None
        username = app.current_user.get("username") if app.current_user else "guest"
        paid_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if amount == 0:
            app.db.add_log(
                event_type="payg_free_session",
                details=f"Plate={found_plate}, duration={minutes} minutes, amount=$0.00",
                user_id=user_id,
                username=username,
            )

            if user_id is not None and hasattr(app.db, "create_notification"):
                app.db.create_notification(
                    title="Free Parking Session",
                    message=(
                        f"PAYG session completed for plate {found_plate}. "
                        f"Duration: {minutes} minutes. Amount: $0.00."
                    ),
                    notification_type="purchase",
                    user_id=user_id,
                )

            app.db.close_session(session_id, amount)

            messagebox.showinfo(
                "Free Session",
                f"No payment required.\n\nPlate: {found_plate}\nDuration: {minutes} minutes\nAmount: $0.00"
            )

        else:
            app.db.add_log(
                event_type="daily_permit_purchase_successful",
                details=f"Plate={found_plate}, duration={minutes} minutes, amount=${amount:.2f}",
                user_id=user_id,
                username=username,
            )

            if hasattr(app.db, "create_payg_payment"):
                app.db.create_payg_payment(
                    user_id=user_id,
                    plate=found_plate,
                    duration_minutes=minutes,
                    amount=amount,
                )

            if user_id is not None and hasattr(app.db, "create_notification"):
                app.db.create_notification(
                    title="Daily Permit Purchased",
                    message=(
                        f"Daily permit purchased for plate {found_plate}. "
                        f"PAYG duration: {minutes} minutes. Amount: ${amount:.2f}. Paid at {paid_at}."
                    ),
                    notification_type="purchase",
                    user_id=user_id,
                )

            app.db.close_session(session_id, amount)

            messagebox.showinfo(
                "Payment Successful",
                f"Daily permit purchased.\n\nPlate: {found_plate}\nDuration: {minutes} minutes\nAmount: ${amount:.2f}"
            )

        stop_timer()

        if user_id is not None and hasattr(app, "refresh_notification_badge"):
            app.refresh_notification_badge()

        plate_entry.delete(0, tk.END)
        amount_label.config(text="Enter plate to calculate time automatically.")

    tk.Button(frame, text="Calculate Amount", command=preview_amount).grid(
        row=4, column=0, pady=10
    )

    tk.Button(frame, text="Pay Now", command=pay_now).grid(
        row=4, column=1, pady=10
    )