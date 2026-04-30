import tkinter as tk

def build_login_screen(app):
    frame = tk.Frame(app.main_frame, padx=20, pady=20)
    frame.pack(expand=True)

    tk.Label(frame, text="Parking System Login", font=("Arial", 18, "bold")).grid(row=0, column=0, columnspan=2, pady=10)

    tk.Label(frame, text="Username").grid(row=1, column=0, sticky="e", pady=5)
    username_entry = tk.Entry(frame, width=30)
    username_entry.grid(row=1, column=1, pady=5)

    tk.Label(frame, text="Password").grid(row=2, column=0, sticky="e", pady=5)
    password_entry = tk.Entry(frame, width=30, show="*")
    password_entry.grid(row=2, column=1, pady=5)

    def do_login():
        app.login(username_entry.get().strip(), password_entry.get().strip())

    tk.Button(frame, text="Login", width=20, command=do_login).grid(row=3, column=0, columnspan=2, pady=25)