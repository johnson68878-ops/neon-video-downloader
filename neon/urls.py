"""從網址或平臺分享文字取出連結；平臺標籤不代替 yt-dlp 解析器。"""
import re
from urllib.parse import urlsplit

PLATFORMS = {
    'YouTube': ('youtube.com', 'youtu.be', 'youtube-nocookie.com'),
    '抖音': ('douyin.com', 'iesdouyin.com'),
    'TikTok': ('tiktok.com',),
    'Facebook': ('facebook.com', 'fb.watch', 'fb.com'),
    'Instagram': ('instagram.com',),
    'Bilibili': ('bilibili.com', 'b23.tv'),
    'X / Twitter': ('x.com', 'twitter.com', 't.co'),
    'Vimeo': ('vimeo.com',),
    'Twitch': ('twitch.tv', 'clips.twitch.tv'),
}

def valid_urls(text):
    found = re.findall(r'https?://[^\s<>"\u3000，。！？；、【】「」『』]+', text, flags=re.I)
    urls = []
    for value in found:
        value = value.rstrip('.,;!?:，。！；）')
        while value.endswith(')') and value.count(')') > value.count('('):
            value = value[:-1]
        try:
            parsed = urlsplit(value)
            if not parsed.hostname or parsed.username or parsed.password:
                raise ValueError()
            parsed.port  # 驗證連線埠格式
        except ValueError:
            raise ValueError('連結格式不正確，請重新複製影片網址。') from None
        if value not in urls:
            urls.append(value)
    if not urls:
        raise ValueError('請貼上 http / https 影片網址，也可貼平臺的整段分享文字。')
    return urls

def platform_name(url):
    host = (urlsplit(url).hostname or '').lower()
    return next((name for name, domains in PLATFORMS.items()
                 if any(host == d or host.endswith('.' + d) for d in domains)), '其他網站 / 直接影片')
