$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
& .\.venv\Scripts\python.exe -m PyInstaller --noconfirm --clean --onefile --windowed --name NOVA-Studio --icon assets/meetstudio.ico --version-file assets/version_info.txt --collect-all pyaudiowpatch --collect-all customtkinter --collect-all yt_dlp --collect-all yt_dlp_ejs --add-data 'binaries;binaries' --add-data 'licenses;licenses' --add-data 'assets;assets' main.py
if ($LASTEXITCODE -ne 0) { throw 'Build failed' }
