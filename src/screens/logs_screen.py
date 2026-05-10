import tkinter as tk
from tkinter import ttk, messagebox

def build_logs_screen(app):
        app.clear_content()

        top = tk.Frame(app.content_frame, padx=10, pady=10)
        top.pack(fill="x")

        tk.Label(top, text="Logs & Reports", font=("Arial", 16, "bold")).pack(side="left")
        tk.Button(top, text="Refresh", command=app.show_logs_reports).pack(side="right")

        table_frame = tk.Frame(app.content_frame, padx=10, pady=10)
        table_frame.pack(fill="both", expand=True)

        columns = ("id", "username", "event_type", "details", "created_at")
        tree = ttk.Treeview(table_frame, columns=columns, show="headings")

        for col in columns:
            tree.heading(col, text=col.replace("_", " ").title())

        tree.column("id", width=60, anchor="center")
        tree.column("username", width=140, anchor="center")
        tree.column("event_type", width=160, anchor="center")
        tree.column("details", width=420, anchor="w")
        tree.column("created_at", width=180, anchor="center")

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)

        tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        try:
            rows = app.db.fetch_logs()
            for row in rows:
                tree.insert("", tk.END, values=row)
        except Exception as e:
            messagebox.showerror("Error", str(e))