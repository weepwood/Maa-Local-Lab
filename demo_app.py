import argparse,json,tkinter as tk
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument("--session",required=True);p.add_argument("--result",required=True);p.add_argument("--simulate-failure",action="store_true");a=p.parse_args()
root=tk.Tk();root.title("MAA LOCAL LAB - "+a.session);root.geometry("720x440");root.configure(bg="#111827")
tk.Label(root,text="MAA LOCAL LAB",font=("Arial",21,"bold"),fg="#a5b4fc",bg="#111827").pack(pady=40)
status=tk.StringVar(value="等待操作");tk.Label(root,textvariable=status,font=("Microsoft YaHei",25),fg="white",bg="#111827").pack(pady=30)
def save():
 if a.simulate_failure:status.set("模拟保存失败");return
 f=Path(a.result);f.parent.mkdir(parents=True,exist_ok=True);f.write_text(json.dumps({"session_id":a.session,"saved":True}),encoding="utf-8");status.set("保存成功")
tk.Button(root,text="执行保存",command=save,font=("Microsoft YaHei",20),fg="white",bg="#6366f1",padx=35,pady=10).pack()
root.mainloop()
