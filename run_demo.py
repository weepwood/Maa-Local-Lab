"""MaaFramework 独立执行器。

普通开发模式: python run_demo.py --resource-root ./resource --runs-dir ./runs
打包模式: maa-runner.exe --resource-root <安装资源路径> --runs-dir <用户数据路径>
打包后也可用同一 exe --demo-ui 启动试验窗口，不依赖外部 Python。
"""
import argparse
import json
import os
import subprocess
import sys
import time
import uuid
from datetime import datetime
from pathlib import Path


BASE = Path(__file__).resolve().parent


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Maa Local Lab Windows 自动化执行器")
    parser.add_argument("--mode", choices=("foreground", "background"), default="foreground")
    parser.add_argument("--simulate-failure", action="store_true")
    parser.add_argument("--resource-root", type=Path, default=BASE / "resource")
    parser.add_argument("--runs-dir", type=Path, default=BASE / "runs")
    parser.add_argument("--pipeline-file", type=Path)
    parser.add_argument("--self-check", action="store_true")
    return parser.parse_args(argv)


def check_resources(root: Path):
    required = [
        root / "pipeline" / "main.json",
        root / "model" / "ocr" / "det.onnx",
        root / "model" / "ocr" / "rec.onnx",
        root / "model" / "ocr" / "keys.txt",
    ]
    missing = [str(p) for p in required if not p.is_file()]
    if missing:
        raise RuntimeError("资源缺失：" + ", ".join(missing))


def self_check(root: Path):
    from maa.library import Library
    check_resources(root)
    print("MaaFramework:", Library.version(), flush=True)
    print("执行器及 OCR 模型检查通过", flush=True)


def main(argv=None):
    args = parse_args(argv)
    if os.name != "nt":
        raise RuntimeError("本实验仅支持 Windows 图形会话")

    if args.self_check:
        self_check(args.resource_root)
        return 0

    from maa.toolkit import Toolkit
    from maa.resource import Resource
    from maa.tasker import Tasker
    from maa.controller import (
        Win32Controller,
        MaaWin32ScreencapMethodEnum,
        MaaWin32InputMethodEnum,
    )
    check_resources(args.resource_root)
    session = uuid.uuid4().hex[:10]
    run_dir = args.runs_dir / (
        datetime.now().strftime("%Y%m%d-%H%M%S") + "-" + session
    )
    run_dir.mkdir(parents=True, exist_ok=True)
    proof = run_dir / "saved.json"
    report = {
        "session_id": session, "mode": args.mode,
        "passed": False, "nodes": []
    }

    if getattr(sys, "frozen", False):
        # 冻结后 sys.executable 是本执行器，不是 Python 解释器。
        command = [sys.executable, "--demo-ui"]
    else:
        command = [sys.executable, str(BASE / "demo_app.py")]
    command += ["--session", session, "--result", str(proof)]
    if args.simulate_failure:
        command.append("--simulate-failure")

    # Windows 上无控制台启动窗口目标；父进程负责终止子进程。
    demo = subprocess.Popen(command)
    try:
        Toolkit.init_option(str(run_dir), {
            "logging": True, "save_draw": True, "save_on_error": True
        })
        title = "MAA LOCAL LAB - " + session
        for _ in range(80):
            found = [w for w in Toolkit.find_desktop_windows()
                     if w.window_name == title]
            if found:
                break
            time.sleep(0.25)
        else:
            raise RuntimeError("未发现实验窗口，连接超时")
        window = found[0]
        print("已发现窗口：", window.window_name, flush=True)

        if args.mode == "foreground":
            import ctypes
            ctypes.windll.user32.ShowWindow(window.hwnd, 9)
            ctypes.windll.user32.SetForegroundWindow(window.hwnd)
            cap = MaaWin32ScreencapMethodEnum.ScreenDC
            inp = MaaWin32InputMethodEnum.Seize
        else:
            cap = MaaWin32ScreencapMethodEnum.Background
            inp = MaaWin32InputMethodEnum.PostMessage

        controller = Win32Controller(
            hWnd=window.hwnd, screencap_method=cap,
            mouse_method=inp, keyboard_method=inp
        )
        if not controller.post_connection().wait().succeeded:
            raise RuntimeError("控制器连接失败")

        resource = Resource()
        if not resource.post_bundle(str(args.resource_root)).wait().succeeded:
            raise RuntimeError("MaaFramework 资源加载失败")
        if args.pipeline_file:
            if not args.pipeline_file.is_file():
                raise RuntimeError("用户 Pipeline 文件不存在")
            if not resource.post_pipeline(str(args.pipeline_file)).wait().succeeded:
                raise RuntimeError("用户 Pipeline 加载失败")

        tasker = Tasker()
        if not tasker.bind(resource, controller) or not tasker.inited:
            raise RuntimeError("Tasker 初始化失败")
        job = tasker.post_task("开始测试").wait()
        detail = job.get()
        if detail:
            report["nodes"] = [
                {"name": node.name, "completed": node.completed}
                for node in detail.nodes
            ]
        completed = any(
            n["name"] == "确认保存成功" and n["completed"]
            for n in report["nodes"]
        )
        valid_proof = (
            proof.is_file() and
            json.loads(proof.read_text(encoding="utf-8")).get("session_id")
            == session
        )
        report["passed"] = bool(job.succeeded and completed and valid_proof)
    except Exception as exc:
        report["error"] = str(exc)
        print("错误：", exc, flush=True)
    finally:
        (run_dir / "report.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        if demo.poll() is None:
            demo.terminate()
            try:
                demo.wait(timeout=5)
            except subprocess.TimeoutExpired:
                demo.kill()
        print("执行完成：", report["passed"], "报告：", run_dir, flush=True)
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    # PyInstaller 的嵌入式 Python 可能无视 PYTHONUTF8 并采用 cp1252。
    # 在任何中文日志输出之前显式设定编码。
    for stream in (sys.stdout, sys.stderr):
        if stream is not None and hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    if len(sys.argv) > 1 and sys.argv[1] == "--demo-ui":
        # PyInstaller 必须在静态导入图中看见 demo_app / tkinter。
        import demo_app
        demo_app.main(sys.argv[2:])
    else:
        sys.exit(main())
