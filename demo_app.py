"""隔离的 Tkinter 试验目标。可被普通 Python 或 PyInstaller 多模式入口调用。"""
import argparse
import json
import tkinter as tk
from pathlib import Path


def main(argv=None):
    parser = argparse.ArgumentParser(description="Maa Local Lab 试验窗口")
    parser.add_argument("--session", required=True)
    parser.add_argument("--result", required=True)
    parser.add_argument("--simulate-failure", action="store_true")
    args = parser.parse_args(argv)

    root = tk.Tk()
    root.title("MAA LOCAL LAB - " + args.session)
    root.geometry("720x440")
    root.configure(bg="#111827")

    tk.Label(root, text="MAA LOCAL LAB", font=("Arial", 21, "bold"),
             fg="#a5b4fc", bg="#111827").pack(pady=40)
    status = tk.StringVar(value="等待操作")
    tk.Label(root, textvariable=status, font=("Microsoft YaHei", 25),
             fg="white", bg="#111827").pack(pady=30)

    def save():
        if args.simulate_failure:
            status.set("模拟保存失败")
            return
        result = Path(args.result)
        result.parent.mkdir(parents=True, exist_ok=True)
        result.write_text(
            json.dumps({"session_id": args.session, "saved": True}),
            encoding="utf-8",
        )
        status.set("保存成功")

    tk.Button(root, text="执行保存", command=save,
              font=("Microsoft YaHei", 20),
              fg="white", bg="#6366f1", padx=35, pady=10).pack()
    root.mainloop()


if __name__ == "__main__":
    main()
