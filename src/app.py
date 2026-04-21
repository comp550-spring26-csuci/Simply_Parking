import tkinter as tk
from PIL import Image, ImageTk
import os
from tkinter import ttk, messagebox
from database_manager import DatabaseManager


ROLE_LABELS = {
    "admin": "Admin",
    "support_agent": "Support Agent",
    "parking_officer": "Parking Officer",
    "semester_user": "Semester Parking User",
    "daily_user": "Daily User",
    "payg_user": "Pay As You Go User",
}


class PlateApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Parking System")
        self.root.geometry("1000x600")

        try:
            self.db = DatabaseManager()
        except Exception as e:
            messagebox.showerror("Database Error", str(e))
            self.root.after(100, self.root.destroy)
            return
        self.current_user = None

        self.main_frame = tk.Frame(self.root)
        self.main_frame.pack(fill="both", expand=True)

        self.show_login()

    def clear_main(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy()

    def show_login(self):
        self.clear_main()

        frame = tk.Frame(self.main_frame, padx=20, pady=20)
        frame.pack(expand=True)

        tk.Label(frame, text="Parking System Login", font=("Arial", 18, "bold")).grid(row=0, column=0, columnspan=2, pady=10)

        tk.Label(frame, text="Username").grid(row=1, column=0, sticky="e", pady=5)
        self.username_entry = tk.Entry(frame, width=30)
        self.username_entry.grid(row=1, column=1, pady=5)

        tk.Label(frame, text="Password").grid(row=2, column=0, sticky="e", pady=5)
        self.password_entry = tk.Entry(frame, width=30, show="*")
        self.password_entry.grid(row=2, column=1, pady=5)

        tk.Button(frame, text="Login", width=20, command=self.login).grid(row=3, column=0, columnspan=2, pady=25)
        
        # tk.Label(
        #     frame,
        #     text="Default admin: admin / admin123",
        #     fg="gray"
        # ).grid(row=4, column=0, columnspan=2)

    def login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()

        user = self.db.authenticate_user(username, password)
        if not user:
            self.db.add_log(
                event_type="login_failed",
                details="Incorrect username or password",
                username=username,
            )
            messagebox.showerror("Login Failed", "Invalid username or password")
            return

        self.current_user = user
        self.db.add_log(
            event_type="login_success",
            details=f"Role={user['role']}",
            user_id=user["id"],
            username=user["username"],
        )
        self.show_dashboard()

    def logout(self):
        if self.current_user:
            self.db.add_log(
                event_type="logout",
                details=f"Role={self.current_user['role']}",
                user_id=self.current_user["id"],
                username=self.current_user["username"],
            )

        self.current_user = None
        self.show_login()

    def show_dashboard(self):
        self.clear_main()

        top = tk.Frame(self.main_frame, padx=10, pady=10)
        top.pack(fill="x")

        role_name = ROLE_LABELS.get(self.current_user["role"], self.current_user["role"])

        tk.Label(
            top,
            text=f"Welcome, {self.current_user.get('full_name') or self.current_user['username']} ({role_name})",
            font=("Arial", 14, "bold")
        ).pack(side="left")

        tk.Button(top, text="Logout", command=self.logout).pack(side="right")

        body = tk.Frame(self.main_frame, padx=10, pady=10)
        body.pack(fill="both", expand=True)

        nav = tk.Frame(body, width=220, bd=1, relief="solid")
        nav.pack(side="left", fill="y", padx=(0, 10))

        content = tk.Frame(body, bd=1, relief="solid")
        content.pack(side="right", fill="both", expand=True)

        self.content_frame = content

        role = self.current_user["role"]

        if role == "admin":
            self.add_nav_button(nav, "Plate Records", self.show_plate_records)
            self.add_nav_button(nav, "Add Plate", self.show_add_plate)
            self.add_nav_button(nav, "Manage Users", self.show_manage_users)
            self.add_nav_button(nav, "Manage Issues", self.show_manage_issues)
            self.add_nav_button(nav, "Logs & Reports", self.show_logs_reports)
            self.add_nav_button(nav, "System Settings", self.show_system_settings)

        elif role == "support_agent":
            self.add_nav_button(nav, "Customer History", self.show_plate_records)
            self.add_nav_button(nav, "Add Plate", self.show_add_plate)
            self.add_nav_button(nav, "Manage Accounts", self.show_manage_users_readonly)
            self.add_nav_button(nav, "Manage Issues", self.show_manage_issues)
            self.add_nav_button(nav, "Reset Password", self.show_reset_password)
            self.add_nav_button(nav, "Logs", self.show_logs_reports)

        elif role == "parking_officer":
            self.add_nav_button(nav, "Monitor Parking", self.show_plate_records)
            self.add_nav_button(nav, "Report Issue", self.show_report_issue)

        elif role == "semester_user":
            self.add_nav_button(nav, "My Vehicle", self.show_my_vehicle)
            self.add_nav_button(nav, "Register Vehicle", self.show_register_vehicle)

        elif role == "daily_user":
            self.add_nav_button(nav, "Buy Daily Permit", self.show_buy_daily_permit)
            self.add_nav_button(nav, "My Daily Permit", self.show_my_daily_permit)

        elif role == "payg_user":
            self.add_nav_button(nav, "Current Session", self.show_current_session)
            self.add_nav_button(nav, "Pay On Exit", self.show_pay_exit)

        self.show_home()

    def add_nav_button(self, parent, text, command):
        tk.Button(parent, text=text, command=command).pack(pady=5, padx=20, fill="x")

    def clear_content(self):
        for widget in self.content_frame.winfo_children():
            widget.destroy()

    def show_home(self):
        self.clear_content()
        tk.Label(
            self.content_frame,
            text="Dashboard",
            font=("Arial", 18, "bold")
        ).pack(pady=20)

        tk.Label(
            self.content_frame,
            text=f"Role: {ROLE_LABELS.get(self.current_user['role'], self.current_user['role'])}"
        ).pack()

    def show_plate_records(self):
        self.clear_content()

        top = tk.Frame(self.content_frame, padx=10, pady=10)
        top.pack(fill="x")

        tk.Label(top, text="Plate Records", font=("Arial", 16, "bold")).pack(side="left")
        tk.Button(top, text="Refresh", command=self.show_plate_records).pack(side="right")

        body = tk.Frame(self.content_frame, padx=10, pady=10)
        body.pack(fill="both", expand=True)

        left_frame = tk.Frame(body)
        left_frame.pack(side="left", fill="both", expand=True)

        right_frame = tk.Frame(body, width=320, bd=1, relief="solid", padx=10, pady=10)
        right_frame.pack(side="right", fill="y")

        tk.Label(right_frame, text="Captured Plate Image", font=("Arial", 14, "bold")).pack(pady=(0, 10))

        preview_canvas = tk.Canvas(right_frame, width=420, height=260, bg="white", highlightthickness=1, highlightbackground="gray")
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

        self.preview_image_ref = None
        selected_record_id = {"value": None}

        def can_modify():
            return self.current_user and self.current_user["role"] in {"admin", "support_agent"}

        def on_row_select(event):
            selected = tree.selection()
            if not selected:
                return

            values = tree.item(selected[0], "values")
            if not values or len(values) < 4:
                return

            record_id, plate_value, image_path, _timestamp = values
            selected_record_id["value"] = record_id

            plate_edit_entry.delete(0, tk.END)
            plate_edit_entry.insert(0, plate_value)

            source_edit_entry.delete(0, tk.END)
            source_edit_entry.insert(0, image_path)

            path_label.config(text=f"Path: {image_path}")

            if not image_path or not os.path.exists(image_path):
                preview_canvas.delete("all")
                preview_canvas.create_text(210, 130, text="Image not found")
                self.preview_image_ref = None
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
                self.preview_image_ref = tk_img
            except Exception as e:
                preview_canvas.delete("all")
                preview_canvas.create_text(210, 130, text=f"Could not load image:\n{e}")
                self.preview_image_ref = None

        tree.bind("<<TreeviewSelect>>", on_row_select)

        edit_frame = tk.Frame(self.content_frame, padx=10, pady=10)
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

        def refresh_table():
            for item in tree.get_children():
                tree.delete(item)
            rows = self.db.fetch_all()
            for row in rows:
                tree.insert("", tk.END, values=row)

        def update_selected_label():
            record_id_label.config(text=str(selected_record_id["value"]) if selected_record_id["value"] else "None")

        def save_edit():
            if not can_modify():
                messagebox.showerror("Access Denied", "You do not have permission to modify plate entries.")
                return

            record_id = selected_record_id["value"]
            if not record_id:
                messagebox.showwarning("Selection Error", "Select a plate record first.")
                return

            ok = self.db.update_plate_entry(
                record_id=int(record_id),
                plate=plate_edit_entry.get().strip(),
                source_file=source_edit_entry.get().strip(),
                actor_user_id=self.current_user["id"],
                actor_username=self.current_user["username"],
            )
            if ok:
                messagebox.showinfo("Success", "Plate entry updated.")
                refresh_table()
            else:
                messagebox.showerror("Error", "Could not update plate entry.")

        def delete_selected():
            if not can_modify():
                messagebox.showerror("Access Denied", "You do not have permission to delete plate entries.")
                return

            record_id = selected_record_id["value"]
            if not record_id:
                messagebox.showwarning("Selection Error", "Select a plate record first.")
                return

            confirm = messagebox.askyesno("Confirm Delete", f"Delete plate record ID {record_id}?")
            if not confirm:
                return

            ok = self.db.delete_plate_entry(
                record_id=int(record_id),
                actor_user_id=self.current_user["id"],
                actor_username=self.current_user["username"],
            )
            if ok:
                messagebox.showinfo("Success", "Plate entry deleted.")
                selected_record_id["value"] = None
                update_selected_label()
                plate_edit_entry.delete(0, tk.END)
                source_edit_entry.delete(0, tk.END)
                preview_canvas.delete("all")
                path_label.config(text="")
                refresh_table()
            else:
                messagebox.showerror("Error", "Could not delete plate entry.")

        tk.Button(edit_frame, text="Save Changes", command=save_edit).grid(row=2, column=1, pady=10, sticky="w")
        tk.Button(edit_frame, text="Delete Row", command=delete_selected).grid(row=2, column=3, pady=10, sticky="w")

        def wrapped_on_select(event):
            on_row_select(event)
            update_selected_label()

        tree.bind("<<TreeviewSelect>>", wrapped_on_select)

        try:
            refresh_table()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def show_add_plate(self):
        self.clear_content()

        frame = tk.Frame(self.content_frame, padx=20, pady=20)
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

            ok = self.db.insert_plate(
                plate,
                source,
                actor_user_id=self.current_user["id"] if self.current_user else None,
                actor_username=self.current_user["username"] if self.current_user else None,
            )
            if ok:
                messagebox.showinfo("Success", "Plate record added")
                plate_entry.delete(0, tk.END)
                source_entry.delete(0, tk.END)
                self.show_plate_records()
            else:
                messagebox.showerror("Error", "Could not add plate")

        tk.Button(frame, text="Save", command=save).grid(row=3, column=0, columnspan=2, pady=10)

    def show_manage_users(self):
        self.clear_content()

        if self.current_user["role"] not in {"admin", "support_agent"}:
            messagebox.showerror("Access Denied", "You do not have permission to manage users.")
            return

        top = tk.Frame(self.content_frame, padx=10, pady=10)
        top.pack(fill="x")

        tk.Label(top, text="Manage Users", font=("Arial", 16, "bold")).pack(side="left")

        form = tk.Frame(self.content_frame, padx=10, pady=10)
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
                "parking_officer",
                "semester_user",
                "daily_user",
                "payg_user",
            ],
        )
        role_combo.grid(row=3, column=1, pady=4, padx=5)
        role_combo.set("semester_user")

        def create_user():
            ok = self.db.create_user(
                username_entry.get(),
                password_entry.get(),
                role_combo.get(),
                full_name_entry.get(),
            )
            if ok:
                messagebox.showinfo("Success", "User created")
                self.db.add_log(
                    event_type="user_created",
                    details=f"Created username={username_entry.get().strip()}, role={role_combo.get()}",
                    user_id=self.current_user["id"],
                    username=self.current_user["username"],
                )
                self.show_manage_users()
            else:
                messagebox.showerror("Error", "Could not create user")

        tk.Button(form, text="Create User", command=create_user).grid(row=4, column=0, columnspan=2, pady=10)

        table_frame = tk.Frame(self.content_frame, padx=10, pady=10)
        table_frame.pack(fill="both", expand=True)

        columns = ("id", "username", "role", "full_name", "created_at")
        tree = ttk.Treeview(table_frame, columns=columns, show="headings")

        for col in columns:
            tree.heading(col, text=col.replace("_", " ").title())

        tree.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

        for row in self.db.fetch_users():
            tree.insert("", tk.END, values=row)

    def show_manage_users_readonly(self):
        self.clear_content()

        tk.Label(self.content_frame, text="User Accounts", font=("Arial", 16, "bold")).pack(pady=10)

        table_frame = tk.Frame(self.content_frame, padx=10, pady=10)
        table_frame.pack(fill="both", expand=True)

        columns = ("id", "username", "role", "full_name", "created_at")
        tree = ttk.Treeview(table_frame, columns=columns, show="headings")
        for col in columns:
            tree.heading(col, text=col.replace("_", " ").title())

        tree.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

        for row in self.db.fetch_users():
            tree.insert("", tk.END, values=row)

    def show_reset_password(self):
        self.clear_content()

        frame = tk.Frame(self.content_frame, padx=20, pady=20)
        frame.pack(anchor="nw")

        tk.Label(frame, text="Reset Password", font=("Arial", 16, "bold")).grid(row=0, column=0, columnspan=2, pady=10)

        tk.Label(frame, text="User ID").grid(row=1, column=0, sticky="e", pady=5)
        user_id_entry = tk.Entry(frame, width=20)
        user_id_entry.grid(row=1, column=1, pady=5)

        tk.Label(frame, text="New Password").grid(row=2, column=0, sticky="e", pady=5)
        new_pass_entry = tk.Entry(frame, width=20, show="*")
        new_pass_entry.grid(row=2, column=1, pady=5)

        def do_reset():
            try:
                user_id = int(user_id_entry.get().strip())
            except ValueError:
                messagebox.showwarning("Input Error", "User ID must be a number")
                return

            ok = self.db.reset_password(user_id, new_pass_entry.get().strip())
            if ok:
                messagebox.showinfo("Success", "Password reset")
                self.db.add_log(
                    event_type="password_reset",
                    details=f"Reset password for user_id={user_id}",
                    user_id=self.current_user["id"],
                    username=self.current_user["username"],
                )
            else:
                messagebox.showerror("Error", "Password reset failed")

        tk.Button(frame, text="Reset", command=do_reset).grid(row=3, column=0, columnspan=2, pady=10)

    def show_logs_reports(self):
        self.clear_content()

        top = tk.Frame(self.content_frame, padx=10, pady=10)
        top.pack(fill="x")

        tk.Label(top, text="Logs & Reports", font=("Arial", 16, "bold")).pack(side="left")
        tk.Button(top, text="Refresh", command=self.show_logs_reports).pack(side="right")

        table_frame = tk.Frame(self.content_frame, padx=10, pady=10)
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
            rows = self.db.fetch_logs()
            for row in rows:
                tree.insert("", tk.END, values=row)
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def show_system_settings(self):
        self.clear_content()
        tk.Label(self.content_frame, text="System Settings", font=("Arial", 16, "bold")).pack(pady=20)
        tk.Label(self.content_frame, text="Placeholder for admin-only configuration").pack()

    def show_report_issue(self):
        self.clear_content()

        top = tk.Frame(self.content_frame, padx=10, pady=10)
        top.pack(fill="x")

        tk.Label(top, text="Report Parking Issue", font=("Arial", 16, "bold")).pack(side="left")
        tk.Button(top, text="Refresh", command=self.show_report_issue).pack(side="right")

        form_frame = tk.Frame(self.content_frame, padx=20, pady=10)
        form_frame.pack(fill="x", anchor="nw")

        tk.Label(form_frame, text="Location").grid(row=0, column=0, sticky="e", pady=5)
        location_entry = tk.Entry(form_frame, width=35)
        location_entry.grid(row=0, column=1, padx=5, pady=5)
        location_entry.insert(0, "Parking Structure A")

        tk.Label(form_frame, text="Category").grid(row=1, column=0, sticky="e", pady=5)
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

        tk.Label(form_frame, text="Priority").grid(row=2, column=0, sticky="e", pady=5)
        priority_combo = ttk.Combobox(
            form_frame,
            width=32,
            state="readonly",
            values=["Low", "Medium", "High", "Urgent"],
        )
        priority_combo.grid(row=2, column=1, padx=5, pady=5)
        priority_combo.set("Medium")

        tk.Label(form_frame, text="Description").grid(row=3, column=0, sticky="ne", pady=5)
        description_text = tk.Text(form_frame, width=45, height=5)
        description_text.grid(row=3, column=1, padx=5, pady=5)

        def submit_issue():
            location = location_entry.get().strip()
            category = category_combo.get().strip()
            priority = priority_combo.get().strip()
            description = description_text.get("1.0", tk.END).strip()

            if not location or not category or not priority or not description:
                messagebox.showwarning("Input Error", "All fields are required.")
                return

            ok = self.db.create_issue(
                user_id=self.current_user["id"],
                username=self.current_user["username"],
                location=location,
                category=category,
                priority=priority,
                description=description,
            )

            if ok:
                self.db.add_log(
                    event_type="issue_reported",
                    details=f"Location={location}, category={category}, priority={priority}",
                    user_id=self.current_user["id"],
                    username=self.current_user["username"],
                )
                messagebox.showinfo("Success", "Issue reported successfully.")
                self.show_report_issue()
            else:
                messagebox.showerror("Error", "Could not submit issue.")

        tk.Button(form_frame, text="Submit Issue", command=submit_issue).grid(row=4, column=0, columnspan=2, pady=10)

        filter_frame = tk.Frame(self.content_frame, padx=10, pady=5)
        filter_frame.pack(fill="x")

        tk.Label(filter_frame, text="View").pack(side="left")
        view_combo = ttk.Combobox(
            filter_frame,
            width=18,
            state="readonly",
            values=["My Issues", "All Issues"],
        )
        view_combo.pack(side="left", padx=8)
        view_combo.set("My Issues")

        table_frame = tk.Frame(self.content_frame, padx=10, pady=10)
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
                if view_combo.get() == "All Issues":
                    rows = self.db.fetch_issues()
                else:
                    rows = self.db.fetch_issues_by_user(self.current_user["id"])

                for row in rows:
                    tree.insert("", tk.END, values=row)
            except Exception as e:
                messagebox.showerror("Error", str(e))

        view_combo.bind("<<ComboboxSelected>>", lambda event: load_issues())

        load_issues()

    def show_my_vehicle(self):
        self.clear_content()

        top = tk.Frame(self.content_frame, padx=10, pady=10)
        top.pack(fill="x")

        tk.Label(top, text="My Vehicles", font=("Arial", 16, "bold")).pack(side="left")
        tk.Button(top, text="Refresh", command=self.show_my_vehicle).pack(side="right")

        table_frame = tk.Frame(self.content_frame, padx=10, pady=10)
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

        button_frame = tk.Frame(self.content_frame, padx=10, pady=5)
        button_frame.pack(fill="x")

        def delete_selected():
            selected = tree.selection()
            if not selected:
                messagebox.showwarning("Selection Error", "Select a vehicle to delete.")
                return

            values = tree.item(selected[0], "values")
            vehicle_id = values[0]

            ok = self.db.delete_vehicle(vehicle_id, self.current_user["id"])
            if ok:
                messagebox.showinfo("Success", "Vehicle deleted.")
                self.show_my_vehicle()
                self.db.add_log(
                    event_type="vehicle_deleted",
                    details=f"Vehicle ID={vehicle_id}",
                    user_id=self.current_user["id"],
                    username=self.current_user["username"],
                )
            else:
                messagebox.showerror("Error", "Could not delete vehicle.")

        tk.Button(button_frame, text="Delete Selected Vehicle", command=delete_selected).pack(anchor="w")

        try:
            rows = self.db.fetch_user_vehicles(self.current_user["id"])
            for row in rows:
                tree.insert("", tk.END, values=row)
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def show_register_vehicle(self):
        self.clear_content()

        frame = tk.Frame(self.content_frame, padx=20, pady=20)
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

            ok = self.db.register_vehicle(
                self.current_user["id"],
                plate,
                make,
                model,
                color,
            )

            if ok:
                messagebox.showinfo("Success", "Vehicle registered.")
                self.show_my_vehicle()
                self.db.add_log(
                    event_type="vehicle_registered",
                    details=f"Plate={plate}, make={make}, model={model}, color={color}",
                    user_id=self.current_user["id"],
                    username=self.current_user["username"],
                )
            else:
                messagebox.showerror("Error", "Could not register vehicle. It may already exist.")

        tk.Button(frame, text="Register Vehicle", command=save_vehicle).grid(row=5, column=0, columnspan=2, pady=10)

    def show_buy_daily_permit(self):
        self.clear_content()
        tk.Label(self.content_frame, text="Buy Daily Permit", font=("Arial", 16, "bold")).pack(pady=20)
        tk.Label(self.content_frame, text="Placeholder for daily permit purchase").pack()

    def show_my_daily_permit(self):
        self.clear_content()
        tk.Label(self.content_frame, text="My Daily Permit", font=("Arial", 16, "bold")).pack(pady=20)
        tk.Label(self.content_frame, text="Placeholder for today's permit view").pack()

    def show_current_session(self):
        self.clear_content()
        tk.Label(self.content_frame, text="Current Parking Session", font=("Arial", 16, "bold")).pack(pady=20)
        tk.Label(self.content_frame, text="Placeholder for pay-as-you-go session tracking").pack()

    def show_manage_issues(self):
        self.clear_content()

        if self.current_user["role"] not in {"admin", "support_agent"}:
            messagebox.showerror("Access Denied", "You do not have permission to manage issues.")
            return

        top = tk.Frame(self.content_frame, padx=10, pady=10)
        top.pack(fill="x")

        tk.Label(top, text="Manage Issues", font=("Arial", 16, "bold")).pack(side="left")
        tk.Button(top, text="Refresh", command=self.show_manage_issues).pack(side="right")

        table_frame = tk.Frame(self.content_frame, padx=10, pady=10)
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

        controls = tk.Frame(self.content_frame, padx=10, pady=10)
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
            rows = self.db.fetch_issues()
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

            ok = self.db.update_issue_status(int(issue_id), new_status)
            if ok:
                self.db.add_log(
                    event_type="issue_status_updated",
                    details=f"Issue ID={issue_id}, new_status={new_status}",
                    user_id=self.current_user["id"],
                    username=self.current_user["username"],
                )
                messagebox.showinfo("Success", "Issue status updated.")
                refresh_table()
            else:
                messagebox.showerror("Error", "Could not update issue status.")

        tk.Button(controls, text="Update Status", command=update_status).grid(row=0, column=4, padx=10, pady=4)

        tree.bind("<<TreeviewSelect>>", on_row_select)

        try:
            refresh_table()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def show_pay_exit(self):
        self.clear_content()
        tk.Label(self.content_frame, text="Pay On Exit", font=("Arial", 16, "bold")).pack(pady=20)
        tk.Label(self.content_frame, text="Placeholder for duration-based exit payment").pack()

    def on_close(self):
        self.db.close()
        self.root.destroy()


if __name__ == "__main__":
    print("Starting GUI...")
    root = tk.Tk()
    root.lift()
    root.attributes("-topmost", True)
    root.after(200, lambda: root.attributes("-topmost", False))
    app = PlateApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()