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
POLL_SECONDS = 2
POLL_ATTEMPTS = 300

# Semester definitions: (label, start_date, end_date)
SEMESTERS = [
    ("Spring 2026", date(2026, 1, 24), date(2026, 5, 29)),
    ("Fall 2026", date(2026, 8, 22), date(2026, 12, 18)),
    ("Spring 2027", date(2027, 1, 22), date(2027, 5, 28)),
    ("Fall 2027", date(2027, 8, 21), date(2027, 12, 17)),
    ("Spring 2028", date(2028, 1, 21), date(2028, 5, 26)),
]

def _entry(parent, **kw):
    return tk.Entry(parent, width=30, bg="#1f1f1f", fg="white", insertbackground="white",
                    relief="solid", highlightthickness=1, highlightbackground="#777",
                    highlightcolor="#aaa", **kw)

def _get_current_semester():
    """Return the label of the semester that today's date falls under, or the next upcoming semester."""
    today = date.today()
    for label, start, end in SEMESTERS:
        if start <= today <= end:
            return label
    # If today is outside all defined semesters, return the first one
    return SEMESTERS[0][0] if SEMESTERS else None

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

    # Semester selection dropdown
    tk.Label(outer, text="Select Semester").grid(row=3, column=0, sticky="e", pady=6)
    semester_var = tk.StringVar()
    semester_combo = ttk.Combobox(outer, textvariable=semester_var, state="readonly", width=32)
    semester_labels = [label for label, _, _ in SEMESTERS]
    semester_combo["values"] = semester_labels
    semester_combo.grid(row=3, column=1, padx=6, pady=6)
    
    # Set default to current semester
    current_sem = _get_current_semester()
    if current_sem:
        semester_combo.set(current_sem)

    # Date display labels (read-only)
    tk.Label(outer, text="Start Date").grid(row=4, column=0, sticky="e", pady=6)
    start_lbl = tk.Label(outer, text="", fg="#1a7a1a", font=("Arial", 10, "bold"))
    start_lbl.grid(row=4, column=1, padx=6, pady=6, sticky="w")

    tk.Label(outer, text="End Date").grid(row=5, column=0, sticky="e", pady=6)
    end_lbl = tk.Label(outer, text="", fg="#1a7a1a", font=("Arial", 10, "bold"))
    end_lbl.grid(row=5, column=1, padx=6, pady=6, sticky="w")

    # Store selected semester dates
    selected_dates = {"start": None, "end": None}

    def update_dates(event=None):
        sem_label = semester_var.get().strip()
        for label, start, end in SEMESTERS:
            if label == sem_label:
                selected_dates["start"] = start
                selected_dates["end"] = end
                start_lbl.config(text=str(start))
                end_lbl.config(text=str(end))
                return
        selected_dates["start"] = None
        selected_dates["end"] = None
        start_lbl.config(text="")
        end_lbl.config(text="")

    semester_combo.bind("<<ComboboxSelected>>", update_dates)
    # Trigger initial date display
    if current_sem:
        app.root.after_idle(update_dates)

    tk.Label(outer, text=f"Price: ${PRICE:.2f} (semester permit)",
             font=("Arial", 11)).grid(row=6, column=0, columnspan=3, pady=8)

    sl = tk.Label(outer, text="", fg="blue", justify="left")
    sl.grid(row=7, column=0, columnspan=3, pady=4)

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

        sd = selected_dates["start"]
        ed = selected_dates["end"]
        if not sd or not ed:
            messagebox.showerror("Semester Error", "Please select a valid semester.")
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

    back_btn = tk.Button(outer, text="← Back", command=app.show_buy_permit_choice)
    back_btn.grid(row=9, column=0, columnspan=3, pady=(20, 0))

    load_vehicles()
    refresh_banner()
