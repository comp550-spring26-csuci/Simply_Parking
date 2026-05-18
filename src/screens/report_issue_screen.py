import tkinter as tk
from tkinter import ttk, messagebox

#from Simply_Parking import app

def build_report_issue_screen(app):
    app.clear_content()
    # helps match the color scheme of other screens, 
    top = tk.Frame(app.content_frame, bg=app.COLORS["bg"], padx=10, pady=10)
    top.pack(fill="x")
    # aded bg and fg to match color scheme
    tk.Label(top, text="Report Parking Issue", font=("Arial", 16, "bold"), bg=app.COLORS["bg"], fg=app.COLORS["text"]).pack(side="left")
    tk.Button(top, text="Refresh", command=app.show_report_issue, bg=app.COLORS["bg"], fg=app.COLORS["text"]).pack(side="right")

    form_frame = tk.Frame(app.content_frame, bg=app.COLORS["bg"], padx=20, pady=10)
    form_frame.pack(fill="x", anchor="nw")
    # added bg and fg to match color scheme
    tk.Label(form_frame, text="Location", bg=app.COLORS["bg"], fg=app.COLORS["text"]).grid(row=0, column=0, sticky="e", pady=5)
    location_entry = tk.Entry(form_frame, width=35)
    location_entry.grid(row=0, column=1, padx=5, pady=5)
    location_entry.insert(0, "Parking Structure A")
    # added bg and fg to match color scheme
    tk.Label(form_frame, text="Category", bg=app.COLORS["bg"], fg=app.COLORS["text"]).grid(row=1, column=0, sticky="e", pady=5)
    category_combo = ttk.Combobox(
        form_frame,
        width=32,
        state="readonly",
        values=[
            "Broken Gate",
            "Lighting Issue",
            "Blocked Space",
            "Unauthorized Vehicle",
            "Damaged Signage",
            "Safety Hazard",
            "Other",
        ],
    )
    category_combo.grid(row=1, column=1, padx=5, pady=5)
    category_combo.set("Broken Gate")

    tk.Label(
        form_frame,
        text="Priority",
        bg=app.COLORS["bg"],
        fg=app.COLORS["text"]
    ).grid(row=2, column=0, sticky="e", pady=5)
    priority_combo = ttk.Combobox(
        form_frame,
        width=32,
        state="readonly",
        values=["Low", "Medium", "High", "Urgent"],
    )
    priority_combo.grid(row=2, column=1, padx=5, pady=5)
    priority_combo.set("Medium")

    tk.Label(
        form_frame,
        text="Description",
        bg=app.COLORS["bg"],
        fg=app.COLORS["text"]
    ).grid(row=3, column=0, sticky="ne", pady=5)

    description_text = tk.Text(
        form_frame,
        width=45,
        height=5,
        bg="white",
        fg=app.COLORS["text"],
        insertbackground=app.COLORS["text"],
        relief="solid",
        bd=1
    )
    description_text.grid(row=3, column=1, padx=5, pady=5)



    def submit_issue():
        location = location_entry.get().strip()
        category = category_combo.get().strip()
        priority = priority_combo.get().strip()
        description = description_text.get("1.0", tk.END).strip()

        if not location or not category or not priority or not description:
            messagebox.showwarning("Input Error", "All fields are required.")
            return

        ok = app.db.create_issue(
            user_id=app.current_user["id"],
            username=app.current_user["username"],
            location=location,
            category=category,
            priority=priority,
            description=description,
        )

        if ok:
            app.db.add_log(
                event_type="issue_reported",
                details=f"Location={location}, category={category}, priority={priority}",
                user_id=app.current_user["id"],
                username=app.current_user["username"],
            )

            # optional, if you added notifications
            if hasattr(app.db, "create_notification"):
                app.db.create_notification(
                    title="New Issue Reported",
                    message=f"{category} at {location} ({priority})",
                    notification_type="issue",
                    user_id=None,
                )

            messagebox.showinfo("Success", "Issue reported successfully.")
            app.show_report_issue()
        else:
            messagebox.showerror("Error", "Could not submit issue.")

    tk.Button(form_frame, text="Submit Issue", command=submit_issue).grid(
        row=4, column=0, columnspan=2, pady=10
    )

    filter_frame = tk.Frame(app.content_frame, bg=app.COLORS["bg"], padx=10, pady=5)
    filter_frame.pack(fill="x")

    tk.Label(filter_frame, text="View", bg=app.COLORS["bg"], fg=app.COLORS["text"]).pack(side="left")

    role = app.current_user["role"]
    can_view_all = role in {"admin", "support_agent"}

    view_options = ["My Issues", "All Issues"] if can_view_all else ["My Issues"]

    view_combo = ttk.Combobox(
        filter_frame,
        width=18,
        state="readonly",
        values=view_options,
    )
    view_combo.pack(side="left", padx=8)
    view_combo.set("My Issues")

    table_frame = tk.Frame(app.content_frame, bg=app.COLORS["bg"], padx=10, pady=10)
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
    tree.column("status", width=90, anchor="center")
    tree.column("description", width=280, anchor="w")
    tree.column("created_at", width=160, anchor="center")

    scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=scrollbar.set)

    tree.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    def load_issues():
        for item in tree.get_children():
            tree.delete(item)

        try:
            if can_view_all and view_combo.get() == "All Issues":
                rows = app.db.fetch_issues()
            else:
                rows = app.db.fetch_issues_by_user(app.current_user["id"])

            for row in rows:
                issue_id, _creator_id, reported_by, location, category, priority, status, description, created_at = row

                tree.insert("",tk.END,values=(
                        issue_id,
                        reported_by,
                        location,
                        category,
                        priority,
                        status,
                        description,
                        created_at,
                    ),
                )
        except Exception as e:
            messagebox.showerror("Error", str(e))

    view_combo.bind("<<ComboboxSelected>>", lambda event: load_issues())

    app.root.after_idle(load_issues)
