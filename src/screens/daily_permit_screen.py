import tkinter as tk

def build_buy_daily_permit_screen(app):
    tk.Label(app.content_frame, text="Buy Daily Permit", font=("Arial", 16, "bold")).pack(pady=20)
    tk.Label(app.content_frame, text="Placeholder for daily permit purchase").pack()

def build_my_daily_permit_screen(app):
    tk.Label(app.content_frame, text="My Daily Permit", font=("Arial", 16, "bold")).pack(pady=20)
    tk.Label(app.content_frame, text="Placeholder for today's permit view").pack()