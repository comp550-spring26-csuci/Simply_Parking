import tkinter as tk
from tkinter import ttk, messagebox

def build_payment_history_screen(app):
    app.clear_content()
    top=tk.Frame(app.content_frame,padx=10,pady=10); top.pack(fill="x")
    tk.Label(top,text="Payment History",font=("Arial",16,"bold")).pack(side="left")
    tk.Button(top,text="🔄 Refresh",command=app.show_payment_history).pack(side="right")
    tf=tk.Frame(app.content_frame,padx=10,pady=10); tf.pack(fill="both",expand=True)
    cols=("id","plate","payment_type","amount","created_at")
    tree=ttk.Treeview(tf,columns=cols,show="headings")
    heads={"id":"ID","plate":"Plate","payment_type":"Type","amount":"Amount","created_at":"Date"}
    ws   ={"id":60,"plate":130,"payment_type":180,"amount":100,"created_at":200}
    for c in cols:
        tree.heading(c,text=heads[c]); tree.column(c,width=ws[c],anchor="center")
    sb=ttk.Scrollbar(tf,orient="vertical",command=tree.yview); tree.configure(yscrollcommand=sb.set)
    tree.pack(side="left",fill="both",expand=True); sb.pack(side="right",fill="y")
    def load():
        for i in tree.get_children(): tree.delete(i)
        if not app.current_user or not app.current_user.get("id"): return
        try:
            rows=app.db.fetch_payment_history(app.current_user["id"])
            if not rows: tree.insert("","end",values=("","No payments found yet.","","","")); return
            for rid,plate,ptype,amt,created in rows:
                tree.insert("","end",values=(rid,plate,ptype,f"${float(amt):.2f}",str(created)[:19]))
        except Exception as e: messagebox.showerror("Error",str(e))
    app.root.after_idle(load)
