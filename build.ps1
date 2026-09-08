$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
& .\.venv\Scripts\python.exe -m PyInstaller --noconfirm --clean --onefile --windowed --name NEON-Video --collect-all customtkinter --collect-all yt_dlp --collect-all yt_dlp_ejs --add-data 'binaries;binaries' --add-data 'licenses;licenses' main.py
if ($LASTEXITCODE -ne 0) { throw 'Build failed' }
