"""yt-dlp 選項與解析度設定。"""
from pathlib import Path
from .runtime import ROOT

QUALITY_CHOICES = ['最佳畫質', '2160p', '1440p', '1080p', '720p', '480p', '360p', 'MP3 音訊']

def options(job, hook=None):
    opts = dict(outtmpl=str(Path(job['folder']) / '%(title).160B [%(id)s].%(ext)s'),
                windowsfilenames=True, noplaylist=True, playlist_items='1', retries=3, fragment_retries=3,
                socket_timeout=20, continuedl=True, quiet=True, no_warnings=False,
                progress_hooks=[hook] if hook else [], ffmpeg_location=str(ROOT / 'binaries'),
                merge_output_format='mp4', concurrent_fragment_downloads=4)
    node = ROOT / 'binaries' / 'node.exe'
    if node.exists(): opts['js_runtimes'] = {'node': {'path': str(node)}}
    quality = job['quality']
    if quality == 'MP3 音訊':
        opts.update(format='bestaudio/best', postprocessors=[{'key':'FFmpegExtractAudio','preferredcodec':'mp3','preferredquality':'192'}])
    else:
        if quality not in QUALITY_CHOICES:
            raise ValueError('不支援的畫質設定')
        height = int(quality[:-1]) if quality.endswith('p') else None
        lim = f'[height<=?{height}]' if height else ''
        opts['format'] = f'bv*{lim}+ba/b{lim}'
    if job.get('subtitles'):
        opts.update(writesubtitles=True, writeautomaticsub=True, subtitleslangs=['zh.*','en'], subtitlesformat='srt/best')
    return opts

