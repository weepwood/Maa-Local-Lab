"""MXU 和 PI V2 的离线结构检查；不假定 CI 具有图形桌面。"""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def validate(base: Path, staged=True) -> None:
    config = json.loads((base / "interface.json").read_text(encoding="utf-8"))
    if config.get("interface_version") != 2:
        raise ValueError("interface_version 必须为 2")
    controllers = {c["name"] for c in config.get("controller", [])}
    resources = {r["name"] for r in config.get("resource", [])}
    if not controllers or not resources:
        raise ValueError("缺少控制器或资源")
    if not any(c["type"] == "Win32" for c in config["controller"]):
        raise ValueError("缺少 Win32 控制器")
    pre = config["pretask"]
    steps = pre if isinstance(pre, list) else [pre]
    for p in steps:
        executable = Path(p["exec"].removeprefix("./"))
        if executable.is_absolute() or ".." in executable.parts:
            raise ValueError("pretask 路径不能越过项目根目录")
        if staged and not (base / executable).is_file():
            raise ValueError("找不到预任务: " + str(executable))
    for res in config["resource"]:
        if not set(res.get("controller", [])).issubset(controllers):
            raise ValueError("资源引用了不存在的控制器")
        for path in res["path"]:
            if not (base / path).is_dir():
                raise ValueError("资源路径不存在: " + path)
    pipeline = {}
    for json_file in (base / "resource" / "pipeline").glob("*.json"):
        nodes = json.loads(json_file.read_text(encoding="utf-8"))
        if not isinstance(nodes, dict):
            raise ValueError("Pipeline 不是 JSON 对象")
        pipeline.update(nodes)
    for task in config["task"]:
        if task["entry"] not in pipeline:
            raise ValueError("任务入口不存在: " + task["entry"])
    for name, node in pipeline.items():
        for next_name in node.get("next", []):
            if next_name not in pipeline:
                raise ValueError(f"{name} 引用了缺失节点 {next_name}")
    if staged:
        required = [
            "Maa Local Lab.exe",
            "maafw/MaaFramework.dll",
            "maafw/MaaToolkit.dll",
            "tools/maa-lab-target.exe",
            "resource/model/ocr/det.onnx",
            "resource/model/ocr/rec.onnx",
            "resource/model/ocr/keys.txt",
            "licenses/MXU-AGPL-3.0.txt",
            "licenses/MaaFramework-LGPL-3.0.md",
        ]
        for file in required:
            p = base / file
            if not p.is_file() or p.stat().st_size < 100:
                raise ValueError("发行包文件缺失或大小异常: " + file)
    print("MXU 项目资源检查通过：", base)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--root", type=Path, default=ROOT)
    p.add_argument("--staged", action="store_true")
    a = p.parse_args()
    validate(a.root, staged=a.staged)
