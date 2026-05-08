import tkinter as tk
from tkinter import ttk


def build_payment_history_screen(app):
    app.clear_content()

    top = tk.Frame(app.content_frame, padx=10, pady=10)
    top.pack(fill="x")

    tk.Label(top,text="Payment History",font=("Arial", 16, "bold")).pack(side="left")

    tk.Button(top,text="Refresh",command=app.show_payment_history).pack(side="right")

    table_frame = tk.Frame(app.content_frame, padx=10, pady=10)
    table_frame.pack(fill="both", expand=True)

    columns = ("id", "plate", "payment_type", "amount", "created_at")
    tree = ttk.Treeview(table_frame, columns=columns, show="headings")

    headings = {
        "id": "ID",
        "plate": "Plate",
        "payment_type": "Type",
        "amount": "Amount",
        "created_at": "Date",
    }

    for col in columns:
        tree.heading(col, text=headings[col])

    tree.column("id", width=60, anchor="center")
    tree.column("plate", width=120, anchor="center")
    tree.column("payment_type", width=160, anchor="center")
    tree.column("amount", width=100, anchor="center")
    tree.column("created_at", width=180, anchor="center")

    scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=scrollbar.set)

    tree.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    # TODO:
    # rows = app.db.fetch_payment_history(app.current_user["id"])
    # for row in rows:
    #     tree.insert("", tk.END, values=row)