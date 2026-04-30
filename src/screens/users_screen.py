# screens/users_screen.py

import tkinter as tk
from tkinter import ttk, messagebox

from utils.permissions import can_manage_users


def build_manage_users_screen(app):
    app.clear_content()

    if not can_manage_users(app.current_user):
        messagebox.showerror("Access Denied", "You do not have permission to manage users.")
        return

    top = tk.Frame(app.content_frame, padx=10, pady=10)
    top.pack(fill="x")

    tk.Label(top, text="Manage Users", font=("Arial", 16, "bold")).pack(side="left")

    form = tk.Frame(app.content_frame, padx=10, pady=10)
    form.pack(fill="x")

    tk.Label(form, text="Full Name").grid(row=0, column=0, sticky="e", pady=4)
    full_name_entry = tk.Entry(form, width=25)
    full_name_entry.grid(row=0, column=1, pady=4, padx=5)

    tk.Label(form, text="Username").grid(row=1, column=0, sticky="e", pady=4)
    username_entry = tk.Entry(form, width=25)
    username_entry.grid(row=1, column=1, pady=4, padx=5)

    tk.Label(form, text="Password").grid(row=2, column=0, sticky="e", pady=4)
    password_entry = tk.Entry(form, width=25, show="*")
    password_entry.grid(row=2, column=1, pady=4, padx=5)

    tk.Label(form, text="Role").grid(row=3, column=0, sticky="e", pady=4)
    role_combo = ttk.Combobox(
        form,
        width=22,
        state="readonly",
        values=[
            "admin",
            "support_agent",
            "semester_user",
            "daily_user",
            "payg_user",
        ],
    )
    role_combo.grid(row=3, column=1, pady=4, padx=5)
    role_combo.set("semester_user")

    def refresh_table():
        for item in tree.get_children():
            tree.delete(item)

        try:
            rows = app.db.fetch_users()
            for row in rows:
                tree.insert("", tk.END, values=row)
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def create_user():
        username = username_entry.get().strip()
        password = password_entry.get().strip()
        role = role_combo.get().strip()
        full_name = full_name_entry.get().strip()

        ok = app.db.create_user(username, password, role, full_name)

        if ok:
            messagebox.showinfo("Success", "User created")
            app.db.add_log(
                event_type="user_created",
                details=f"Created username={username}, role={role}",
                user_id=app.current_user["id"],
                username=app.current_user["username"],
            )
            refresh_table()
            full_name_entry.delete(0, tk.END)
            username_entry.delete(0, tk.END)
            password_entry.delete(0, tk.END)
            role_combo.set("semester_user")
        else:
            messagebox.showerror("Error", "Could not create user")

    tk.Button(form, text="Create User", command=create_user).grid(
        row=4, column=0, columnspan=2, pady=10
    )

    table_frame = tk.Frame(app.content_frame, padx=10, pady=10)
    table_frame.pack(fill="both", expand=True)

    columns = ("id", "username", "role", "full_name", "created_at")
    tree = ttk.Treeview(table_frame, columns=columns, show="headings")

    for col in columns:
        tree.heading(col, text=col.replace("_", " ").title())

    tree.column("id", width=60, anchor="center")
    tree.column("username", width=160, anchor="center")
    tree.column("role", width=160, anchor="center")
    tree.column("full_name", width=220, anchor="w")
    tree.column("created_at", width=180, anchor="center")

    tree.pack(side="left", fill="both", expand=True)

    scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=scrollbar.set)
    scrollbar.pack(side="right", fill="y")

    actions = tk.Frame(app.content_frame, padx=10, pady=5)
    actions.pack(fill="x")

    def delete_selected_user():
        if app.current_user["role"] != "admin":
            messagebox.showerror("Access Denied", "Only admins can delete users.")
            return

        selected = tree.selection()
        if not selected:
            messagebox.showwarning("Selection Error", "Select a user first.")
            return

        values = tree.item(selected[0], "values")
        if not values:
            messagebox.showwarning("Selection Error", "Invalid selection.")
            return

        user_id = int(values[0])
        username = values[1]
        role = values[2]

        if user_id == app.current_user["id"]:
            messagebox.showwarning("Action Blocked", "You cannot delete your own account.")
            return

        if username == "admin" and role == "admin":
            messagebox.showwarning("Action Blocked", "Default admin account cannot be deleted.")
            return

        confirm = messagebox.askyesno(
            "Confirm Delete",
            f"Delete user '{username}' (ID {user_id})?"
        )
        if not confirm:
            return

        ok = app.db.delete_user(user_id)
        if ok:
            app.db.add_log(
                event_type="user_deleted",
                details=f"Deleted user_id={user_id}, username={username}, role={role}",
                user_id=app.current_user["id"],
                username=app.current_user["username"],
            )
            messagebox.showinfo("Success", "User deleted.")
            app.root.after_idle(refresh_table)
        else:
            messagebox.showerror("Error", "Could not delete user.")

    if app.current_user["role"] == "admin":
        tk.Button(actions, text="Delete Selected User", command=delete_selected_user).pack(anchor="w")

    def safe_refresh():
        try:
            refresh_table()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    app.content_frame.update_idletasks()
    app.root.after_idle(safe_refresh)


def build_manage_users_readonly_screen(app):
    app.clear_content()

    tk.Label(app.content_frame, text="User Accounts", font=("Arial", 16, "bold")).pack(pady=10)

    table_frame = tk.Frame(app.content_frame, padx=10, pady=10)
    table_frame.pack(fill="both", expand=True)

    columns = ("id", "username", "role", "full_name", "created_at")
    tree = ttk.Treeview(table_frame, columns=columns, show="headings")

    for col in columns:
        tree.heading(col, text=col.replace("_", " ").title())

    tree.column("id", width=60, anchor="center")
    tree.column("username", width=160, anchor="center")
    tree.column("role", width=160, anchor="center")
    tree.column("full_name", width=220, anchor="w")
    tree.column("created_at", width=180, anchor="center")

    tree.pack(side="left", fill="both", expand=True)

    scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=scrollbar.set)
    scrollbar.pack(side="right", fill="y")

    try:
        for row in app.db.fetch_users():
            tree.insert("", tk.END, values=row)
    except Exception as e:
        messagebox.showerror("Error", str(e))