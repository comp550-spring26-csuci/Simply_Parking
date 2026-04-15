import tkinter as tk
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

        self.db = DatabaseManager()
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
            messagebox.showerror("Login Failed", "Invalid username or password")
            return

        self.current_user = user
        self.show_dashboard()

    def logout(self):
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
            self.add_nav_button(nav, "Logs & Reports", self.show_logs_reports)
            self.add_nav_button(nav, "System Settings", self.show_system_settings)

        elif role == "support_agent":
            self.add_nav_button(nav, "Customer History", self.show_plate_records)
            self.add_nav_button(nav, "Manage Accounts", self.show_manage_users_readonly)
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
        tk.Button(parent, text=text, width=24, command=command).pack(pady=5, padx=10)

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

        table_frame = tk.Frame(self.content_frame, padx=10, pady=10)
        table_frame.pack(fill="both", expand=True)

        columns = ("id", "plate", "source_file", "timestamp")
        tree = ttk.Treeview(table_frame, columns=columns, show="headings")

        for col in columns:
            tree.heading(col, text=col.replace("_", " ").title())

        tree.column("id", width=60, anchor="center")
        tree.column("plate", width=150, anchor="center")
        tree.column("source_file", width=350, anchor="w")
        tree.column("timestamp", width=180, anchor="center")

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)

        tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        try:
            rows = self.db.fetch_all()
            for row in rows:
                tree.insert("", tk.END, values=row)
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

            ok = self.db.insert_plate(plate, source)
            if ok:
                messagebox.showinfo("Success", "Plate record added")
                plate_entry.delete(0, tk.END)
                source_entry.delete(0, tk.END)
            else:
                messagebox.showerror("Error", "Could not add plate")

        tk.Button(frame, text="Save", command=save).grid(row=3, column=0, columnspan=2, pady=10)

    def show_manage_users(self):
        self.clear_content()

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
            else:
                messagebox.showerror("Error", "Password reset failed")

        tk.Button(frame, text="Reset", command=do_reset).grid(row=3, column=0, columnspan=2, pady=10)

    def show_logs_reports(self):
        self.clear_content()
        tk.Label(self.content_frame, text="Logs & Reports", font=("Arial", 16, "bold")).pack(pady=20)
        tk.Label(self.content_frame, text="Placeholder for logs, access history, and reports").pack()

    def show_system_settings(self):
        self.clear_content()
        tk.Label(self.content_frame, text="System Settings", font=("Arial", 16, "bold")).pack(pady=20)
        tk.Label(self.content_frame, text="Placeholder for admin-only configuration").pack()

    def show_report_issue(self):
        self.clear_content()
        tk.Label(self.content_frame, text="Report Parking Issue", font=("Arial", 16, "bold")).pack(pady=20)
        tk.Label(self.content_frame, text="Placeholder for officer issue reporting").pack()

    def show_my_vehicle(self):
        self.clear_content()
        tk.Label(self.content_frame, text="My Vehicle", font=("Arial", 16, "bold")).pack(pady=20)
        tk.Label(self.content_frame, text="View registered semester parking vehicle").pack()

    def show_register_vehicle(self):
        self.clear_content()
        tk.Label(self.content_frame, text="Register Vehicle", font=("Arial", 16, "bold")).pack(pady=20)
        tk.Label(self.content_frame, text="Placeholder for semester user vehicle registration").pack()

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