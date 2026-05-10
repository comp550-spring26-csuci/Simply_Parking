import tkinter as tk


def build_admin_dashboard_screen(app):
    app.clear_content()

    tk.Label(
        app.content_frame,
        text="Admin Dashboard",
        font=("Arial", 16, "bold")
    ).pack(pady=20)

    tk.Label(
        app.content_frame,
        text="Placeholder for revenue totals, active sessions, permit counts, and issue metrics."
    ).pack(pady=10)

    # TODO:
    # - total daily permit revenue
    # - total PAYG revenue
    # - active parking sessions count
    # - open issues count
    # - registered users count