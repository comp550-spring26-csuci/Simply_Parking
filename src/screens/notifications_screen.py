import tkinter as tk
from tkinter import ttk, messagebox

def build_notifications_screen(app):
    app.clear_content()
    top = tk.Frame(app.content_frame, padx=10, pady=10); top.pack(fill="x")
    tk.Label(top, text="Notifications", font=("Arial",16,"bold")).pack(side="left")
    tk.Button(top, text="Refresh", command=app.show_notifications).pack(side="right")
    acts = tk.Frame(app.content_frame, padx=10, pady=5); acts.pack(fill="x")

    def mark_all():
        ok = app.db.mark_all_notifications_read(user_id=app.current_user["id"] if app.current_user else None)
        if ok: app.refresh_notification_badge(); app.show_notifications()
        else: messagebox.showerror("Error","Could not mark as read.")

    tk.Button(acts, text="Mark All Read", command=mark_all).pack(side="left")

    tf = tk.Frame(app.content_frame, padx=10, pady=10); tf.pack(fill="both", expand=True)
    cols = ("id","title","message","type","is_read","created_at")
    tree = ttk.Treeview(tf, columns=cols, show="headings")
    heads={"id":"ID","title":"Title","message":"Message","type":"Type","is_read":"Read","created_at":"Created"}
    ws   ={"id":45,"title":150,"message":360,"type":90,"is_read":70,"created_at":150}
    for c in cols:
        tree.heading(c, text=heads[c])
        tree.column(c, width=ws[c], anchor="w" if c=="message" else "center")
    sb = ttk.Scrollbar(tf, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=sb.set)
    tree.pack(side="left", fill="both", expand=True); sb.pack(side="right", fill="y")

    def shorten(t,n=45): t=str(t); return t if len(t)<=n else t[:n-3]+"..."
    def refresh():
        for i in tree.get_children(): tree.delete(i)
        role = app.current_user.get("role") if app.current_user else None

        if role in {"admin", "support_agent"}:
            uid = None
        else:
            uid = app.current_user["id"] if app.current_user else None

        for row in app.db.fetch_notifications(user_id=uid):
            nid,_,title,msg,ntype,is_read,created_at = row
            tree.insert("",tk.END,values=(nid,shorten(title,20),shorten(msg,45),
                ntype,"Yes" if is_read else "No",str(created_at)[:16]))

    def mark_sel():
        sel = tree.selection()
        if not sel: messagebox.showwarning("Selection","Select a notification first."); return
        nid = tree.item(sel[0],"values")[0]
        if app.db.mark_notification_read(int(nid)):
            app.refresh_notification_badge(); refresh()
        else: messagebox.showerror("Error","Could not mark as read.")

    tk.Button(acts, text="Mark Selected Read", command=mark_sel).pack(side="left", padx=10)
    try: refresh()
    except Exception as e: messagebox.showerror("Error",str(e))
