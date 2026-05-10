# notifier.py

from tkinter import messagebox

try:
    from plyer import notification
    PLYER_AVAILABLE = True
except ImportError:
    PLYER_AVAILABLE = False


class Notifier:
    def __init__(self, app_name="Parking System"):
        self.app_name = app_name

    def alert(self, title, message, popup=True, desktop=False):
        if popup:
            try:
                messagebox.showinfo(title, message)
            except Exception as e:
                print(f"Popup alert failed: {e}")

        if desktop and PLYER_AVAILABLE:
            try:
                notification.notify(
                    title=title,
                    message=message,
                    app_name=self.app_name,
                    timeout=5,
                )
            except Exception as e:
                print(f"Desktop notification failed: {e}")