import tkinter as tk
from tkinter import messagebox
import webbrowser
import threading
import time

import stripe_payments


# how often to check Stripe (in seconds)
POLL_TIME = 2
# stop checking after this many seconds
TIMEOUT = 600


class StripePaymentApp:

    def __init__(self):
        # make the main window
        self.window = tk.Tk()
        self.window.title("Simply Parking - Payments")
        self.window.geometry("450x500")

        # variable to remember the current Stripe session id
        self.session_id = None
        # flag to stop the polling loop if needed
        self.checking = False

        # build all the widgets
        self.make_widgets()

    def make_widgets(self):
        # title at the top
        title = tk.Label(self.window, text="Simply Parking",
                         font=("Arial", 16, "bold"))
        title.pack(pady=10)

        sub = tk.Label(self.window, text="Pay with Stripe")
        sub.pack()

        # user id input
        tk.Label(self.window, text="User ID:").pack(pady=(15, 0))
        self.user_id_entry = tk.Entry(self.window, width=30)
        self.user_id_entry.pack()

        # license plate input
        tk.Label(self.window, text="License Plate:").pack(pady=(10, 0))
        self.plate_entry = tk.Entry(self.window, width=30)
        self.plate_entry.pack()

        # permit type radio buttons
        tk.Label(self.window, text="Permit Type:").pack(pady=(10, 0))
        self.permit_type = tk.StringVar()
        self.permit_type.set("daily")  # default

        tk.Radiobutton(self.window, text="Daily ($5.00)",
                       variable=self.permit_type, value="daily").pack()
        tk.Radiobutton(self.window, text="Semester ($250.00)",
                       variable=self.permit_type, value="semester").pack()

        # buy permit button
        self.buy_button = tk.Button(self.window,
                                    text="Buy Permit with Stripe",
                                    command=self.buy_permit,
                                    width=30)
        self.buy_button.pack(pady=15)

        # divider line
        tk.Label(self.window, text="------------------------------").pack()

        # PAYG section
        tk.Label(self.window, text="Pay-As-You-Go Exit",
                 font=("Arial", 11, "bold")).pack(pady=(10, 0))
        tk.Label(self.window,
                 text="First 30 min free, then $0.50/min").pack()

        self.exit_button = tk.Button(self.window,
                                     text="Pay Exit Fee",
                                     command=self.pay_exit,
                                     width=30)
        self.exit_button.pack(pady=10)

        # status message at bottom
        self.status_label = tk.Label(self.window, text="Ready",
                                     fg="blue")
        self.status_label.pack(pady=10)

    # called when user clicks "Buy Permit"
    def buy_permit(self):
        # get the values from the form
        plate = self.plate_entry.get().strip().upper()
        user_id_text = self.user_id_entry.get().strip()

        # check that fields are filled in
        if plate == "":
            messagebox.showerror("Error", "Please enter a license plate")
            return

        # user id should be a number
        try:
            user_id = int(user_id_text)
        except ValueError:
            messagebox.showerror("Error", "User ID must be a number")
            return

        permit_type = self.permit_type.get()

        # disable buttons so user can't click again
        self.buy_button.config(state="disabled")
        self.exit_button.config(state="disabled")
        self.status_label.config(text="Creating checkout...")

        # do the Stripe call in the background so the window doesn't freeze
        thread = threading.Thread(target=self.do_buy_permit,
                                  args=(permit_type, plate, user_id))
        thread.daemon = True
        thread.start()

    # this runs in a background thread
    def do_buy_permit(self, permit_type, plate, user_id):
        try:
            print("Creating Stripe checkout for", permit_type, plate)
            session_id, url = stripe_payments.create_permit_checkout(
                permit_type, plate, user_id
            )
        except Exception as e:
            print("Stripe error:", e)
            self.show_error("Stripe error: " + str(e))
            return

        # save the session id so we can check it later
        self.session_id = session_id

        # open the browser to Stripe Checkout
        webbrowser.open(url)

        # update the status (must use .after because we're in a thread)
        self.window.after(0, lambda: self.status_label.config(
            text="Complete payment in browser..."
        ))

        # start checking if payment is done
        self.start_checking(self.permit_paid)

    # called when permit payment is confirmed
    def permit_paid(self):
        try:
            print("Payment confirmed, saving permit to database")
            ok = stripe_payments.activate_permit_after_payment(self.session_id)
        except Exception as e:
            print("Database error:", e)
            self.show_error("Database error: " + str(e))
            return

        if ok:
            self.show_success("Permit activated!")
        else:
            self.show_error("Payment ok but database insert failed")

    # called when user clicks "Pay Exit Fee"
    def pay_exit(self):
        plate = self.plate_entry.get().strip().upper()

        if plate == "":
            messagebox.showerror("Error", "Please enter the license plate")
            return

        # disable buttons
        self.buy_button.config(state="disabled")
        self.exit_button.config(state="disabled")
        self.status_label.config(text="Calculating amount...")

        # do this in a thread too
        thread = threading.Thread(target=self.do_pay_exit, args=(plate,))
        thread.daemon = True
        thread.start()

    def do_pay_exit(self, plate):
        try:
            print("Looking up active session for plate", plate)
            session_id, url, amount, minutes = (
                stripe_payments.create_payg_exit_checkout(plate)
            )
        except Exception as e:
            print("Error:", e)
            self.show_error("Error: " + str(e))
            return

        # case 1: no active session found
        if session_id is None and amount == 0 and minutes == 0:
            self.show_error("No active parking session for this plate")
            return

        # case 2: under 30 min, free exit (already closed in DB)
        if session_id is None and amount == 0:
            self.show_success(
                "Free exit (" + str(minutes) + " min). Session closed."
            )
            return

        # case 3: need to pay
        self.session_id = session_id
        webbrowser.open(url)

        dollars = amount / 100.0
        msg = ("$" + str(dollars) + " due (" + str(minutes) +
               " min). Complete payment in browser...")
        self.window.after(0, lambda: self.status_label.config(text=msg))

        self.start_checking(self.exit_paid)

    def exit_paid(self):
        try:
            print("Closing parking session in database")
            ok = stripe_payments.finalize_payg_exit(self.session_id)
        except Exception as e:
            print("Database error:", e)
            self.show_error("Database error: " + str(e))
            return

        if ok:
            self.show_success("Exit complete. Drive safely.")
        else:
            self.show_error("Payment ok but session close failed")

    # checks Stripe every 2 seconds to see if payment is done
    def start_checking(self, on_done):
        self.checking = True

        def check_loop():
            stop_time = time.time() + TIMEOUT
            while self.checking and time.time() < stop_time:
                try:
                    info = stripe_payments.get_session_status(self.session_id)

                    # payment is done
                    if info["payment_status"] == "paid":
                        print("Payment is paid!")
                        self.window.after(0, on_done)
                        return

                    # session expired
                    if info["status"] == "expired":
                        self.show_error("Checkout session expired")
                        return

                except Exception as e:
                    # if there's a network error, just print it and try again
                    print("Check error (will retry):", e)

                time.sleep(POLL_TIME)

            # if we got here, we timed out
            if self.checking:
                self.show_error("Timed out waiting for payment")

        thread = threading.Thread(target=check_loop)
        thread.daemon = True
        thread.start()

    # show success message and reset buttons
    def show_success(self, msg):
        self.checking = False
        self.window.after(0, lambda: self.status_label.config(text=msg,
                                                              fg="green"))
        self.window.after(0, lambda: self.buy_button.config(state="normal"))
        self.window.after(0, lambda: self.exit_button.config(state="normal"))
        self.window.after(0, lambda: messagebox.showinfo("Success", msg))

    # show error message and reset buttons
    def show_error(self, msg):
        self.checking = False
        self.window.after(0, lambda: self.status_label.config(text=msg,
                                                              fg="red"))
        self.window.after(0, lambda: self.buy_button.config(state="normal"))
        self.window.after(0, lambda: self.exit_button.config(state="normal"))
        self.window.after(0, lambda: messagebox.showerror("Error", msg))

    # start the app
    def run(self):
        self.window.mainloop()


# main - this runs when you do "python stripe_ui.py"
if __name__ == "__main__":
    app = StripePaymentApp()
    app.run()
