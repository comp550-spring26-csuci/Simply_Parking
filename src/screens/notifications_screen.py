# screens/notifications_screen.py

import tkinter as tk
from tkinter import ttk, messagebox


def build_notifications_screen(app):
    app.clear_content()

    top = tk.Frame(app.content_frame, padx=10, pady=10)
    top.pack(fill="x")

    tk.Label(top, text="Notifications", font=("Arial", 16, "bold")).pack(side="left")
    tk.Button(top, text="Refresh", command=app.show_notifications).pack(side="right")

    actions = tk.Frame(app.content_frame, padx=10, pady=5)
    actions.pack(fill="x")

    def mark_all_read():
        user_id = app.current_user["id"] if app.current_user else None
        ok = app.db.mark_all_notifications_read(user_id=user_id)
        if ok:
            app.refresh_notification_badge()
            app.show_notifications()
        else:
            messagebox.showerror("Error", "Could not mark notifications as read.")

    tk.Button(actions, text="Mark All Read", command=mark_all_read).pack(side="left")

    table_frame = tk.Frame(app.content_frame, padx=10, pady=10)
    table_frame.pack(fill="both", expand=True)

    columns = ("id", "title", "message", "type", "is_read", "created_at")
    tree = ttk.Treeview(table_frame, columns=columns, show="headings")

    headings = {
        "id": "ID",
        "title": "Title",
        "message": "Message",
        "type": "Type",
        "is_read": "Read",
        "created_at": "Created",
    }

    for col in columns:
        tree.heading(col, text=headings[col])

    tree.column("id", width=45, minwidth=45, anchor="center", stretch=False)
    tree.column("title", width=150, minwidth=120, anchor="w", stretch=False)
    tree.column("message", width=360, minwidth=220, anchor="w", stretch=True)
    tree.column("type", width=90, minwidth=80, anchor="center", stretch=False)
    tree.column("is_read", width=70, minwidth=60, anchor="center", stretch=False)
    tree.column("created_at", width=150, minwidth=130, anchor="center", stretch=False)

    scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=scrollbar.set)

    tree.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    def shorten(text, max_len=45):
        text = str(text)
        return text if len(text) <= max_len else text[:max_len - 3] + "..."

    def refresh_table():
        for item in tree.get_children():
            tree.delete(item)

        user_id = app.current_user["id"] if app.current_user else None
        rows = app.db.fetch_notifications(user_id=user_id)

        for row in rows:
            notification_id, _user_id, title, message, notification_type, is_read, created_at = row
            tree.insert(
                "",
                tk.END,
                values=(
                    notification_id,
                    shorten(title, 20),
                    shorten(message, 45),
                    notification_type,
                    "Yes" if is_read else "No",
                    str(created_at)[:16],
                ),
            )

    def mark_selected_read():
        selected = tree.selection()
        if not selected:
            messagebox.showwarning("Selection Error", "Select a notification first.")
            return

        values = tree.item(selected[0], "values")
        notification_id = values[0]

        ok = app.db.mark_notification_read(int(notification_id))
        if ok:
            app.refresh_notification_badge()
            refresh_table()
        else:
            messagebox.showerror("Error", "Could not mark notification as read.")

    tk.Button(actions, text="Mark Selected Read", command=mark_selected_read).pack(side="left", padx=10)

    try:
        refresh_table()
    except Exception as e:
        messagebox.showerror("Error", str(e))