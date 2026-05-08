import tkinter as tk
from tkinter import ttk


def build_active_sessions_screen(app):
    app.clear_content()

    top = tk.Frame(app.content_frame, padx=10, pady=10)
    top.pack(fill="x")

    tk.Label(
        top,
        text="Active Parking Sessions",
        font=("Arial", 16, "bold")
    ).pack(side="left")

    tk.Button(
        top,
        text="Refresh",
        command=app.show_active_sessions
    ).pack(side="right")

    table_frame = tk.Frame(app.content_frame, padx=10, pady=10)
    table_frame.pack(fill="both", expand=True)

    columns = ("id", "plate", "entry_time", "duration", "status", "amount_due")
    tree = ttk.Treeview(table_frame, columns=columns, show="headings")

    headings = {
        "id": "ID",
        "plate": "Plate",
        "entry_time": "Entry Time",
        "duration": "Duration",
        "status": "Status",
        "amount_due": "Amount Due",
    }

    for col in columns:
        tree.heading(col, text=headings[col])

    tree.column("id", width=60, anchor="center")
    tree.column("plate", width=120, anchor="center")
    tree.column("entry_time", width=180, anchor="center")
    tree.column("duration", width=140, anchor="center")
    tree.column("status", width=120, anchor="center")
    tree.column("amount_due", width=120, anchor="center")

    scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=scrollbar.set)

    tree.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    # TODO:
    # rows = app.db.fetch_active_sessions()
    # for row in rows:
    #     tree.insert("", tk.END, values=row)