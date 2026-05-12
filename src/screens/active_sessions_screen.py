import tkinter as tk
from tkinter import ttk, messagebox

def build_active_sessions_screen(app):
    app.clear_content()
    top=tk.Frame(app.content_frame,padx=10,pady=10); top.pack(fill="x")
    tk.Label(top,text="Active Parking Sessions",font=("Arial",16,"bold")).pack(side="left")
    tk.Button(top,text="🔄 Refresh",command=app.show_active_sessions).pack(side="right")
    tf=tk.Frame(app.content_frame,padx=10,pady=10); tf.pack(fill="both",expand=True)
    cols=("id","plate","entry_time","duration","status","amount_due")
    tree=ttk.Treeview(tf,columns=cols,show="headings")
    heads={"id":"ID","plate":"Plate","entry_time":"Entry Time","duration":"Duration","status":"Status","amount_due":"Amount Due"}
    ws   ={"id":60,"plate":120,"entry_time":180,"duration":120,"status":110,"amount_due":110}
    for c in cols:
        tree.heading(c,text=heads[c]); tree.column(c,width=ws[c],anchor="center")
    sb=ttk.Scrollbar(tf,orient="vertical",command=tree.yview); tree.configure(yscrollcommand=sb.set)
    tree.pack(side="left",fill="both",expand=True); sb.pack(side="right",fill="y")
    def load():
        for i in tree.get_children(): tree.delete(i)
        try:
            rows=app.db.fetch_active_sessions()
            if not rows: tree.insert("","end",values=("","No active sessions.","","","","")); return
            for sid,plate,entry,dur,status,amt in rows:
                tree.insert("","end",values=(sid,plate,str(entry)[:19],
                    f"{dur} min" if dur is not None else "—",status,f"${float(amt):.2f}"))
        except Exception as e: messagebox.showerror("Error",str(e))
    app.root.after_idle(load)
