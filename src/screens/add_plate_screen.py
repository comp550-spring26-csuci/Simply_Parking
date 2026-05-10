import tkinter as tk
from tkinter import messagebox

def build_add_plate_screen(app):
    frame = tk.Frame(app.content_frame, padx=20, pady=20)
    frame.pack(anchor="nw")

    tk.Label(frame, text="Add Plate Record", font=("Arial", 16, "bold")).grid(row=0, column=0, columnspan=2, pady=10)

    tk.Label(frame, text="License Plate").grid(row=1, column=0, sticky="e", pady=5)
    plate_entry = tk.Entry(frame, width=30)
    plate_entry.grid(row=1, column=1, pady=5)

    tk.Label(frame, text="Source File").grid(row=2, column=0, sticky="e", pady=5)
    source_entry = tk.Entry(frame, width=30)
    source_entry.grid(row=2, column=1, pady=5)

    def save():
        plate = plate_entry.get().strip()
        source = source_entry.get().strip()

        if not plate:
            messagebox.showwarning("Input Error", "License plate is required")
            return

        ok = app.db.insert_plate(
            plate,
            source,
            actor_user_id=app.current_user["id"] if app.current_user else None,
            actor_username=app.current_user["username"] if app.current_user else None,
        )
        if ok:
            messagebox.showinfo("Success", "Plate record added")
            plate_entry.delete(0, tk.END)
            source_entry.delete(0, tk.END)
            app.show_plate_records()
        else:
            messagebox.showerror("Error", "Could not add plate")

    tk.Button(frame, text="Save", command=save).grid(row=3, column=0, columnspan=2, pady=10)