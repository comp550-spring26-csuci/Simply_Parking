import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date, timedelta
import webbrowser
import threading
import time
import stripe_service
import stripe_controller
from screens.qr_payment_screen import open_qr_payment

PRICE = 250.00
DEFAULT_DAYS = 120
POLL_SECONDS = 2
POLL_ATTEMPTS = 300


def _entry(parent, **kw):
    return tk.Entry(parent, width=30, bg="#1f1f1f", fg="white", insertbackground="white",
                    relief="solid", highlightthickness=1, highlightbackground="#777",
                    highlightcolor="#aaa", **kw)


def build_semester_permit_screen(app):
    app.clear_content()
    outer = tk.Frame(app.content_frame, padx=20, pady=20)
    outer.pack(anchor="nw", fill="both", expand=True)

    tk.Label(outer, text="Semester Parking Permit",
             font=("Arial", 16, "bold")).grid(row=0, column=0, columnspan=3, pady=10)

    banner = tk.Frame(outer, bd=1, relief="solid", padx=12, pady=10, bg="#f0f8f0")
    banner.grid(row=1, column=0, columnspan=3, sticky="ew", pady=(0, 14))
    banner_lbl = tk.Label(banner, text="Checking permit status…", bg="#f0f8f0", font=("Arial", 11))
    banner_lbl.pack(anchor="w")

    vehicle_map = {}

    def refresh_banner():
        try:
            rows = app.db.fetch_active_semester_permits_for_user(app.current_user["id"])
            if rows:
                _, plate, start, end, _amt, _created = rows[0]
                days_left = (date.fromisoformat(str(end)) - date.today()).days
                banner.config(bg="#e8f5e9")
                banner_lbl.config(bg="#e8f5e9", fg="#1a7a1a",
                    text=f"ACTIVE — Plate: {plate} | Valid: {start} → {end} | {days_left} days left")
            else:
                banner.config(bg="#fff3e0")
                banner_lbl.config(bg="#fff3e0", fg="#bf6000",
                    text="No active semester permit. Register a vehicle, then purchase below.")
        except Exception as e:
            banner_lbl.config(text=f"Could not load status: {e}", fg="red")

    tk.Label(outer, text="Registered Vehicle").grid(row=2, column=0, sticky="e", pady=6)
    vehicle_combo = ttk.Combobox(outer, width=34, state="readonly")
    vehicle_combo.grid(row=2, column=1, padx=6, pady=6)
    tk.Button(outer, text="Register Vehicle", command=app.show_register_vehicle).grid(row=2, column=2, padx=6)

    today = date.today()
    end_default = today + timedelta(days=DEFAULT_DAYS)

    tk.Label(outer, text="Start Date (YYYY-MM-DD)").grid(row=3, column=0, sticky="e", pady=6)
    se = _entry(outer)
    se.insert(0, str(today))
    se.grid(row=3, column=1, padx=6, pady=6)

    tk.Label(outer, text="End Date (YYYY-MM-DD)").grid(row=4, column=0, sticky="e", pady=6)
    ee = _entry(outer)
    ee.insert(0, str(end_default))
    ee.grid(row=4, column=1, padx=6, pady=6)

    tk.Label(outer, text=f"Price: ${PRICE:.2f} ({DEFAULT_DAYS}-day semester permit)",
             font=("Arial", 11)).grid(row=5, column=0, columnspan=3, pady=8)

    sl = tk.Label(outer, text="", fg="blue", justify="left")
    sl.grid(row=6, column=0, columnspan=3, pady=4)

    state = {"session_id": None, "done": False}
    lock = threading.Lock()

    def load_vehicles():
        vehicle_map.clear()
        labels = []
        try:
            rows = app.db.fetch_user_vehicles(app.current_user["id"])
            for _vid, plate, make, model, color, _created in rows:
                details = " ".join(x for x in [make, model, color] if x)
                label = plate if not details else f"{plate} — {details}"
                vehicle_map[label] = plate
                labels.append(label)
        except Exception as e:
            sl.config(text=f"Could not load vehicles: {e}", fg="red")
        vehicle_combo["values"] = labels
        if labels:
            vehicle_combo.current(0)
        else:
            sl.config(text="No registered vehicles found. Register a vehicle before buying a semester permit.", fg="orange")

    def selected_plate():
        label = vehicle_combo.get().strip()
        return vehicle_map.get(label, "").strip().upper()

    def set_status(msg, colour="blue"):
        app.root.after(0, lambda: sl.config(text=msg, fg=colour))

    def validate():
        if not app.current_user or not app.current_user.get("id"):
            messagebox.showerror("Login Required", "You must be logged in.")
            return None, None, None

        plate = selected_plate()
        if not plate:
            messagebox.showwarning("Vehicle Required", "Register and select a vehicle before buying a semester permit.")
            return None, None, None

        try:
            sd = date.fromisoformat(se.get().strip())
            ed = date.fromisoformat(ee.get().strip())
        except ValueError:
            messagebox.showerror("Date Error", "Use YYYY-MM-DD format.")
            return None, None, None
        if ed <= sd:
            messagebox.showerror("Date Error", "End date must be after start date.")
            return None, None, None
        if sd < date.today():
            messagebox.showerror("Date Error", "Start date cannot be in the past.")
            return None, None, None

        if not app.db.user_owns_vehicle(app.current_user["id"], plate):
            messagebox.showerror("Vehicle Required", "This vehicle is not registered to your account.")
            return None, None, None

        if app.db.has_active_semester_permit_for_plate(app.current_user["id"], plate):
            messagebox.showinfo("Already Active", f"{plate} already has an active semester permit.")
            return None, None, None

        return plate, sd, ed

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
            ok, msg = stripe_controller.activate_semester_permit_after_payment(app, sid)
        except Exception as e:
            ok, msg = False, str(e)
        set_status(msg, "green" if ok else "red")
        if ok:
            app.root.after(0, lambda: messagebox.showinfo("Success", msg))
            app.root.after(0, load_permits)
            app.root.after(0, refresh_banner)
            if hasattr(app, "refresh_notification_badge"):
                app.root.after(0, app.refresh_notification_badge)
        else:
            with lock:
                state["done"] = False
            app.root.after(0, lambda: messagebox.showerror("Error", msg))
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
        plate, sd, ed = validate()
        if plate is None:
            return
        with lock:
            state["done"] = False
        disable()
        sl.config(text="Creating Stripe checkout…", fg="blue")

        def worker():
            try:
                sid, url = stripe_service.create_semester_permit_checkout(
                    user_id=app.current_user["id"], plate=plate,
                    start_date=str(sd), end_date=str(ed))
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
                    app.root, sid, url, PRICE, f"Semester Permit — {plate}",
                    _activate_once, lambda: (set_status("Payment cancelled.", "orange"), enable())))

        threading.Thread(target=worker, daemon=True).start()

    bf = tk.Frame(outer)
    bf.grid(row=7, column=0, columnspan=3, pady=12)

    buy_btn = tk.Button(bf, text="Pay with Stripe (Browser)", width=26, command=lambda: _start_checkout("browser"))
    buy_btn.pack(side="left", padx=6)

    qr_btn = tk.Button(bf, text="Pay with QR Code", width=20, command=lambda: _start_checkout("qr"))
    qr_btn.pack(side="left", padx=6)

    verify_btn = tk.Button(outer, text="I've Paid — Verify Now",
                           width=30, bg="#1a7a1a", fg="white",
                           font=("Arial", 11, "bold"),
                           state="disabled", command=manual_verify)
    verify_btn.grid(row=8, column=0, columnspan=3, pady=(4, 4))

    tk.Label(outer, text="My Semester Permits",
             font=("Arial", 13, "bold")).grid(row=9, column=0, columnspan=3, pady=(20, 6))

    cols = ("id", "plate", "start", "end", "amount", "status", "purchased")
    tree = ttk.Treeview(outer, columns=cols, show="headings", height=6)
    heads = {"id": "ID", "plate": "Plate", "start": "Start", "end": "End",
             "amount": "Amount", "status": "Status", "purchased": "Purchased"}
    widths = {"id": 50, "plate": 100, "start": 100, "end": 100,
              "amount": 80, "status": 80, "purchased": 140}
    for c in cols:
        tree.heading(c, text=heads[c])
        tree.column(c, width=widths[c], anchor="center")

    sb = ttk.Scrollbar(outer, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=sb.set)
    tree.grid(row=10, column=0, columnspan=2, pady=4, sticky="ew")
    sb.grid(row=10, column=2, sticky="ns")

    def load_permits():
        for item in tree.get_children():
            tree.delete(item)
        try:
            rows = app.db.fetch_semester_permits_for_user(app.current_user["id"])
            if not rows:
                tree.insert("", "end", values=("", "No permits found.", "", "", "", "", ""))
                return
            today_ = date.today()
            for pid, plate, start, end, amount, created in rows:
                status = "Active" if date.fromisoformat(str(start)) <= today_ <= date.fromisoformat(str(end)) else "Expired"
                tree.insert("", "end", values=(pid, plate, start, end, f"${float(amount):.2f}", status, str(created)[:16]))
        except Exception as e:
            messagebox.showerror("Error", str(e))

    load_vehicles()
    refresh_banner()
    load_permits()
