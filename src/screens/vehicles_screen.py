import tkinter as tk
from tkinter import ttk, messagebox

def build_my_vehicle_screen(app):
    app.clear_content()

    top = tk.Frame(app.content_frame, padx=10, pady=10)
    top.pack(fill="x")

    tk.Label(top, text="My Vehicles", font=("Arial", 16, "bold")).pack(side="left")
    tk.Button(top, text="Refresh", command=app.show_my_vehicle).pack(side="right")

    table_frame = tk.Frame(app.content_frame, padx=10, pady=10)
    table_frame.pack(fill="both", expand=True)

    columns = ("id", "plate", "make", "model", "color", "created_at")
    tree = ttk.Treeview(table_frame, columns=columns, show="headings")

    for col in columns:
        tree.heading(col, text=col.replace("_", " ").title())

    tree.column("id", width=60, anchor="center")
    tree.column("plate", width=120, anchor="center")
    tree.column("make", width=140, anchor="center")
    tree.column("model", width=140, anchor="center")
    tree.column("color", width=100, anchor="center")
    tree.column("created_at", width=180, anchor="center")

    scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=scrollbar.set)

    tree.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    button_frame = tk.Frame(app.content_frame, padx=10, pady=5)
    button_frame.pack(fill="x")

    def delete_selected():
        selected = tree.selection()
        if not selected:
            messagebox.showwarning("Selection Error", "Select a vehicle to delete.")
            return

        values = tree.item(selected[0], "values")
        vehicle_id = values[0]

        ok = app.db.delete_vehicle(vehicle_id, app.current_user["id"])
        if ok:
            messagebox.showinfo("Success", "Vehicle deleted.")
            app.show_my_vehicle()
            app.db.add_log(
                event_type="vehicle_deleted",
                details=f"Vehicle ID={vehicle_id}",
                user_id=app.current_user["id"],
                username=app.current_user["username"],
            )
        else:
            messagebox.showerror("Error", "Could not delete vehicle.")

    tk.Button(button_frame, text="Delete Selected Vehicle", command=delete_selected).pack(anchor="w")

    try:
        rows = app.db.fetch_user_vehicles(app.current_user["id"])
        for row in rows:
            tree.insert("", tk.END, values=row)
    except Exception as e:
        messagebox.showerror("Error", str(e))

def build_register_vehicle_screen(app):
    app.clear_content()

    frame = tk.Frame(app.content_frame, padx=20, pady=20)
    frame.pack(anchor="nw")

    tk.Label(frame, text="Register Vehicle", font=("Arial", 16, "bold")).grid(row=0, column=0, columnspan=2, pady=10)

    tk.Label(frame, text="License Plate").grid(row=1, column=0, sticky="e", pady=5)
    plate_entry = tk.Entry(frame, width=30)
    plate_entry.grid(row=1, column=1, pady=5)

    tk.Label(frame, text="Make").grid(row=2, column=0, sticky="e", pady=5)
    make_entry = tk.Entry(frame, width=30)
    make_entry.grid(row=2, column=1, pady=5)

    tk.Label(frame, text="Model").grid(row=3, column=0, sticky="e", pady=5)
    model_entry = tk.Entry(frame, width=30)
    model_entry.grid(row=3, column=1, pady=5)

    tk.Label(frame, text="Color").grid(row=4, column=0, sticky="e", pady=5)
    color_entry = tk.Entry(frame, width=30)
    color_entry.grid(row=4, column=1, pady=5)

    def save_vehicle():
        plate = plate_entry.get().strip()
        make = make_entry.get().strip()
        model = model_entry.get().strip()
        color = color_entry.get().strip()

        if not plate:
            messagebox.showwarning("Input Error", "License plate is required.")
            return

        ok = app.db.register_vehicle(
            app.current_user["id"],
            plate,
            make,
            model,
            color,
        )

        if ok:
            messagebox.showinfo("Success", "Vehicle registered.")
            app.show_my_vehicle()
            app.db.add_log(
                event_type="vehicle_registered",
                details=f"Plate={plate}, make={make}, model={model}, color={color}",
                user_id=app.current_user["id"],
                username=app.current_user["username"],
            )
        else:
            messagebox.showerror("Error", "Could not register vehicle. It may already exist.")

    tk.Button(frame, text="Register Vehicle", command=save_vehicle).grid(row=5, column=0, columnspan=2, pady=10)