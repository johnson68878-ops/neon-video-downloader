# NEON MeetStudio · 會議影音工作站

Windows 本地桌面應用：會議錄屏與影音下載。繁體中文介面。


## 直接執行

雙擊 `dist/NEON-MeetStudio.exe`。獨立 EXE 內含 Python、FFmpeg 與 Node.js。

## 會議預約

新增獨立分頁，提供五個平台圖示、本機優先啟動、網頁登入與自訂路徑。詳見 [偵測方式與來源](docs/MEETING-LAUNCHERS.md)。

## 會議錄屏

1. 選擇螢幕，或點選“框選區域”拖動選擇；Esc 取消框選。
2. 選擇 720p（預設）或 1080p。勾選“優先小檔案”使用更高壓縮；取消可提高細節清晰度。
3. 選擇系統聲音、麥克風（可同時開啟，也可全部關閉）。使用 Windows 預設輸出/輸入裝置。
4. 點選“開始錄製”，倒計時 3 秒後錄製。主視窗最小化，浮動控制欄可暫停、繼續、停止。
5. “停止並儲存”生成 H.264 / AAC MP4，可直接播放或開啟資料夾。

預設輸出到使用者 Videos/NEON MeetStudio。錄屏為 15 fps，適合會議、課件、操作講解；不是高幀率遊戲錄製模式。
解析度選項是影片高度上限，保留區域原始比例，小區域不會被放大。檔案大小隨畫面變化及錄製時長而變化，不承諾固定大小。
暫停透過獨立片段實現，恢復時會重新準備裝置；最終影片不含暫停時間。停止後請等待合併完成。
錄製期間不要切換 Windows 預設聲音裝置。會議建議使用耳機，以免麥克風再次錄入揚聲器的聲音。
程式不自動獲取會議登入憑證，也不上傳錄製檔案。下載功能按指定網址連線來源網站。

### 異常恢復

錄製中畫面儲存為 MKV，音訊實時壓縮為 AAC，不生成巨大的整場 PCM 臨時檔案。
若裝置斷開、磁碟異常或程式意外退出，保留輸出目錄內 `.錄製中-*` 資料夾。
裡面的 `segment-*.mp4` 是已完成片段，`video-*.mkv` 與 `audio-*.m4a` 是尚未完成合並的素材，日誌記錄失敗原因。
成功輸出 MP4 後才清理當前會話的臨時檔案。恢復素材暫不提供一鍵修復介面。

## 影音下載

支援 yt-dlp 可解析的來源，例如 YouTube、抖音、Facebook、TikTok、Instagram、Bilibili 等。
支援分享文字、批次連結、解析度選擇、MP3、字幕、停止及續傳。網站支援受來源網站和 yt-dlp 版本影響。
僅錄屏輸出固定 MP4；下載保留原有容器相容策略，可能輸出 MP4 / WebM。
不支援 DRM，當前版本不提供登入 Cookie 匯入。

## 從原始碼開發與打包

環境：Windows 10/11 x64，Python 3.12 或 3.13（包含 tkinter），Node.js 22 或更新。
本次在 Python 3.13 x64 上構建和測試。

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe prepare_runtime.py
.\.venv\Scripts\python.exe main.py
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
powershell -ExecutionPolicy Bypass -File build.ps1
```

`build.ps1` 生成 `dist/NEON-MeetStudio.exe`，沒有數字簽名。
原始碼入口為 `main.py`；錄屏引擎 `neon/recorder.py`；主介面 `neon/ui.py`；下載頁 `neon/download_ui.py`。
第三方許可證隨包放在 `licenses`，來源見 `THIRD_PARTY.md`。

## 方案參考

- FFmpeg gdigrab 螢幕採集：https://www.ffmpeg.org/ffmpeg-devices.html#gdigrab
- PyAudioWPatch WASAPI 系統聲音採集：https://github.com/s0d3s/PyAudioWPatch
- Windows 截圖工具的錄製互動：https://support.microsoft.com/en-us/windows/apps/use-snipping-tool-to-capture-screenshots

介面與業務程式碼在本專案實現，未複製格式工廠的閉原始碼。
