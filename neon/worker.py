"""背景下載程式：JSON 任務輸入，JSONL 事件輸出。"""
import json
from pathlib import Path
from .downloader import options
from .urls import platform_name

def video_summary(info):
    """只回傳顯示所需資料，不把串流網址／權杖寫入介面事件。"""
    if info.get('entries') is not None:
        info = next((entry for entry in info['entries'] if entry), info)
    heights = sorted({int(f['height']) for f in info.get('formats', [])
                      if f.get('height') and f.get('vcodec') != 'none'}, reverse=True)
    return {'title': info.get('title', '未命名影片'), 'heights': heights,
            'extractor': info.get('extractor_key') or info.get('extractor', '')}

def worker(job):
    import yt_dlp
    def emit(kind, **data):
        print(json.dumps(dict(kind=kind, **data), ensure_ascii=True), flush=True)
    class Logger:
        def debug(self, msg): pass
        def warning(self, msg): emit('log', text=str(msg))
        def error(self, msg): emit('log', text=str(msg))
    def hook(d):
        total = d.get('total_bytes') or d.get('total_bytes_estimate') or 0
        emit('progress', fraction=min(d.get('downloaded_bytes',0)/total,1) if total else 0,
             speed=d.get('speed') or 0, eta=d.get('eta'), title=Path(d.get('filename','')).name,
             status=d['status'])
    opts = options(job, hook)
    opts['logger'] = Logger()
    for index, url in enumerate(job['urls']):
        emit('item', index=index, platform=platform_name(url))
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=not job.get('inspect'))
            if info is None: raise RuntimeError('網站未傳回影片資訊')
            emit('success', **video_summary(info), inspect=job.get('inspect',False))
        except Exception as exc:
            emit('error', text=str(exc))
    emit('done')

