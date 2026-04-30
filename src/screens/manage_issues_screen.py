# screens/manage_issues_screen.py

import tkinter as tk
from tkinter import ttk, messagebox

from utils.permissions import can_manage_issues


def build_manage_issues_screen(app):
    app.clear_content()

    if not can_manage_issues(app.current_user):
        messagebox.showerror("Access Denied", "You do not have permission to manage issues.")
        return

    top = tk.Frame(app.content_frame, padx=10, pady=10)
    top.pack(fill="x")

    tk.Label(top, text="Manage Issues", font=("Arial", 16, "bold")).pack(side="left")
    tk.Button(top, text="Refresh", command=app.show_manage_issues).pack(side="right")

    table_frame = tk.Frame(app.content_frame, padx=10, pady=10)
    table_frame.pack(fill="both", expand=True)

    columns = ("id", "reported_by", "location", "category", "priority", "status", "description", "created_at")
    tree = ttk.Treeview(table_frame, columns=columns, show="headings")

    headings = {
        "id": "ID",
        "reported_by": "Reported By",
        "location": "Location",
        "category": "Category",
        "priority": "Priority",
        "status": "Status",
        "description": "Description",
        "created_at": "Created At",
    }

    for col in columns:
        tree.heading(col, text=headings[col])

    tree.column("id", width=50, anchor="center")
    tree.column("reported_by", width=110, anchor="center")
    tree.column("location", width=140, anchor="center")
    tree.column("category", width=130, anchor="center")
    tree.column("priority", width=90, anchor="center")
    tree.column("status", width=100, anchor="center")
    tree.column("description", width=280, anchor="w")
    tree.column("created_at", width=160, anchor="center")

    scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=scrollbar.set)

    tree.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    controls = tk.Frame(app.content_frame, padx=10, pady=10)
    controls.pack(fill="x")

    tk.Label(controls, text="Selected Issue ID").grid(row=0, column=0, sticky="e", pady=4)
    issue_id_label = tk.Label(controls, text="None", width=10, anchor="w")
    issue_id_label.grid(row=0, column=1, sticky="w", padx=5)

    tk.Label(controls, text="New Status").grid(row=0, column=2, sticky="e", pady=4)
    status_combo = ttk.Combobox(
        controls,
        width=20,
        state="readonly",
        values=["Open", "In Progress", "Resolved"],
    )
    status_combo.grid(row=0, column=3, padx=5, pady=4)
    status_combo.set("Open")

    selected_issue_id = {"value": None}

    def refresh_table():
        for item in tree.get_children():
            tree.delete(item)

        rows = app.db.fetch_issues()
        for row in rows:
            tree.insert("", tk.END, values=row)

    def on_row_select(event):
        selected = tree.selection()
        if not selected:
            return

        values = tree.item(selected[0], "values")
        if not values:
            return

        issue_id = values[0]
        current_status = values[5]

        selected_issue_id["value"] = issue_id
        issue_id_label.config(text=str(issue_id))
        status_combo.set(current_status)

    def update_status():
        issue_id = selected_issue_id["value"]
        new_status = status_combo.get().strip()

        if not issue_id:
            messagebox.showwarning("Selection Error", "Select an issue first.")
            return

        ok = app.db.update_issue_status(int(issue_id), new_status)
        if ok:
            app.db.add_log(
                event_type="issue_status_updated",
                details=f"Issue ID={issue_id}, new_status={new_status}",
                user_id=app.current_user["id"],
                username=app.current_user["username"],
            )
            messagebox.showinfo("Success", "Issue status updated.")
            app.root.after_idle(refresh_table)
        else:
            messagebox.showerror("Error", "Could not update issue status.")

    tk.Button(controls, text="Update Status", command=update_status).grid(
        row=0, column=4, padx=10, pady=4
    )

    tree.bind("<<TreeviewSelect>>", on_row_select)

    try:
        app.root.after_idle(refresh_table)
    except Exception as e:
        messagebox.showerror("Error", str(e))