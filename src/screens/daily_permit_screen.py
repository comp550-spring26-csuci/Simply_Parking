import tkinter as tk
from tkinter import messagebox

DAILY_PERMIT_PRICE = 6.00


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


def build_buy_daily_permit_screen(app):
    app.clear_content()

    frame = tk.Frame(app.content_frame, padx=20, pady=20)
    frame.pack(anchor="nw")

    tk.Label(frame, text="Buy Daily Permit", font=("Arial", 16, "bold")).grid(
        row=0, column=0, columnspan=2, pady=10
    )

    tk.Label(frame, text="License Plate").grid(row=1, column=0, sticky="e", pady=5)
    plate_entry = dark_entry(frame)
    plate_entry.grid(row=1, column=1, padx=5, pady=5)

    tk.Label(frame, text=f"Price: ${DAILY_PERMIT_PRICE:.2f}").grid(
        row=2, column=0, columnspan=2, pady=10
    )

    def purchase():
        plate = plate_entry.get().strip().upper()

        if not plate:
            messagebox.showwarning("Input Error", "License plate is required.")
            return

        ok = app.db.create_daily_permit(
            user_id=app.current_user["id"],
            plate=plate,
            amount=DAILY_PERMIT_PRICE,
        )

        if not ok:
            messagebox.showerror(
                "Error",
                "Could not purchase daily permit. You may already have one for this plate today."
            )
            return

        app.db.add_log(
            event_type="daily_permit_purchase",
            details=f"Plate={plate}, amount=${DAILY_PERMIT_PRICE:.2f}",
            user_id=app.current_user["id"],
            username=app.current_user["username"],
        )

        if hasattr(app.db, "create_notification"):
            app.db.create_notification(
                title="Daily Permit Purchased",
                message=f"Daily permit purchased for plate {plate}. Amount: ${DAILY_PERMIT_PRICE:.2f}.",
                notification_type="purchase",
                user_id=app.current_user["id"],
            )

        if hasattr(app, "refresh_notification_badge"):
            app.refresh_notification_badge()

        messagebox.showinfo(
            "Success",
            f"Daily permit purchased.\n\nPlate: {plate}\nAmount: ${DAILY_PERMIT_PRICE:.2f}"
        )

        plate_entry.delete(0, tk.END)

    tk.Button(frame, text="Purchase Permit", command=purchase).grid(
        row=3, column=0, columnspan=2, pady=10
    )


def build_my_daily_permit_screen(app):
    app.clear_content()

    frame = tk.Frame(app.content_frame, padx=20, pady=20)
    frame.pack(anchor="nw")

    tk.Label(frame, text="My Daily Permit", font=("Arial", 16, "bold")).pack(pady=10)

    def load_today_permits():
        try:
            rows = app.db.fetch_today_daily_permits_for_user(app.current_user["id"])

            if not rows:
                tk.Label(frame, text="No active daily permit for today.").pack(pady=10)
                return

            for permit_id, plate, permit_date, amount, created_at in rows:
                tk.Label(
                    frame,
                    text=(
                        f"Active Daily Permit\n\n"
                        f"Permit ID: {permit_id}\n"
                        f"Plate: {plate}\n"
                        f"Date: {permit_date}\n"
                        f"Amount: ${float(amount):.2f}\n"
                        f"Purchased At: {created_at}"
                    ),
                    justify="left",
                ).pack(pady=10, anchor="w")

        except Exception as e:
            messagebox.showerror("Error", str(e))

    app.root.after_idle(load_today_permits)