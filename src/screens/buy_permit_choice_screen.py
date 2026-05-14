import tkinter as tk
from tkinter import messagebox


def build_buy_permit_choice_screen(app):
    app.clear_content()
    f = tk.Frame(app.content_frame, padx=20, pady=20)
    f.pack(anchor="nw", fill="both", expand=True)

    tk.Label(f, text="Buy Parking Permit",
             font=("Arial", 16, "bold")).pack(pady=20)

    tk.Label(f, text="Select the type of permit you want to purchase:",
             font=("Arial", 11)).pack(pady=(0, 30))

    bf = tk.Frame(f)
    bf.pack(pady=20)

    def go_daily():
        app.show_buy_daily_permit()

    def go_semester():
        app.show_semester_permit()

    tk.Button(bf, text="Buy Daily Permit\n$6.00 (valid today only)",
              width=30, height=3, font=("Arial", 11),
              command=go_daily).pack(pady=10)

    tk.Button(bf, text="Buy Semester Permit\n$250.00 (by semester)",
              width=30, height=3, font=("Arial", 11),
              command=go_semester).pack(pady=10)
