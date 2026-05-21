import tkinter as tk
from tkinter import messagebox
from datetime import datetime
import webbrowser
import threading
import time
import stripe_service
import stripe_controller
from screens.qr_payment_screen import open_qr_payment

FREE_MINUTES = 30
PAYG_AMOUNT = 6.00
POLL_SECONDS = 2
POLL_ATTEMPTS = 150


def _fmt(minutes):
    h, m = divmod(minutes, 60)
    return f"{h}h {m}min" if h else f"{m} min"


def _calc(entry_time):
    if isinstance(entry_time, str):
        entry_dt = datetime.strptime(entry_time, "%Y-%m-%d %H:%M:%S")
    else:
        entry_dt = entry_time
    minutes = max(0, int((datetime.now() - entry_dt).total_seconds() // 60))
    amount = 0.00 if minutes <= FREE_MINUTES else PAYG_AMOUNT
    return entry_dt, minutes, amount


def _entry(parent):
    return tk.Entry(parent, width=30, bg="#1f1f1f", fg="white", insertbackground="white",
                    relief="solid", highlightthickness=1, highlightbackground="#777",
                    highlightcolor="#aaa")


def build_current_session_screen(app):
    app.clear_content()
    f = tk.Frame(app.content_frame, padx=20, pady=20)
    f.pack(anchor="nw")

    tk.Label(f, text="Current Parking Session",
             font=("Arial", 16, "bold")).grid(row=0, column=0, columnspan=2, pady=10)
    tk.Label(f, text="License Plate").grid(row=1, column=0, sticky="e", pady=5)
    pe = _entry(f)
    pe.grid(row=1, column=1, padx=5, pady=5)

    rl = tk.Label(f, text="Enter your plate to check active session.", justify="left")
    rl.grid(row=3, column=0, columnspan=2, sticky="w", pady=15)

    job = {"id": None}

    def stop():
        if job["id"]:
            app.root.after_cancel(job["id"])
            job["id"] = None

    def refresh(plate):
        row = app.db.fetch_active_session_by_plate(plate)
        if not row:
            rl.config(text=f"No active session for {plate}.")
            job["id"] = None
            return
        _, fp, et, _ = row
        edt, mins, amt = _calc(et)
        rl.config(text=(
            f"Plate      : {fp}\n"
            f"Entry Time : {edt.strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"Time Parked: {_fmt(mins)}\n"
            f"Status     : {'Free (under 30 min)' if amt == 0 else 'Payment required on exit'}\n"
            f"Est. Amount: ${amt:.2f}"))
        job["id"] = app.root.after(3000, lambda: refresh(plate))

    def lookup():
        plate = pe.get().strip().upper()
        if not plate:
            messagebox.showwarning("Input", "License plate is required.")
            return
        stop()
        refresh(plate)

    tk.Button(f, text="Check Time", command=lookup).grid(row=2, column=0, columnspan=2, pady=10)


def build_pay_exit_screen(app):
    app.clear_content()
    f = tk.Frame(app.content_frame, padx=20, pady=20)
    f.pack(anchor="nw")

    tk.Label(f, text="Pay On Exit",
             font=("Arial", 16, "bold")).grid(row=0, column=0, columnspan=3, pady=10)
    tk.Label(f, text="License Plate").grid(row=1, column=0, sticky="e", pady=5)
    pe = _entry(f)
    pe.grid(row=1, column=1, pady=5, padx=5)

    al = tk.Label(f, text="Enter plate to calculate amount.", justify="left")
    al.grid(row=3, column=0, columnspan=3, pady=10)

    state = {"session_id": None, "done": False}
    lock = threading.Lock()
    job = {"id": None}

    def set_status(msg, colour="blue"):
        app.root.after(0, lambda: al.config(text=msg, fg=colour))

    def stop_timer():
        if job["id"]:
            app.root.after_cancel(job["id"])
            job["id"] = None

    def reset():
        stop_timer()
        pe.delete(0, tk.END)
        al.config(text="Enter plate to calculate amount.", fg="black")
        verify_btn.config(state="disabled")
        pay_btn.config(state="normal")
        qr_btn.config(state="normal")
        with lock:
            state["session_id"] = None
            state["done"] = False
        if hasattr(app, "refresh_notification_badge"):
            app.refresh_notification_badge()

    def refresh_amount(plate):
        row = app.db.fetch_active_session_by_plate(plate)
        if not row:
            al.config(text=f"No active session for {plate}.", fg="black")
            job["id"] = None
            return
        _, fp, et, _ = row
        edt, mins, amt = _calc(et)
        al.config(fg="black", text=(
            f"Plate   : {fp}\n"
            f"Entry   : {edt.strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"Duration: {_fmt(mins)}\n"
            f"Status  : {'Free (under 30 min)' if amt == 0 else 'Payment required'}\n"
            f"Amount  : ${amt:.2f}"))
        job["id"] = app.root.after(3000, lambda: refresh_amount(plate))

    def calc():
        plate = pe.get().strip().upper()
        if not plate:
            messagebox.showwarning("Input", "License plate is required.")
            return
        stop_timer()
        refresh_amount(plate)

    def _get_session():
        plate = pe.get().strip().upper()
        if not plate:
            messagebox.showwarning("Input", "License plate is required.")
            return None
        row = app.db.fetch_active_session_by_plate(plate)
        if not row:
            messagebox.showerror("Error", f"No active session for {plate}.")
            return None
        sid, fp, et, _status = row
        _edt, mins, amt = _calc(et)
        uid = app.current_user.get("id") if app.current_user else None
        user = app.current_user.get("username", "guest") if app.current_user else "guest"
        return sid, fp, mins, amt, uid, user

    def _handle_free(sid, fp, mins, uid, user):
        # Free session close is not a Stripe payment.
        if not app.db.close_session(sid, 0.00):
            messagebox.showerror("Error", "Could not close parking session.")
            return
        app.db.add_log("payg_free_session", f"Plate={fp},duration={mins}min,$0.00",
                       user_id=uid, username=user)
        if uid:
            app.db.create_notification("Free Parking Session",
                f"Session closed for {fp}. {mins} min. $0.00.",
                notification_type="purchase", user_id=uid)
        messagebox.showinfo("Free Session",
                            f"No charge.\nPlate: {fp}\nDuration: {_fmt(mins)}\nAmount: $0.00")
        reset()

    def _finalize_once(sid2):
        with lock:
            if state["done"]:
                return
            state["done"] = True
        try:
            ok, msg = stripe_controller.finalize_payg_after_payment(app, sid2)
        except Exception as e:
            ok, msg = False, str(e)
        set_status(msg, "green" if ok else "red")
        if ok:
            app.root.after(0, lambda: messagebox.showinfo("Payment Complete", msg))
            app.root.after(0, reset)
        else:
            with lock:
                state["done"] = False
            app.root.after(0, lambda: messagebox.showerror("Error", msg))
            app.root.after(0, lambda: pay_btn.config(state="normal"))
            app.root.after(0, lambda: qr_btn.config(state="normal"))

    def manual_verify():
        sid2 = state["session_id"]
        if not sid2:
            messagebox.showwarning("No Session", "Start a payment first.")
            return
        set_status("Checking payment status…", "blue")
        threading.Thread(target=lambda: _check_once(sid2), daemon=True).start()

    def _check_once(sid2):
        try:
            info = stripe_service.get_checkout_status(sid2)
            if info["payment_status"] == "paid":
                _finalize_once(sid2)
            elif info["status"] == "expired":
                set_status("Session expired. Try again.", "red")
                app.root.after(0, lambda: pay_btn.config(state="normal"))
                app.root.after(0, lambda: qr_btn.config(state="normal"))
            else:
                set_status(f"Not paid yet. Stripe status: {info['payment_status']}.", "orange")
        except Exception as e:
            set_status(f"Check failed: {e}", "red")

    def _poll(sid2):
        for _ in range(POLL_ATTEMPTS):
            time.sleep(POLL_SECONDS)
            with lock:
                if state["done"]:
                    return
            try:
                info = stripe_service.get_checkout_status(sid2)
                if info["payment_status"] == "paid":
                    _finalize_once(sid2)
                    return
                if info["status"] == "expired":
                    set_status("Checkout expired. Try again.", "red")
                    app.root.after(0, lambda: pay_btn.config(state="normal"))
                    app.root.after(0, lambda: qr_btn.config(state="normal"))
                    return
            except Exception as e:
                set_status(f"Polling issue. You can still click Verify after paying. {e}", "orange")
        set_status("Auto-check timed out. Click 'I've Paid — Verify Now' below.", "orange")
        app.root.after(0, lambda: pay_btn.config(state="normal"))
        app.root.after(0, lambda: qr_btn.config(state="normal"))

    def _start_checkout(kind):
        vals = _get_session()
        if vals is None:
            return
        sid, fp, mins, amt, uid, user = vals
        if amt == 0:
            _handle_free(sid, fp, mins, uid, user)
            return

        with lock:
            state["done"] = False
        pay_btn.config(state="disabled")
        qr_btn.config(state="disabled")
        verify_btn.config(state="normal")
        set_status("Creating Stripe checkout…", "blue")

        def worker():
            try:
                s2, url = stripe_service.create_payg_checkout(uid, fp, sid, mins, amt)
                if not url.startswith("https://checkout.stripe.com/"):
                    raise ValueError(f"Invalid Stripe Checkout URL: {url}")
            except Exception as e:
                set_status(f"Stripe Error: {e}", "red")
                app.root.after(0, lambda: pay_btn.config(state="normal"))
                app.root.after(0, lambda: qr_btn.config(state="normal"))
                return

            state["session_id"] = s2
            if kind == "browser":
                webbrowser.open(url)
                set_status("Browser opened. Complete payment, then wait or click Verify.", "blue")
                threading.Thread(target=_poll, args=(s2,), daemon=True).start()
            else:
                app.root.after(0, lambda: open_qr_payment(
                    app.root, s2, url, amt, f"PAYG Exit — {fp}",
                    _finalize_once, lambda: (set_status("Payment cancelled.", "orange"),
                                             pay_btn.config(state="normal"), qr_btn.config(state="normal"))))

        threading.Thread(target=worker, daemon=True).start()

    tk.Button(f, text="Calculate Amount", command=calc).grid(row=2, column=0, pady=10, padx=4)

    bf = tk.Frame(f)
    bf.grid(row=4, column=0, columnspan=3, pady=8)
    pay_btn = tk.Button(bf, text="Pay with Stripe (Browser)", width=26, command=lambda: _start_checkout("browser"))
    pay_btn.pack(side="left", padx=6)
    qr_btn = tk.Button(bf, text="Pay with QR Code", width=20, command=lambda: _start_checkout("qr"))
    qr_btn.pack(side="left", padx=6)

    verify_btn = tk.Button(f,
                           text="I've Paid — Verify Now",
                           width=30, bg="#1a7a1a", fg="white",
                           font=("Arial", 11, "bold"),
                           state="disabled", command=manual_verify)
    verify_btn.grid(row=5, column=0, columnspan=3, pady=(4, 4))
