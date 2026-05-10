import tkinter as tk
from tkinter import messagebox

def build_reset_password_screen(app):
    frame = tk.Frame(app.content_frame, padx=20, pady=20)
    frame.pack(anchor="nw")

    tk.Label(frame, text="Reset Password", font=("Arial", 16, "bold")).grid(row=0, column=0, columnspan=2, pady=10)

    tk.Label(frame, text="User ID").grid(row=1, column=0, sticky="e", pady=5)
    user_id_entry = tk.Entry(frame, width=20)
    user_id_entry.grid(row=1, column=1, pady=5)

    tk.Label(frame, text="New Password").grid(row=2, column=0, sticky="e", pady=5)
    new_pass_entry = tk.Entry(frame, width=20, show="*")
    new_pass_entry.grid(row=2, column=1, pady=5)

    def do_reset():
        try:
            user_id = int(user_id_entry.get().strip())
        except ValueError:
            messagebox.showwarning("Input Error", "User ID must be a number")
            return

        ok = app.db.reset_password(user_id, new_pass_entry.get().strip())
        if ok:
            messagebox.showinfo("Success", "Password reset")
            app.db.add_log(
                event_type="password_reset",
                details=f"Reset password for user_id={user_id}",
                user_id=app.current_user["id"],
                username=app.current_user["username"],
            )
        else:
            messagebox.showerror("Error", "Password reset failed")

    tk.Button(frame, text="Reset", command=do_reset).grid(row=3, column=0, columnspan=2, pady=10)