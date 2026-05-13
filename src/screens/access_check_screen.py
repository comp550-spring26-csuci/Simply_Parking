"""Parking officer screen — check if a plate has valid access."""
import tkinter as tk
from tkinter import messagebox

def _entry(parent):
    return tk.Entry(parent, width=30, bg="#1f1f1f", fg="white", insertbackground="white",
                    relief="solid", highlightthickness=1, highlightbackground="#777",
                    highlightcolor="#aaa", font=("Arial",12))

def build_access_check_screen(app):
    app.clear_content()
    f = tk.Frame(app.content_frame, padx=24, pady=24); f.pack(anchor="nw")
    tk.Label(f, text="Plate Access Check", font=("Arial",16,"bold")).grid(row=0,column=0,columnspan=2,pady=10)
    tk.Label(f, text="License Plate").grid(row=1,column=0,sticky="e",pady=8)
    pe = _entry(f); pe.grid(row=1,column=1,padx=8,pady=8); pe.focus_set()

    result_frame = tk.Frame(f, bd=1, relief="solid", padx=16, pady=14, width=420)
    result_frame.grid(row=3,column=0,columnspan=2,sticky="ew",pady=12)
    result_frame.grid_propagate(False)
    result_lbl = tk.Label(result_frame, text="Enter a plate and click Check.",
                          font=("Arial",12), justify="left", wraplength=400)
    result_lbl.pack(anchor="w")
    badge_lbl = tk.Label(result_frame, text="", font=("Arial",22,"bold"))
    badge_lbl.pack(anchor="w", pady=(8,0))

    def check():
        plate = pe.get().strip().upper()
        if not plate: messagebox.showwarning("Input","Enter a license plate."); return
        try:
            r = app.db.check_plate_access(plate)
        except Exception as e:
            result_lbl.config(text=f"Error: {e}", fg="red"); badge_lbl.config(text=""); return

        if r["has_access"]:
            result_frame.config(bg="#e8f5e9"); result_lbl.config(bg="#e8f5e9",fg="#1b5e20")
            badge_lbl.config(bg="#e8f5e9", text="✅  ACCESS GRANTED", fg="#1a7a1a")
            result_lbl.config(text=f"Plate : {plate}\nType  : {r['access_type']}\n{r['details']}")
            app.db.add_log("access_check_granted", f"Plate={plate},type={r['access_type']}",
                           user_id=app.current_user["id"], username=app.current_user["username"])
        else:
            result_frame.config(bg="#ffebee"); result_lbl.config(bg="#ffebee",fg="#b71c1c")
            badge_lbl.config(bg="#ffebee", text="❌  ACCESS DENIED", fg="#c62828")
            result_lbl.config(text=f"Plate : {plate}\n{r['details']}")
            app.db.add_log("access_check_denied", f"Plate={plate}",
                           user_id=app.current_user["id"], username=app.current_user["username"])

    pe.bind("<Return>", lambda e: check())
    tk.Button(f, text="Check Access", width=20, font=("Arial",12,"bold"),
              command=check).grid(row=2,column=0,columnspan=2,pady=8)

    tk.Label(f, text="Checks: Semester Permit → Daily Permit → Active PAYG Session",
             font=("Arial",9), fg="#888").grid(row=4,column=0,columnspan=2)
