# 平台支援

本程式使用 yt-dlp 的網站解析器，自動依網址選擇；不需手動選平台。

| 平台 | 可貼的網址類型 | 注意事項 |
| --- | --- | --- |
| YouTube | youtube.com/watch、Shorts、youtu.be | 已附 Node.js 與 EJS；登入、年齡、反機器人驗證仍可能限制 |
| 抖音 | douyin.com/video、v.douyin.com 分享短鏈 | 可貼整段分享文；網站可能要求新鮮 Cookie 或驗證 |
| TikTok | tiktok.com、vm.tiktok.com、vt.tiktok.com | 與中國抖音不同平台，由各自解析器處理 |
| Facebook | facebook.com 影片 / Reels、fb.watch | 私人、登入限定內容可能無法下載 |
| Instagram | instagram.com Reels / 貼文 | 常受登入與頻率限制 |
| Bilibili | bilibili.com/video、b23.tv | 高畫質可能受登入與會員狀態限制 |
| X / Twitter | x.com、twitter.com 貼文 | 網站 API 或登入限制可能影響 |
| Vimeo / Twitch | 影片或剪輯網址 | 依來源與權限提供格式 |
| 其他 | yt-dlp 支援網站或公開影片直連 | 由通用或專用 extractor 嘗試解析 |

`neon/urls.py` 的平台表只決定畫面標籤。實際支援由 yt-dlp 決定，沒有逐一實測上述平台的線上下載。網站持續變更，名單不代表每支影片當下都能成功。

來源：[yt-dlp 官方支援清單](https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md)、[官方說明](https://github.com/yt-dlp/yt-dlp)。

## 畫質與使用方式

1. 選擇「最佳畫質」或 2160p / 1440p / 1080p / 720p / 480p / 360p。
2. 選擇儲存資料夾。
3. 保持「貼上即下載」勾選，按「貼上剪貼簿」或在網址欄 Ctrl+V，自動開始。
4. 若想先查看影片資訊，取消「貼上即下載」，貼上後按「解析資訊」。日誌會列出網站提供的影片高度。

預設只處理播放清單的單支影片。沒有選定畫質時以最佳畫質下載；選定上限時選來源中不超過上限的格式。來源高度未知則保留原檔，不保證符合上限。字幕必須來源提供。
