"""為 GitHub 原始碼下載版準備 FFmpeg 與 Node.js。"""
from pathlib import Path
import shutil
import subprocess
import imageio_ffmpeg

root = Path(__file__).resolve().parent
target = root / 'binaries'
target.mkdir(exist_ok=True)
if not (target / 'ffmpeg.exe').exists():
    shutil.copy2(imageio_ffmpeg.get_ffmpeg_exe(), target / 'ffmpeg.exe')
if not (target / 'node.exe').exists():
    node = shutil.which('node.exe')
    if node:
        major = int(subprocess.check_output([node, '--version'], text=True).strip().lstrip('v').split('.')[0])
        if major >= 22:
            shutil.copy2(node, target / 'node.exe')
    if not (target / 'node.exe').exists():
        raise SystemExit('請從 https://nodejs.org 安裝 Node.js 22 或更新版本，重新開啟終端機後再執行 setup.ps1。')
print('FFmpeg and Node.js are ready.')
