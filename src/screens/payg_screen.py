import tkinter as tk

def build_current_session_screen(app):
    tk.Label(app.content_frame, text="Current Parking Session", font=("Arial", 16, "bold")).pack(pady=20)
    tk.Label(app.content_frame, text="Placeholder for pay-as-you-go session tracking").pack()

def build_pay_exit_screen(app):
    tk.Label(app.content_frame, text="Pay On Exit", font=("Arial", 16, "bold")).pack(pady=20)
    tk.Label(app.content_frame, text="Placeholder for duration-based exit payment").pack()