# screens/plate_records_screen.py

import os
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk

from utils.permissions import can_modify_plates


def build_plate_records_screen(app):
    top = tk.Frame(app.content_frame, padx=10, pady=10)
    top.pack(fill="x")

    tk.Label(top, text="Plate Records", font=("Arial", 16, "bold")).pack(side="left")
    tk.Button(top, text="Refresh", command=app.show_plate_records).pack(side="right")

    body = tk.Frame(app.content_frame, padx=10, pady=10)
    body.pack(fill="both", expand=True)

    left_frame = tk.Frame(body)
    left_frame.pack(side="left", fill="both", expand=True)

    right_frame = tk.Frame(body, width=320, bd=1, relief="solid", padx=10, pady=10)
    right_frame.pack(side="right", fill="y")

    tk.Label(
        right_frame,
        text="Captured Plate Image",
        font=("Arial", 14, "bold")
    ).pack(pady=(0, 10))

    preview_canvas = tk.Canvas(
        right_frame,
        width=420,
        height=260,
        bg="white",
        highlightthickness=1,
        highlightbackground="gray"
    )
    preview_canvas.pack(pady=5)

    path_label = tk.Label(right_frame, text="", wraplength=280, justify="left")
    path_label.pack(pady=10)

    columns = ("id", "plate", "source_file", "timestamp")
    tree = ttk.Treeview(left_frame, columns=columns, show="headings")

    for col in columns:
        tree.heading(col, text=col.replace("_", " ").title())

    tree.column("id", width=60, anchor="center")
    tree.column("plate", width=120, anchor="center")
    tree.column("source_file", width=260, anchor="w")
    tree.column("timestamp", width=180, anchor="center")

    scrollbar = ttk.Scrollbar(left_frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=scrollbar.set)

    tree.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    app.preview_image_ref = None
    selected_record_id = {"value": None}

    edit_frame = tk.Frame(app.content_frame, padx=10, pady=10)
    edit_frame.pack(fill="x")

    tk.Label(edit_frame, text="Selected Record ID").grid(row=0, column=0, sticky="e", pady=4)
    record_id_label = tk.Label(edit_frame, text="None", width=12, anchor="w")
    record_id_label.grid(row=0, column=1, sticky="w", padx=5)

    tk.Label(edit_frame, text="Plate").grid(row=1, column=0, sticky="e", pady=4)
    plate_edit_entry = tk.Entry(edit_frame, width=25)
    plate_edit_entry.grid(row=1, column=1, padx=5, pady=4)

    tk.Label(edit_frame, text="Source File").grid(row=1, column=2, sticky="e", pady=4)
    source_edit_entry = tk.Entry(edit_frame, width=45)
    source_edit_entry.grid(row=1, column=3, padx=5, pady=4)

    def update_selected_label():
        record_id_label.config(
            text=str(selected_record_id["value"]) if selected_record_id["value"] else "None"
        )

    def refresh_table():
        for item in tree.get_children():
            tree.delete(item)

        try:
            rows = app.db.fetch_all()
            for row in rows:
                tree.insert("", tk.END, values=row)
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def clear_preview():
        preview_canvas.delete("all")
        path_label.config(text="")
        app.preview_image_ref = None

    def on_row_select(event):
        selected = tree.selection()
        if not selected:
            return

        values = tree.item(selected[0], "values")
        if not values or len(values) < 4:
            return

        record_id, plate_value, image_path, _timestamp = values
        selected_record_id["value"] = record_id
        update_selected_label()

        plate_edit_entry.delete(0, tk.END)
        plate_edit_entry.insert(0, plate_value)

        source_edit_entry.delete(0, tk.END)
        source_edit_entry.insert(0, image_path)

        path_label.config(text=f"Path: {image_path}")

        if not image_path or not os.path.exists(image_path):
            preview_canvas.delete("all")
            preview_canvas.create_text(210, 130, text="Image not found")
            app.preview_image_ref = None
            return

        try:
            img = Image.open(image_path)
            img.thumbnail((420, 260))
            tk_img = ImageTk.PhotoImage(img)

            preview_canvas.delete("all")

            canvas_w = 420
            canvas_h = 260
            img_w = tk_img.width()
            img_h = tk_img.height()

            x = (canvas_w - img_w) // 2
            y = (canvas_h - img_h) // 2

            preview_canvas.create_image(x, y, anchor="nw", image=tk_img)
            app.preview_image_ref = tk_img
        except Exception as e:
            preview_canvas.delete("all")
            preview_canvas.create_text(210, 130, text=f"Could not load image:\n{e}")
            app.preview_image_ref = None

    def save_edit():
        if not can_modify_plates(app.current_user):
            messagebox.showerror(
                "Access Denied",
                "You do not have permission to modify plate entries."
            )
            return

        record_id = selected_record_id["value"]
        if not record_id:
            messagebox.showwarning("Selection Error", "Select a plate record first.")
            return

        ok = app.db.update_plate_entry(
            record_id=int(record_id),
            plate=plate_edit_entry.get().strip(),
            source_file=source_edit_entry.get().strip(),
            actor_user_id=app.current_user["id"],
            actor_username=app.current_user["username"],
        )

        if ok:
            messagebox.showinfo("Success", "Plate entry updated.")
            app.root.after_idle(refresh_table)
        else:
            messagebox.showerror("Error", "Could not update plate entry.")

    def delete_selected():
        if not can_modify_plates(app.current_user):
            messagebox.showerror(
                "Access Denied",
                "You do not have permission to delete plate entries."
            )
            return

        record_id = selected_record_id["value"]
        if not record_id:
            messagebox.showwarning("Selection Error", "Select a plate record first.")
            return

        confirm = messagebox.askyesno(
            "Confirm Delete",
            f"Delete plate record ID {record_id}?"
        )
        if not confirm:
            return

        ok = app.db.delete_plate_entry(
            record_id=int(record_id),
            actor_user_id=app.current_user["id"],
            actor_username=app.current_user["username"],
        )

        if ok:
            messagebox.showinfo("Success", "Plate entry deleted.")
            selected_record_id["value"] = None
            update_selected_label()

            plate_edit_entry.delete(0, tk.END)
            source_edit_entry.delete(0, tk.END)
            clear_preview()
            app.root.after_idle(refresh_table)
        else:
            messagebox.showerror("Error", "Could not delete plate entry.")

    tk.Button(edit_frame, text="Save Changes", command=save_edit).grid(
        row=2, column=1, pady=10, sticky="w"
    )
    tk.Button(edit_frame, text="Delete Row", command=delete_selected).grid(
        row=2, column=3, pady=10, sticky="w"
    )

    tree.bind("<<TreeviewSelect>>", on_row_select)

    def safe_refresh():
        try:
            refresh_table()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    app.content_frame.update_idletasks()
    app.root.after_idle(safe_refresh)