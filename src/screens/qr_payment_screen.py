import tkinter as tk
from tkinter import messagebox
import threading
import time

try:
    from PIL import ImageTk
    PIL_OK = True
except ImportError:
    PIL_OK = False

import stripe_service
import qr_payment as qr_util

POLL = 2
TIMEOUT = 600


class QRPaymentWindow(tk.Toplevel):
    def __init__(self, parent, session_id, checkout_url, amount, description, on_success, on_cancel=None):
        super().__init__(parent)
        self.session_id = session_id
        self.checkout_url = checkout_url
        self.amount = amount
        self.description = description
        self.on_success = on_success
        self.on_cancel = on_cancel
        self._polling = False
        self._done_called = False
        self.title("Scan QR Code to Pay")
        self.resizable(False, False)
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self._close)
        self._ui()
        self._start()

    def _ui(self):
        f = tk.Frame(self, padx=24, pady=20)
        f.pack()
        tk.Label(f, text="Scan QR Code to Pay", font=("Arial", 15, "bold")).pack()
        tk.Label(f, text=self.description, font=("Arial", 11), fg="#555").pack(pady=(4, 0))
        tk.Label(f, text=f"Amount: ${self.amount:.2f}", font=("Arial", 13, "bold"), fg="#1a7a1a").pack(pady=(3, 12))

        if not self.checkout_url.startswith("https://checkout.stripe.com/"):
            tk.Label(f, text="Invalid Stripe Checkout URL. Do not use checkout.stripe.dev.", fg="red").pack(pady=8)
            return

        img = qr_util.generate_qr_pil(self.checkout_url, box_size=8)
        if img and PIL_OK:
            self._tk = ImageTk.PhotoImage(img)
            tk.Label(f, image=self._tk, bd=2, relief="solid").pack(pady=6)
        else:
            tk.Label(f, text="Install qrcode[pil] for QR display. URL:", fg="red").pack()
            e = tk.Entry(f, width=52)
            e.insert(0, self.checkout_url)
            e.config(state="readonly")
            e.pack(pady=4)

        tk.Label(f, text="Point your phone camera at the QR code\nto open Stripe Checkout.",
                 font=("Arial", 10), fg="#444", justify="center").pack(pady=(8, 0))
        self.status = tk.Label(f, text="Waiting for payment…", fg="blue", font=("Arial", 11))
        self.status.pack(pady=(14, 4))
        tk.Button(f, text="Cancel", command=self._close, width=20).pack(pady=8)

    def _start(self):
        if not self.checkout_url.startswith("https://checkout.stripe.com/"):
            return
        self._polling = True
        threading.Thread(target=self._loop, daemon=True).start()

    def _loop(self):
        deadline = time.time() + TIMEOUT
        while self._polling and time.time() < deadline:
            try:
                info = stripe_service.get_checkout_status(self.session_id)
                if info["payment_status"] == "paid":
                    self._polling = False
                    self.after(0, self._paid)
                    return
                if info["status"] == "expired":
                    self._polling = False
                    self.after(0, lambda: self._error("Checkout session expired."))
                    return
            except Exception as e:
                print(f"QR poll: {e}")
            time.sleep(POLL)
        if self._polling:
            self._polling = False
            self.after(0, lambda: self._error("Timed out waiting for payment. Click Verify in the main window after paying."))

    def _paid(self):
        self.status.config(text="Payment confirmed!", fg="green")
        self.after(700, lambda: self._done(True))

    def _error(self, msg):
        if hasattr(self, "status"):
            self.status.config(text=msg, fg="red")
        messagebox.showerror("Payment Error", msg, parent=self)
        self.after(0, lambda: self._done(False))

    def _done(self, ok):
        if self._done_called:
            return
        self._done_called = True
        self._polling = False
        if ok and self.on_success:
            self.on_success(self.session_id)
        elif not ok and self.on_cancel:
            self.on_cancel()
        try:
            self.destroy()
        except Exception:
            pass

    def _close(self):
        if self._polling:
            if not messagebox.askyesno("Cancel", "Cancel this payment window? Payment will not be cancelled in Stripe.", parent=self):
                return
        self._done(False)


def open_qr_payment(parent, session_id, checkout_url, amount, description, on_success, on_cancel=None):
    return QRPaymentWindow(parent, session_id, checkout_url, amount, description, on_success, on_cancel)
