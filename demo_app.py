"""Windows 隔离实验窗口。可作为 MXU pretask 启动，也保留原 CLI 会话模式。"""
import argparse
import json
import os
import subprocess
import sys
import tkinter as tk
from pathlib import Path


def default_result() -> Path:
    folder = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parent
    if folder.name.lower() == "tools":
        folder = folder.parent
    return folder / "debug" / "lab-saved.json"


def spawn_detached(args: argparse.Namespace) -> None:
    """MXU 需要预任务及时退出，目标窗口则在独立子进程保持运行。"""
    import ctypes
    import time
    if ctypes.windll.user32.FindWindowW(None, "MAA LOCAL LAB - MXU"):
        return  # 已有同名测试窗口，避免重复启动
    exe = Path(sys.executable).resolve()
    cmd = [str(exe)]
    if not getattr(sys, "frozen", False):
        cmd.append(str(Path(__file__).resolve()))
    cmd.extend(["--session", "MXU", "--result", str(default_result())])
    if args.simulate_failure:
        cmd.append("--simulate-failure")
    subprocess.Popen(
        cmd,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        close_fds=True,
        creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP,
    )
    # 防止 Controller 连接时目标窗体尚未出现。
    for _ in range(100):
        if ctypes.windll.user32.FindWindowW(None, "MAA LOCAL LAB - MXU"):
            return
        time.sleep(0.1)
    raise RuntimeError("实验窗口在 10 秒内未就绪")


def main(argv=None):
    parser = argparse.ArgumentParser(description="Maa Local Lab Windows 测试目标")
    parser.add_argument("--session", default="MXU")
    parser.add_argument("--result")
    parser.add_argument("--spawn", action="store_true", help="预任务：启动独立窗口后退出")
    parser.add_argument("--simulate-failure", action="store_true")
    parser.add_argument("--self-check", action="store_true")
    args = parser.parse_args(argv)
    if args.self_check:
        if not hasattr(subprocess, "DETACHED_PROCESS") and os.name == "nt":
            return 1
        return 0
    if args.spawn:
        if os.name != "nt":
            parser.error("--spawn 仅适用于 Windows")
        spawn_detached(args)
        return 0

    result_path = Path(args.result).resolve() if args.result else default_result()
    root = tk.Tk()
    root.title("MAA LOCAL LAB - " + args.session)
    root.geometry("720x440")
    root.configure(bg="#111827")
    tk.Label(root, text="MAA LOCAL LAB", font=("Arial", 21, "bold"), fg="#a5b4fc", bg="#111827").pack(pady=40)
    status = tk.StringVar(value="等待操作")
    tk.Label(root, textvariable=status, font=("Microsoft YaHei", 25), fg="white", bg="#111827").pack(pady=30)

    def save():
        if args.simulate_failure:
            status.set("模拟保存失败")
            return
        result_path.parent.mkdir(parents=True, exist_ok=True)
        result_path.write_text(json.dumps({"session_id": args.session, "saved": True}, ensure_ascii=False), encoding="utf-8")
        status.set("保存成功")

    tk.Button(root, text="执行保存", command=save, font=("Microsoft YaHei", 20), fg="white", bg="#6366f1", padx=35, pady=10).pack()
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
