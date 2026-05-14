import tkinter as tk
from tkinter import messagebox


def build_register_account_screen(app):
    if app.current_user and app.current_user.get("role") == "guest":
        app.clear_content()
        container = app.content_frame
    else:
        app.clear_main()
        container = app.main_frame

    card = tk.Frame(container, padx=24, pady=24, bd=1, relief="solid")
    card.pack(pady=40, padx=40)

    tk.Label(card, text="Create Account", font=("Arial", 18, "bold")).grid(
        row=0, column=0, columnspan=2, pady=(0, 12)
    )

    tk.Label(card, text="Full Name", font=("Arial", 11)).grid(row=1, column=0, sticky="e", pady=6)
    full_name_entry = tk.Entry(card, width=32)
    full_name_entry.grid(row=1, column=1, pady=6, padx=8)

    tk.Label(card, text="Username", font=("Arial", 11)).grid(row=2, column=0, sticky="e", pady=6)
    username_entry = tk.Entry(card, width=32)
    username_entry.grid(row=2, column=1, pady=6, padx=8)

    tk.Label(card, text="Password", font=("Arial", 11)).grid(row=3, column=0, sticky="e", pady=6)
    password_entry = tk.Entry(card, width=32, show="*")
    password_entry.grid(row=3, column=1, pady=6, padx=8)

    tk.Label(card, text="Confirm Password", font=("Arial", 11)).grid(row=4, column=0, sticky="e", pady=6)
    confirm_entry = tk.Entry(card, width=32, show="*")
    confirm_entry.grid(row=4, column=1, pady=6, padx=8)

    def do_create():
        full_name = full_name_entry.get().strip()
        username = username_entry.get().strip()
        password = password_entry.get().strip()
        confirm = confirm_entry.get().strip()

        if not username or not password or not confirm:
            messagebox.showwarning("Missing Fields", "Username and password are required.")
            return
        if password != confirm:
            messagebox.showwarning("Password Mismatch", "Passwords do not match.")
            return

        ok = app.db.create_user(username, password, "user", full_name)
        if ok:
            app.db.add_log(
                event_type="user_registered",
                details=f"Guest created username={username}",
                user_id=app.current_user["id"] if app.current_user else None,
                username=app.current_user["username"] if app.current_user else "guest",
            )
            messagebox.showinfo("Success", "Account created successfully. Please log in.")
            app.show_login()
        else:
            messagebox.showerror(
                "Error",
                "Could not create account. Username may already exist.",
            )

    create_button = tk.Button(card, text="Create Account", width=30, command=do_create)
    create_button.grid(row=5, column=0, columnspan=2, pady=(16, 6), ipady=4)

    def go_back():
        if app.current_user and app.current_user.get("role") == "guest":
            app.show_dashboard()
        else:
            app.show_login()

    tk.Button(card, text="Back", width=30, command=go_back).grid(
        row=6, column=0, columnspan=2, pady=(0, 4), ipady=4
    )

    username_entry.focus_set()
