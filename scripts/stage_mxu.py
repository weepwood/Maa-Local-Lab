"""将官方 MXU/MaaFramework 发布包与 Maa Local Lab 测试资源组装为可分发目录。"""
import argparse
import shutil
import sys
import tempfile
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OCR_URL = "https://download.maafw.xyz/MaaCommonAssets/OCR/ppocr_v6/ppocr_v6-small.zip"
MXU_REF = "v2.7.1"
MAA_REF = "v5.14.3"


def unpack(archive: Path, folder: Path):
    folder.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive) as z:
        # Restrict paths to the requested staging directory, including absolute and traversal cases.
        root = folder.resolve()
        for item in z.infolist():
            target = (root / item.filename).resolve()
            if not target.is_relative_to(root):
                raise ValueError("不安全的 ZIP 文件路径: " + item.filename)
        z.extractall(root)


def unique_file(folder: Path, name: str) -> Path:
    matches = [f for f in folder.rglob("*") if f.is_file() and f.name.casefold() == name.casefold()]
    if len(matches) != 1:
        raise RuntimeError(f"{folder}: 预期 1 个 {name}，实际 {len(matches)} 个")
    return matches[0]


def fetch(url: str, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(url, headers={"User-Agent": "Maa-Local-Lab-build"})
    with urllib.request.urlopen(request, timeout=100) as stream, path.open("wb") as out:
        shutil.copyfileobj(stream, out)
    if not path.is_file() or path.stat().st_size < 100:
        raise RuntimeError("下载不完整: " + url)


def stage(mxu: Path, maafw: Path, target: Path, destination: Path, ocr: Path | None):
    if destination.exists():
        shutil.rmtree(destination)
    destination.mkdir(parents=True)
    with tempfile.TemporaryDirectory() as scratch:
        tmp = Path(scratch)
        unpack(mxu, tmp / "mxu")
        unpack(maafw, tmp / "maafw")
        exe = unique_file(tmp / "mxu", "mxu.exe")
        shutil.copytree(exe.parent, destination, dirs_exist_ok=True)
        ui = destination / "mxu.exe"
        if not ui.is_file():
            raise RuntimeError("官方 MXU 发布包未包含 mxu.exe")
        ui.rename(destination / "Maa Local Lab.exe")

        dll = unique_file(tmp / "maafw", "MaaFramework.dll")
        shutil.copytree(dll.parent, destination / "maafw", dirs_exist_ok=True)
        if not (destination / "maafw" / "MaaToolkit.dll").is_file():
            raise RuntimeError("MaaFramework 发布包缺少 MaaToolkit.dll")

        if not (target / "maa-lab-target.exe").exists():
            raise RuntimeError("请先用 PyInstaller 构建 maa-lab-target.exe")
        shutil.copytree(target, destination / "tools", dirs_exist_ok=True)
        shutil.copytree(ROOT / "resource", destination / "resource", dirs_exist_ok=True)
        shutil.copy2(ROOT / "interface.json", destination / "interface.json")

        if ocr is None:
            ocr = tmp / "ocr.zip"
            fetch(OCR_URL, ocr)
        unpack(ocr, tmp / "ocr")
        model = destination / "resource" / "model" / "ocr"
        model.mkdir(parents=True, exist_ok=True)
        for name in ("det.onnx", "rec.onnx", "keys.txt"):
            file = unique_file(tmp / "ocr", name)
            shutil.copy2(file, model / name)

    license_dir = destination / "licenses"
    license_dir.mkdir(exist_ok=True)
    fetch(f"https://raw.githubusercontent.com/MistEO/MXU/{MXU_REF}/LICENSE", license_dir / "MXU-AGPL-3.0.txt")
    fetch(f"https://raw.githubusercontent.com/MaaXYZ/MaaFramework/{MAA_REF}/LICENSE.md", license_dir / "MaaFramework-LGPL-3.0.md")
    shutil.copy2(ROOT / "THIRD_PARTY.md", license_dir / "SOURCES.md")
    (destination / "README.txt").write_text(
        "Maa Local Lab — MXU GUI\n"
        "1. 运行 'Maa Local Lab.exe'。\n"
        "2. 选择 Windows 实验窗口和实验资源。\n"
        "3. 在 MXU 的「添加任务」（+）中加入并启用「自动启动实验窗口」预任务。\n"
        "4. 点击运行；也可以先双击 tools/maa-lab-target.exe 手动启动目标。\n"
        "5. 在 MXU 的截图和日志中查看执行结果；debug/lab-saved.json 是本地凭据。\n"
        "源代码及许可证请查看 licenses 目录。\n",
        encoding="utf-8",
    )
    from validate_mxu import validate
    validate(destination)
    print("MXU 主界面与试验资源打包完成：", destination)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mxu", type=Path, required=True)
    parser.add_argument("--maafw", type=Path, required=True)
    parser.add_argument("--target", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--ocr", type=Path)
    a = parser.parse_args()
    stage(a.mxu, a.maafw, a.target, a.out, a.ocr)
