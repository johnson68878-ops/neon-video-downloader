"""Meeting launchers: registered Windows apps, known paths and PWA shortcuts."""
from dataclasses import dataclass
import json
import os
from pathlib import Path
import webbrowser


@dataclass(frozen=True)
class Provider:
    key: str
    name: str
    icon: str
    color: str
    web: str
    hint: str
    paths: tuple = ()
    shortcuts: tuple = ()
    protocols: tuple = ()


PROVIDERS = (
    Provider('zoom', 'Zoom', 'zoom.png', '#2563EB', 'https://zoom.us/meeting/schedule',
             '登入後選擇「排程」，設定會議日期與時間。',
             (('APPDATA','Zoom/bin/Zoom.exe'), ('ProgramFiles','Zoom/bin/Zoom.exe'),
              ('ProgramFiles(x86)','Zoom/bin/Zoom.exe'), ('LOCALAPPDATA','Zoom/bin/Zoom.exe')),
             ('Zoom.lnk','Zoom Workplace.lnk')),
    Provider('teams', 'Microsoft Teams', 'microsoft-teams.png', '#6264A7', 'https://teams.microsoft.com/v2/',
             '登入後在行事曆中排程會議；支援新版與傳統版 Teams。',
             (('LOCALAPPDATA','Microsoft/Teams/current/Teams.exe'),),
             ('Microsoft Teams.lnk','Microsoft Teams (work or school).lnk'),
             (('msteams','msteams:/l/meeting/new'),('ms-teams','ms-teams:'))),
    Provider('google-meet', 'Google Meet', 'google-meet.png', '#168447', 'https://meet.google.com/',
             '選擇「新會議」，再透過 Google 日曆安排時間。',
             shortcuts=('Google Meet.lnk','Google Meet - Google Chrome.lnk','Google Meet - Microsoft Edge.lnk')),
    Provider('tencent', '騰訊會議', 'tencent.png', '#1478D4', 'https://meeting.tencent.com/user-center',
             '登入後選擇「預定會議」，完成主題與時間設定。',
             (('ProgramFiles','Tencent/WeMeet/WeMeetApp.exe'),
              ('ProgramFiles(x86)','Tencent/WeMeet/WeMeetApp.exe'),
              ('LOCALAPPDATA','Tencent/WeMeet/WeMeetApp.exe')),
             ('腾讯会议.lnk','騰訊會議.lnk','Tencent Meeting.lnk')),
    Provider('webex', 'Webex', 'webex.png', '#087F8C', 'https://web.webex.com/',
             '登入 Webex 帳號，從會議頁面選擇排程。',
             (('LOCALAPPDATA','Programs/Cisco Spark/CiscoCollabHost.exe'),
              ('ProgramFiles','Cisco Spark/CiscoCollabHost.exe'),
              ('ProgramFiles(x86)','Cisco Spark/CiscoCollabHost.exe'),
              ('LOCALAPPDATA','Programs/Webex/Webex.exe')),
             ('Webex.lnk','Cisco Webex.lnk','Cisco Webex Meetings.lnk')),
)
BY_KEY = {p.key: p for p in PROVIDERS}
# Compatibility for the original Tencent-only entry point.
DEFAULT_CLIENT = Path(r'C:\Program Files\Tencent\WeMeet\WeMeetApp.exe')
WEB_URL = BY_KEY['tencent'].web


def config_path():
    root = Path(os.environ.get('LOCALAPPDATA') or Path.home()/'.config')
    return root/'MeetStudio'/'meeting-apps.json'


def load_overrides():
    try:
        value = json.loads(config_path().read_text(encoding='utf-8'))
        return {k:v for k,v in value.items() if k in BY_KEY and isinstance(v,str)}
    except (OSError, ValueError, AttributeError):
        return {}


def save_override(key, path):
    if key not in BY_KEY: raise ValueError('未知的會議服務')
    data = load_overrides()
    if path:
        candidate = Path(path).expanduser().resolve()
        if candidate.suffix.lower() not in ('.exe','.lnk') or not candidate.is_file():
            raise ValueError('請選擇已安裝程式的 EXE 或 Windows 捷徑（LNK）')
        data[key] = str(candidate)
    else:
        data.pop(key, None)
    target = config_path(); target.parent.mkdir(parents=True,exist_ok=True)
    temp = target.with_suffix('.tmp')
    temp.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
    temp.replace(target)


def registered_protocol(scheme):
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, scheme) as key:
            winreg.QueryValueEx(key, 'URL Protocol')
        return True
    except (ImportError, OSError):
        return False


def candidate_files(provider):
    for variable, relative in provider.paths:
        root = os.environ.get(variable)
        if not root and variable == 'ProgramFiles':root = r'C:\Program Files'
        if not root and variable == 'ProgramFiles(x86)':root = r'C:\Program Files (x86)'
        if root:yield Path(root)/relative


def start_menu_shortcuts(provider):
    names = {name.casefold() for name in provider.shortcuts}
    for variable in ('APPDATA','ProgramData'):
        root = os.environ.get(variable)
        if not root:continue
        folder = Path(root)/'Microsoft'/'Windows'/'Start Menu'/'Programs'
        try:
            for shortcut in folder.rglob('*.lnk'):
                if shortcut.name.casefold() in names and shortcut.is_file():
                    yield shortcut
        except OSError:
            continue


@dataclass(frozen=True)
class LocalTarget:
    value: str
    kind: str


def find_local(provider, overrides=None):
    overrides = load_overrides() if overrides is None else overrides
    custom = overrides.get(provider.key)
    if custom:
        file = Path(custom)
        if file.suffix.lower() in ('.exe','.lnk') and file.is_file():
            return LocalTarget(str(file),'custom')
    # MSIX Teams is versioned; a registered URI survives upgrades and alternate drives.
    for scheme, uri in provider.protocols:
        if registered_protocol(scheme):return LocalTarget(uri,'protocol')
    for file in candidate_files(provider):
        if file.is_file():return LocalTarget(str(file),'file')
    for file in start_menu_shortcuts(provider):
        return LocalTarget(str(file),'shortcut')
    return None


def open_web(provider):
    if not webbrowser.open(provider.web, new=2):
        raise OSError('無法開啟預設瀏覽器，請手動前往：'+provider.web)
    return 'web'


def open_provider(key, notify, web_only=False):
    provider = BY_KEY[key]
    if web_only:return open_web(provider)
    target = find_local(provider)
    if target:
        try:
            os.startfile(target.value)
            return 'desktop'
        except OSError:
            reason = '本機程式無法啟動。'
    else:
        reason = '未找到本機應用程式或已安裝的網頁應用捷徑。' if key=='google-meet' else '未找到本機應用程式。'
    notify('開啟 '+provider.name, reason+'\n將改用官方網頁登入與預約。\n'+provider.hint)
    return open_web(provider)


def find_client():
    target = find_local(BY_KEY['tencent'])
    return Path(target.value) if target else None


def open_scheduler(notify):
    # Keep existing integrations working while the new page uses open_provider.
    client = find_client()
    reason = '未檢測到騰訊會議電腦版。'
    if client:
        try:
            os.startfile(str(client)); return 'desktop'
        except OSError:reason = '騰訊會議電腦版無法啟動。'
    notify('騰訊會議網頁版',reason+'\n將開啟官方網頁個人中心，登入後選擇「預定會議」。')
    return open_web(BY_KEY['tencent'])
