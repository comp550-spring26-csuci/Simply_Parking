import tkinter as tk
from tkinter import ttk, messagebox
import webbrowser
import threading
import time
import stripe_service
import stripe_controller
from screens.qr_payment_screen import open_qr_payment

PRICE = 6.00
POLL_SECONDS = 2
POLL_ATTEMPTS = 150


def _entry(parent):
    return tk.Entry(parent, width=30, bg="#1f1f1f", fg="white", insertbackground="white",
                    relief="solid", highlightthickness=1, highlightbackground="#777",
                    highlightcolor="#aaa")


def build_buy_daily_permit_screen(app):
    app.clear_content()
    f = tk.Frame(app.content_frame, padx=20, pady=20)
    f.pack(anchor="nw")

    tk.Label(f, text="Buy Daily Permit", font=("Arial", 16, "bold")).grid(
        row=0, column=0, columnspan=3, pady=10)

    tk.Label(f, text="Registered Vehicle").grid(row=1, column=0, sticky="e", pady=5)
    vehicle_combo = ttk.Combobox(f, width=28, state="readonly")
    vehicle_combo.grid(row=1, column=1, padx=5, pady=5)

    tk.Label(f, text="Visitor / Manual Plate").grid(row=2, column=0, sticky="e", pady=5)
    manual_plate_entry = _entry(f)
    manual_plate_entry.grid(row=2, column=1, padx=5, pady=5)

    tk.Label(f, text="Use dropdown for your vehicle, or type a visitor plate manually.",
             fg="#666", font=("Arial", 9)).grid(row=3, column=0, columnspan=3, pady=(0, 6))

    tk.Label(f, text=f"Price: ${PRICE:.2f}  (valid today only)").grid(
        row=4, column=0, columnspan=3, pady=6)

    sl = tk.Label(f, text="", fg="blue", justify="left")
    sl.grid(row=5, column=0, columnspan=3, pady=4)

    state = {"session_id": None, "done": False}
    lock = threading.Lock()

    def load_vehicles():
        values = []
        try:
            if app.current_user and app.current_user.get("id"):
                rows = app.db.fetch_user_vehicles(app.current_user["id"])
                for _vid, plate, make, model, color, _created in rows:
                    label = plate
                    details = " ".join(x for x in [make, model, color] if x)
                    if details:
                        label = f"{plate} — {details}"
                    values.append(label)
        except Exception as e:
            sl.config(text=f"Could not load vehicles: {e}", fg="orange")
        vehicle_combo["values"] = values
        if values:
            vehicle_combo.current(0)

    def selected_registered_plate():
        value = vehicle_combo.get().strip()
        if not value:
            return ""
        return value.split("—", 1)[0].strip().upper()

    def set_status(msg, colour="blue"):
        app.root.after(0, lambda: sl.config(text=msg, fg=colour))

    def validate():
        if not app.current_user or not app.current_user.get("id"):
            messagebox.showerror("Login Required", "You must be logged in.")
            return None

        manual = manual_plate_entry.get().strip().upper()
        registered = selected_registered_plate()
        plate = manual or registered

        if not plate:
            messagebox.showwarning("Input", "Select a registered vehicle or enter a visitor plate.")
            return None

        if len(plate) < 2:
            messagebox.showwarning("Input", "License plate looks too short.")
            return None

        try:
            if app.db.has_daily_permit_today(app.current_user["id"], plate):
                messagebox.showinfo("Already Active", f"You already have a daily permit for {plate} today.")
                return None
        except Exception:
            # Do not block checkout if the pre-check fails; DB uniqueness still protects duplicates.
            pass

        return plate

    def disable():
        app.root.after(0, lambda: buy_btn.config(state="disabled"))
        app.root.after(0, lambda: qr_btn.config(state="disabled"))
        app.root.after(0, lambda: verify_btn.config(state="normal"))

    def enable():
        app.root.after(0, lambda: buy_btn.config(state="normal"))
        app.root.after(0, lambda: qr_btn.config(state="normal"))
        app.root.after(0, lambda: verify_btn.config(state="disabled"))

    def _activate_once(sid):
        with lock:
            if state["done"]:
                return
            state["done"] = True
        try:
            ok, msg = stripe_controller.activate_daily_permit_after_payment(app, sid)
        except Exception as e:
            ok, msg = False, str(e)

        set_status(msg, "green" if ok else "red")
        if ok:
            app.root.after(0, lambda: messagebox.showinfo("Success", msg))
            app.root.after(0, lambda: manual_plate_entry.delete(0, tk.END))
            app.root.after(0, app.show_my_daily_permit)
            if hasattr(app, "refresh_notification_badge"):
                app.root.after(0, app.refresh_notification_badge)
        else:
            app.root.after(0, lambda: messagebox.showerror("Error", msg))
            with lock:
                state["done"] = False
            enable()

    def manual_verify():
        sid = state["session_id"]
        if not sid:
            messagebox.showwarning("No Session", "Start a payment first.")
            return
        set_status("Checking payment status…", "blue")
        threading.Thread(target=lambda: _check_once(sid), daemon=True).start()

    def _check_once(sid):
        try:
            info = stripe_service.get_checkout_status(sid)
            if info["payment_status"] == "paid":
                _activate_once(sid)
            elif info["status"] == "expired":
                set_status("Session expired. Please try again.", "red")
                enable()
            else:
                set_status(f"Not paid yet. Stripe status: {info['payment_status']}.", "orange")
        except Exception as e:
            set_status(f"Check failed: {e}", "red")

    def _poll(sid):
        for _ in range(POLL_ATTEMPTS):
            time.sleep(POLL_SECONDS)
            with lock:
                if state["done"]:
                    return
            try:
                info = stripe_service.get_checkout_status(sid)
                if info["payment_status"] == "paid":
                    _activate_once(sid)
                    return
                if info["status"] == "expired":
                    set_status("Checkout expired. Please try again.", "red")
                    enable()
                    return
            except Exception as e:
                set_status(f"Polling issue. You can still click Verify after paying. {e}", "orange")
        set_status("Auto-check timed out. Click 'I've Paid — Verify Now'.", "orange")
        enable()

    def _start_checkout(kind):
        plate = validate()
        if not plate:
            return
        with lock:
            state["done"] = False
        disable()
        sl.config(text="Creating Stripe checkout…", fg="blue")

        def worker():
            try:
                sid, url = stripe_service.create_daily_permit_checkout(
                    user_id=app.current_user["id"], plate=plate)
                if not url.startswith("https://checkout.stripe.com/"):
                    raise ValueError(f"Invalid Stripe Checkout URL: {url}")
            except Exception as e:
                set_status(f"Stripe Error: {e}", "red")
                enable()
                return

            state["session_id"] = sid
            if kind == "browser":
                webbrowser.open(url)
                set_status("Browser opened. Complete payment, then wait or click Verify.", "blue")
                threading.Thread(target=_poll, args=(sid,), daemon=True).start()
            else:
                app.root.after(0, lambda: open_qr_payment(
                    app.root, sid, url, PRICE, f"Daily Permit — {plate}",
                    _activate_once, lambda: (set_status("Payment cancelled.", "orange"), enable())))

        threading.Thread(target=worker, daemon=True).start()

    bf = tk.Frame(f)
    bf.grid(row=6, column=0, columnspan=3, pady=10)

    buy_btn = tk.Button(bf, text="Pay with Stripe (Browser)", width=26, command=lambda: _start_checkout("browser"))
    buy_btn.pack(side="left", padx=6)

    qr_btn = tk.Button(bf, text="Pay with QR Code", width=20, command=lambda: _start_checkout("qr"))
    qr_btn.pack(side="left", padx=6)

    verify_btn = tk.Button(f, text="I've Paid — Verify Now",
                           width=30, bg="#1a7a1a", fg="white",
                           font=("Arial", 11, "bold"),
                           state="disabled", command=manual_verify)
    verify_btn.grid(row=7, column=0, columnspan=3, pady=(4, 12))

    tk.Button(f, text="← Back", command=app.show_buy_permit_choice).grid(row=8, column=0, columnspan=3, pady=(0, 0))

    load_vehicles()


def build_my_daily_permit_screen(app):
    app.clear_content()
    f = tk.Frame(app.content_frame, padx=20, pady=20)
    f.pack(anchor="nw")
    tk.Label(f, text="My Daily Permit", font=("Arial", 16, "bold")).pack(pady=10)

    def load():
        try:
            rows = app.db.fetch_today_daily_permits_for_user(app.current_user["id"])
            if not rows:
                tk.Label(f, text="No active daily permit for today.\n\nClick 'Buy Daily Permit' to purchase one.",
                         fg="#555").pack(pady=10)
                return
            for pid, plate, pdate, amount, created in rows:
                card = tk.Frame(f, bd=1, relief="solid", padx=16, pady=12)
                card.pack(anchor="w", pady=6)
                tk.Label(card, text="ACTIVE", font=("Arial", 11, "bold"), fg="#1a7a1a").pack(anchor="w")
                tk.Label(card, text=(
                    f"Permit ID  : {pid}\n"
                    f"Plate      : {plate}\n"
                    f"Valid Date : {pdate}\n"
                    f"Amount     : ${float(amount):.2f}\n"
                    f"Purchased  : {str(created)[:16]}"),
                    justify="left", font=("Arial", 10)).pack(anchor="w", pady=4)
        except Exception as e:
            messagebox.showerror("Error", str(e))

    app.root.after_idle(load)
