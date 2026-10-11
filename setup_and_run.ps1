$ErrorActionPreference="Stop"
Set-Location $PSScriptRoot
if (!(Test-Path ".venv")) { py -3 -m venv .venv }
& ".venv/Scripts/python.exe" -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) { throw "无法安装 Python 依赖" }
$ocr="resource/model/ocr"
New-Item -ItemType Directory -Force -Path $ocr | Out-Null
if (!(Test-Path "$ocr/det.onnx") -or !(Test-Path "$ocr/rec.onnx") -or !(Test-Path "$ocr/keys.txt")) {
 $zip=Join-Path $env:TEMP "maa-ocr-small.zip"
 Invoke-WebRequest "https://download.maafw.xyz/MaaCommonAssets/OCR/ppocr_v6/ppocr_v6-small.zip" -OutFile $zip
 $tmp=Join-Path $env:TEMP "maa-ocr-extract"
 if (Test-Path $tmp) { Remove-Item $tmp -Recurse -Force }
 Expand-Archive $zip $tmp
 foreach ($name in @("det.onnx","rec.onnx","keys.txt")) {
   $f=Get-ChildItem $tmp -Filter $name -Recurse | Select-Object -First 1
   if (!$f) { throw "缺少模型文件 $name" }
   Copy-Item $f.FullName (Join-Path $ocr $name)
 }
}
& ".venv/Scripts/python.exe" run_demo.py
exit $LASTEXITCODE
