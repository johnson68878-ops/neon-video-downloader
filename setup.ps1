$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
if (-not (Test-Path '.venv\Scripts\python.exe')) {
    python -m venv .venv
    if ($LASTEXITCODE -ne 0) { throw '請先安裝含 tkinter 的 Python 3.12 x64，並加入 PATH。' }
}
& .\.venv\Scripts\python.exe -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) { throw '套件安裝失敗，請檢視上方訊息。' }
& .\.venv\Scripts\python.exe prepare_runtime.py
if ($LASTEXITCODE -ne 0) { throw '影音工具尚未備妥，請依上方訊息處理後重試。' }
Write-Host '完成。可以在 VS Code 按 F5，或執行 run.cmd。'
