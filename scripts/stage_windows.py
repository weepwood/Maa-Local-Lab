"""将 PyInstaller 运行时、Maa OCR 模型和 Pipeline 放入 Tauri 的资源目录。"""
import argparse
import shutil
import urllib.request
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "src-tauri" / "resources"
OCR_URL = "https://download.maafw.xyz/MaaCommonAssets/OCR/ppocr_v6/ppocr_v6-small.zip"


def prepare():
    source = ROOT / "dist" / "maa-runner"
    runner = source / "maa-runner.exe"
    if not runner.is_file():
        raise RuntimeError("未找到 dist/maa-runner/maa-runner.exe，请先执行 PyInstaller")

    engine = ASSETS / "engine"
    if engine.exists():
        shutil.rmtree(engine)
    shutil.copytree(source, engine)
    if not (engine / "maa-runner.exe").is_file():
        raise RuntimeError("执行器复制失败")

    target_resource = ASSETS / "resource"
    target_pipeline = target_resource / "pipeline"
    target_pipeline.mkdir(parents=True, exist_ok=True)
    shutil.copy2(ROOT / "resource" / "pipeline" / "main.json",
                 target_pipeline / "main.json")

    target_ocr = target_resource / "model" / "ocr"
    target_ocr.mkdir(parents=True, exist_ok=True)
    archive = ROOT / "dist" / "ocr-small.zip"
    if not archive.exists():
        print("下载官方 OCR 模型...", flush=True)
        urllib.request.urlretrieve(OCR_URL, archive)
    with zipfile.ZipFile(archive) as zipped:
        for name in ("det.onnx", "rec.onnx", "keys.txt"):
            matches = [x for x in zipped.namelist()
                       if not x.endswith("/") and Path(x).name == name]
            if not matches:
                raise RuntimeError("OCR 压缩包缺少 " + name)
            with zipped.open(matches[0]) as inp, (target_ocr / name).open("wb") as out:
                shutil.copyfileobj(inp, out)
            if (target_ocr / name).stat().st_size == 0:
                raise RuntimeError("OCR 文件为空：" + name)
    print("已准备完成资源目录：", ASSETS, flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.parse_args()
    prepare()
