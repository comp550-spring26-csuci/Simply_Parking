import tkinter as tk

BG = "#F7F7F7"
CARD_BG = "#FFFFFF"
PRIMARY = "#C8102E"
PRIMARY_DARK = "#A00D25"
TEXT = "#1F1F1F"
MUTED = "#6B7280"
BORDER = "#D9D9D9"


def styled_entry(parent, show=None):
    return tk.Entry(
        parent,
        width=32,
        show=show,
        bg="white",
        fg=TEXT,
        insertbackground=TEXT,
        relief="solid",
        bd=1,
        highlightthickness=2,
        highlightbackground=BORDER,
        highlightcolor=PRIMARY,
        font=("Arial", 13),
    )


def build_login_screen(app):
    app.main_frame.configure(bg=BG)

    outer = tk.Frame(app.main_frame, bg=BG)
    outer.pack(expand=True)

    card = tk.Frame(
        outer,
        bg=CARD_BG,
        padx=38,
        pady=32,
        highlightbackground=BORDER,
        highlightthickness=1,
    )
    card.pack()

    tk.Label(
        card,
        text="SP",
        font=("Arial", 36),
        bg=CARD_BG,
        fg=PRIMARY,
    ).grid(row=0, column=0, columnspan=2, pady=(0, 8))

    tk.Label(
        card,
        text="SimplyPark",
        font=("Arial", 30, "bold"),
        bg=CARD_BG,
        fg=PRIMARY,
    ).grid(row=1, column=0, columnspan=2, pady=(0, 6))

    tk.Label(
        card,
        text="parking made simple",
        font=("Arial", 12),
        bg=CARD_BG,
        fg=MUTED,
    ).grid(row=2, column=0, columnspan=2, pady=(0, 28))

    tk.Label(
        card,
        text="Username",
        bg=CARD_BG,
        fg=TEXT,
        font=("Arial", 12, "bold"),
    ).grid(row=3, column=0, columnspan=2, sticky="w", pady=(0, 6))

    username_entry = styled_entry(card)
    username_entry.grid(row=4, column=0, columnspan=2, pady=(0, 16), ipady=8)

    tk.Label(
        card,
        text="Password",
        bg=CARD_BG,
        fg=TEXT,
        font=("Arial", 12, "bold"),
    ).grid(row=5, column=0, columnspan=2, sticky="w", pady=(0, 6))

    password_entry = styled_entry(card, show="*")
    password_entry.grid(row=6, column=0, columnspan=2, pady=(0, 24), ipady=8)

    def do_login():
        app.login(username_entry.get().strip(), password_entry.get().strip())

    username_entry.bind("<Return>", lambda event: do_login())
    password_entry.bind("<Return>", lambda event: do_login())

    login_button = tk.Label(
        card,
        text="Login",
        bg=PRIMARY,
        fg="white",
        font=("Arial", 12, "bold"),
        width=30,
        pady=12,
        cursor="hand2",
    )

    login_button.grid(row=7, column=0, columnspan=2, pady=(0, 12))

    login_button.bind("<Button-1>", lambda e: do_login())

    login_button.bind(
        "<Enter>",
        lambda e: login_button.config(bg=PRIMARY_DARK)
    )

    login_button.bind(
        "<Leave>",
        lambda e: login_button.config(bg=PRIMARY)
    )


    guest_button = tk.Label(
        card,
        text="Continue as Guest",
        bg="white",
        fg=PRIMARY,
        font=("Arial", 12, "bold"),
        width=30,
        pady=12,
        relief="solid",
        bd=1,
        cursor="hand2",
    )

    guest_button.grid(row=8, column=0, columnspan=2)

    guest_button.bind(
        "<Button-1>",
        lambda e: app.continue_as_guest()
    )

    guest_button.bind(
        "<Enter>",
        lambda e: guest_button.config(bg="#FDECEF")
    )

    guest_button.bind(
        "<Leave>",
        lambda e: guest_button.config(bg="white")
    )
    username_entry.focus_set()