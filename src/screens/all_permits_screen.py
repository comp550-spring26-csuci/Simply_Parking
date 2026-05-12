"""Admin screen — view ALL daily and semester permits across all users."""
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date

def build_all_permits_screen(app):
    app.clear_content()
    nb = ttk.Notebook(app.content_frame); nb.pack(fill="both", expand=True, padx=10, pady=10)

    # ── Tab 1: Daily Permits ─────────────────────────────────────────────────
    dp_tab = tk.Frame(nb); nb.add(dp_tab, text="Daily Permits")
    top1 = tk.Frame(dp_tab, padx=10, pady=6); top1.pack(fill="x")
    tk.Label(top1, text="All Daily Permits", font=("Arial",14,"bold")).pack(side="left")
    tk.Button(top1, text="Refresh", command=lambda: load_daily()).pack(side="right")

    cols1=("id","username","plate","date","amount","created")
    t1=ttk.Treeview(dp_tab,columns=cols1,show="headings"); sb1=ttk.Scrollbar(dp_tab,orient="v",command=t1.yview)
    t1.configure(yscrollcommand=sb1.set)
    heads1={"id":"ID","username":"User","plate":"Plate","date":"Permit Date","amount":"Amount","created":"Purchased"}
    ws1   ={"id":50,"username":120,"plate":110,"date":110,"amount":90,"created":150}
    for c in cols1:
        t1.heading(c,text=heads1[c]); t1.column(c,width=ws1[c],anchor="center")
    t1.pack(side="left",fill="both",expand=True,padx=(10,0),pady=6)
    sb1.pack(side="right",fill="y",pady=6,padx=(0,10))

    today=date.today()
    def load_daily():
        for i in t1.get_children(): t1.delete(i)
        try:
            rows=app.db.fetch_all_daily_permits(limit=200)
            if not rows: t1.insert("","end",values=("","No daily permits found.","","","","")); return
            for pid,uname,plate,pdate,amt,created in rows:
                tag="today" if str(pdate)==str(today) else ""
                t1.insert("","end",values=(pid,uname,plate,str(pdate),f"${float(amt):.2f}",str(created)[:16]),tags=(tag,))
            t1.tag_configure("today",background="#e8f5e9")
        except Exception as e: messagebox.showerror("Error",str(e))

    # ── Tab 2: Semester Permits ──────────────────────────────────────────────
    sp_tab = tk.Frame(nb); nb.add(sp_tab, text="Semester Permits")
    top2 = tk.Frame(sp_tab, padx=10, pady=6); top2.pack(fill="x")
    tk.Label(top2, text="All Semester Permits", font=("Arial",14,"bold")).pack(side="left")
    tk.Button(top2, text="Refresh", command=lambda: load_sem()).pack(side="right")

    cols2=("id","username","plate","start","end","amount","status","created")
    t2=ttk.Treeview(sp_tab,columns=cols2,show="headings"); sb2=ttk.Scrollbar(sp_tab,orient="v",command=t2.yview)
    t2.configure(yscrollcommand=sb2.set)
    heads2={"id":"ID","username":"User","plate":"Plate","start":"Start","end":"End",
            "amount":"Amount","status":"Status","created":"Purchased"}
    ws2   ={"id":50,"username":110,"plate":100,"start":100,"end":100,"amount":80,"status":80,"created":140}
    for c in cols2:
        t2.heading(c,text=heads2[c]); t2.column(c,width=ws2[c],anchor="center")
    t2.pack(side="left",fill="both",expand=True,padx=(10,0),pady=6)
    sb2.pack(side="right",fill="y",pady=6,padx=(0,10))
    t2.tag_configure("active",background="#e8f5e9")
    t2.tag_configure("expired",foreground="#999")

    def load_sem():
        for i in t2.get_children(): t2.delete(i)
        try:
            rows=app.db.fetch_all_semester_permits(limit=200)
            if not rows: t2.insert("","end",values=("","No semester permits found.","","","","","","")); return
            for pid,uname,plate,start,end,amt,created,status in rows:
                tag="active" if status=="Active" else "expired"
                t2.insert("","end",values=(pid,uname,plate,str(start),str(end),
                    f"${float(amt):.2f}",status,str(created)[:16]),tags=(tag,))
        except Exception as e: messagebox.showerror("Error",str(e))

    app.root.after_idle(load_daily)
    app.root.after_idle(load_sem)
