import tkinter as tk

BG = "#2b2b2b"
CARD_BG = "#242424"
ENTRY_BG = "#1f1f1f"
BORDER = "#777777"

def dark_entry(parent, show=None):
    return tk.Entry(
        parent,
        width=32,
        show=show,
        bg=ENTRY_BG,
        fg="white",
        insertbackground="white",
        relief="solid",
        highlightthickness=1,
        highlightbackground=BORDER,
        highlightcolor="#4a90e2",
        font=("Arial", 12),
    )

def build_login_screen(app):
    app.main_frame.configure(bg=BG)

    outer = tk.Frame(app.main_frame, bg=BG)
    outer.pack(expand=True)

    card = tk.Frame(outer,bg=CARD_BG,padx=42,pady=34,bd=1,relief="solid",
)
    card.pack()

    tk.Label(card,text="SimplyPark",font=("Arial", 24, "bold"),bg=CARD_BG,fg="white",).grid(row=0, column=0, columnspan=2, pady=(0, 6))

    tk.Label(card,text="--parking made simple--",font=("Arial", 11),bg=CARD_BG,fg="#bdbdbd",).grid(row=1, column=0, columnspan=2, pady=(0, 28))

    tk.Label(card,text="Username",bg=CARD_BG,fg="white",font=("Arial", 11),).grid(row=2, column=0, columnspan=2, sticky="w", pady=(0, 5))

    username_entry = dark_entry(card)
    username_entry.grid(row=3, column=0, columnspan=2, pady=(0, 14), ipady=4)

    tk.Label(card,text="Password",bg=CARD_BG,fg="white",font=("Arial", 11),).grid(row=4, column=0, columnspan=2, sticky="w", pady=(0, 5))

    password_entry = dark_entry(card, show="*")
    password_entry.grid(row=5, column=0, columnspan=2, pady=(0, 22), ipady=4)

    def do_login():
        app.login(username_entry.get().strip(), password_entry.get().strip())

    username_entry.bind("<Return>", lambda event: do_login())
    password_entry.bind("<Return>", lambda event: do_login())

    tk.Button(card,text="Login",width=30,command=do_login,font=("Arial", 11, "bold"),).grid(row=6, column=0, columnspan=2, pady=(0, 10), ipady=3)

    tk.Button(card,text="Continue as Guest",width=30,command=app.continue_as_guest,font=("Arial", 11),).grid(row=7, column=0, columnspan=2, ipady=3)

    username_entry.focus_set()