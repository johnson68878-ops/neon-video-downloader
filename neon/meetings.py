"""Open Tencent Meeting locally, with an official web scheduling fallback."""
import os
import webbrowser
from pathlib import Path

DEFAULT_CLIENT = Path(r'C:\Program Files\Tencent\WeMeet\WeMeetApp.exe')
WEB_URL = 'https://meeting.tencent.com/user-center'


def find_client():
    candidates = [DEFAULT_CLIENT]
    for variable in ('ProgramFiles', 'ProgramFiles(x86)'):
        if os.environ.get(variable):
            candidates.append(Path(os.environ[variable])/'Tencent'/'WeMeet'/'WeMeetApp.exe')
    return next((path for path in candidates if path.is_file()), None)


def open_scheduler(notify):
    """Launch the client; notify before falling back. Does not create a meeting."""
    client = find_client()
    reason = '未檢測到騰訊會議電腦版。'
    if client:
        try:
            os.startfile(str(client))
            return 'desktop'
        except OSError:
            reason = '騰訊會議電腦版無法啟動。'
    notify('騰訊會議網頁版', reason + '\n將開啟騰訊會議官方網頁個人中心。\n登入後選擇“預定會議”，填寫時間並確認預約。')
    if not webbrowser.open(WEB_URL, new=2):
        raise OSError('無法開啟預設瀏覽器，請手動訪問：'+WEB_URL)
    return 'web'
