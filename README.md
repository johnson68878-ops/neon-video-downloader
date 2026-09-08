# NEON Video 影片下載工作站

## VS Code 直接開啟

開啟整個 `NEON-Source` 資料夾，先看 [ARCHITECTURE.md](ARCHITECTURE.md)。
也可雙擊 `NEON.code-workspace` 在 VS Code 開啟整份專案。
程式入口為 [main.py](main.py)，各功能分開放在 `neon/`。
安裝 Python 3.12 x64 後，可在 VS Code 的「終端機 → 執行工作」選「NEON：首次安裝」，完成後按 F5。
也可在終端機執行 `powershell -ExecutionPolicy Bypass -File setup.ps1`，之後用 `run.cmd` 開啟。
平台操作與限制見 [docs/PLATFORMS.md](docs/PLATFORMS.md)。

Windows 10/11 64 位元。繁體中文深色介面，使用 yt-dlp。

## 從 GitHub 取得

Git 儲存庫保存可閱讀的原始碼、文件與授權，不包含大型 EXE、FFmpeg、Node.js 二進位檔。
從 GitHub 複製本專案後，安裝 Python 3.12 x64 與 [Node.js 22 或更新版](https://nodejs.org)，再執行 `setup.ps1`。
安裝腳本會從 imageio-ffmpeg 套件取得 FFmpeg，並複製已安裝的 Node.js 到 `binaries/`。
本地提供的完整原始碼 ZIP 已附二進位工具，可直接依原有安裝步驟使用。

## 使用
開啟 NEON-Video.exe，先選畫質與儲存位置，再貼上網址或分享文字。預設「貼上即下載」開啟，會自動辨識平台並開始下載。
取消勾選「貼上即下載」後，可先貼連結，再選畫質與按「開始下載」。手動輸入網址也可按「開始下載」。
「解析資訊」會先查詢影片標題，不下載影片。下載失敗原因會顯示於下方紀錄。
支援批次、最高可用畫質、2160p/1440p/1080p/720p/480p/360p 影片高度上限、192 kbps MP3、可用的中英文字幕。「解析資訊」會在紀錄區列出來源提供的高度。
最佳畫質可能輸出 MP4、WebM 等，依來源編碼與容器相容性決定。字幕保存為獨立檔案。
停止會終止目前下載與轉換，保留部分檔案；相同網址和設定再次下載時可嘗試續傳。
網站支援以 yt-dlp 為準，不承諾所有網站。需登入、地區限制、付費或 DRM 內容可能無法下載。
本版不提供登入 Cookie 匯入。YouTube 等網站的變動可能需要升級 yt-dlp 並重新打包。
僅下載你有權儲存的內容。

## Python 原始碼與建置
安裝 Python 3.12 64 位元（需包含 tkinter），於此資料夾執行：
```
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python main.py
```
`binaries` 包含 FFmpeg 與 Node.js，供影音轉換及 yt-dlp JavaScript 解題使用。
執行 `build.ps1` 產生 `dist/NEON-Video.exe`。此為 PyInstaller 打包的獨立程式，使用者不需安裝 Python。
建置不是程式碼簽署，檔案沒有數位簽章。來源主程式採 MIT 授權；各依賴遵循各自授權，見 THIRD_PARTY.md 和 licenses。

## 開源參考
- yt-dlp：https://github.com/yt-dlp/yt-dlp
- CustomTkinter：https://github.com/TomSchimansky/CustomTkinter
- PyInstaller：https://github.com/pyinstaller/pyinstaller
- imageio-ffmpeg：https://github.com/imageio/imageio-ffmpeg
- Node.js：https://github.com/nodejs/node

介面為此專案自行撰寫，下載核心使用 yt-dlp 的 Python API。
