# 會議預約入口

v2.2.0 提供 Zoom、Microsoft Teams、Google Meet、騰訊會議與 Webex。每張圖示卡可開啟本機客戶端、直接網頁登入或設定自訂 EXE / LNK 路徑。登入與最後建立會議由使用者操作。

## Windows 偵測方式

| 平台 | 常見安裝位置或方式 | 官方網頁 |
|---|---|---|
| Zoom | `%APPDATA%/Zoom/bin/Zoom.exe`、`%ProgramFiles%/Zoom/bin/Zoom.exe` | https://zoom.us/meeting/schedule |
| Teams | 新版使用 Windows 註冊的 msteams 協定；傳統版 `%LOCALAPPDATA%/Microsoft/Teams/current/Teams.exe` | https://teams.microsoft.com/v2/ |
| Google Meet | Chrome / Edge 安裝的 PWA 開始功能表捷徑，沒有固定 GoogleMeet.exe | https://meet.google.com/ |
| 騰訊會議 | `%ProgramFiles%/Tencent/WeMeet/WeMeetApp.exe`，亦檢查 x86 / LocalAppData | https://meeting.tencent.com/user-center |
| Webex | `%LOCALAPPDATA%/Programs/Cisco Spark/CiscoCollabHost.exe` 或 `%ProgramFiles%/Cisco Spark/CiscoCollabHost.exe` | https://web.webex.com/ |

環境變數通常展開到 C 槽，但遵循使用者實際系統設定。自訂路徑優先；未找到或啟動失敗先提示，再開啟官方網頁。設定只儲存在本機 `%LOCALAPPDATA%/MeetStudio/meeting-apps.json`，不儲存帳密。兩個語言版本共用這份路徑設定。

## 來源

- [Teams 官方深層連結](https://learn.microsoft.com/en-us/microsoftteams/platform/concepts/build-and-test/deep-link-workflow)
- [Google Meet 官方 PWA 說明](https://support.google.com/meet/answer/10708569?hl=en)
- [Zoom 安裝說明](https://support.zoom.com/hc/en/article?id=zm_kb&sysparm_article=KB0058758)
- [Webex 安裝說明](https://help.webex.com/en-us/article/nw5p67g/Webex-Installation-and-Automatic-Upgrade)
- [dashboard-icons 開源圖示](https://github.com/homarr-labs/dashboard-icons)：Zoom、Teams、Google Meet、Webex PNG，Apache-2.0，授權附於 licenses/dashboard-icons/LICENSE。平台名稱與標誌的商標權歸各所有人。
- 騰訊圖示取自官方已安裝 WeMeetApp.exe 的圖示資源，僅識別啟動目標；不適用上述 Apache 授權。

啟動邏輯為本專案實作，沒有引入其他會議系統的登入 SDK。Google Meet 的捷徑名稱若經修改，可使用「設定路徑」選取。客戶端啟動成功不代表已登入或已預約成功。
