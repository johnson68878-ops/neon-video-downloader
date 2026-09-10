"""Local Windows recording: gdigrab video, WASAPI audio, recoverable segments."""
import ctypes
import json
import queue
import re
import shutil
import subprocess
import threading
import time
import uuid
from pathlib import Path
from .runtime import ROOT

FFMPEG = ROOT / 'binaries' / 'ffmpeg.exe'
FLAGS = getattr(subprocess, 'CREATE_NO_WINDOW', 0)


def monitors():
    from ctypes import wintypes
    result = []
    callback_type = ctypes.WINFUNCTYPE(ctypes.c_int, ctypes.c_void_p, ctypes.c_void_p,
                                       ctypes.POINTER(wintypes.RECT), ctypes.c_ssize_t)
    def visit(handle, dc, rect, data):
        r = rect.contents
        result.append((r.left, r.top, r.right-r.left, r.bottom-r.top))
        return 1
    callback = callback_type(visit)
    ctypes.windll.user32.EnumDisplayMonitors(None, None, callback, 0)
    return sorted(result, key=lambda r: (r[0] != 0 or r[1] != 0, r[0], r[1]))


def video_command(rect, height, compact, output):
    x, y, w, h = rect
    if height not in (720, 1080) or w < 16 or h < 16:
        raise ValueError('請選擇有效的錄製範圍和解析度')
    target_h = min(h, height)
    scale = f'scale=-2:{target_h//2*2},pad=ceil(iw/2)*2:ceil(ih/2)*2'
    return [str(FFMPEG), '-hide_banner', '-loglevel', 'warning', '-y',
            '-f', 'gdigrab', '-framerate', '15', '-draw_mouse', '1',
            '-offset_x', str(x), '-offset_y', str(y), '-video_size', f'{w}x{h}',
            '-i', 'desktop', '-an', '-vf', scale, '-c:v', 'libx264',
            '-preset', 'veryfast', '-crf', '29' if compact else '24',
            '-pix_fmt', 'yuv420p', '-r', '15', '-g', '30', str(output)]


def run_ffmpeg(args, log):
    with open(log, 'ab') as stream:
        result = subprocess.run([str(FFMPEG), '-hide_banner', '-loglevel', 'warning', '-y'] + args,
                                stdout=subprocess.DEVNULL, stderr=stream, creationflags=FLAGS)
    if result.returncode:
        raise RuntimeError(f'影片處理失敗，原始錄製已保留。診斷檔案：{log}')


def media_duration(path):
    probe = subprocess.run([str(FFMPEG), '-hide_banner', '-i', str(path)],
                           capture_output=True, creationflags=FLAGS, timeout=20)
    match = re.search(rb'Duration: (\d+):(\d+):(\d+\.\d+)', probe.stderr)
    if not match:
        raise RuntimeError('無法讀取錄製時長，原始檔案已保留：'+str(path))
    hours, minutes, seconds = map(float, match.groups())
    return hours*3600 + minutes*60 + seconds


class AudioTrack:
    """Encode continuously to AAC; never accumulate meeting-length PCM in memory."""
    def __init__(self, pa, device, output):
        import pyaudiowpatch as p
        self.frames = queue.Queue(maxsize=256)
        self.error = None
        self.start_time = None
        self.end_time = None
        self.channels = min(2, int(device['maxInputChannels']))
        self.rate = int(device['defaultSampleRate'])
        self.log = open(output.with_suffix('.log'), 'wb')
        self.process = subprocess.Popen([str(FFMPEG), '-hide_banner', '-loglevel', 'warning', '-y',
            '-f', 's16le', '-ar', str(self.rate), '-ac', str(self.channels), '-i', 'pipe:0',
            '-c:a', 'aac', '-b:a', '96k', str(output)], stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL, stderr=self.log, creationflags=FLAGS)
        def callback(data, count, info, status):
            if status:
                self.error = '音訊裝置發生丟幀，請檢查裝置或降低系統負載'
            try:
                self.frames.put_nowait((time.monotonic() - count / self.rate, data))
            except queue.Full:
                self.error = '音訊編碼速度不足，錄製已停止以避免音畫不同步'
                return (None, p.paAbort)
            return (None, p.paContinue)
        self.stream = None
        try:
            self.stream = pa.open(format=p.paInt16, channels=self.channels, rate=self.rate,
                                  input=True, input_device_index=device['index'],
                                  frames_per_buffer=1024, stream_callback=callback, start=False)
        except Exception:
            self.process.stdin.close(); self.process.wait(timeout=15); self.log.close()
            raise
        self.writer = threading.Thread(target=self._write, daemon=True)
        self.writer.start()

    def _write(self):
        written = 0
        sample_bytes = self.channels * 2
        def silence(count):
            # WASAPI loopback emits no callbacks while the output device is silent.
            # Fill the missing wall-clock interval instead of shifting the next speech earlier.
            while count > 0:
                chunk = min(count, self.rate)
                self.process.stdin.write(bytes(chunk * sample_bytes))
                count -= chunk
        try:
            while True:
                packet = self.frames.get()
                if packet is None:
                    if self.start_time and self.end_time:
                        silence(max(0, int((self.end_time-self.start_time)*self.rate)-written))
                    break
                timestamp, data = packet
                expected = max(0, int((timestamp-self.start_time)*self.rate))
                if expected-written > self.rate//10:
                    silence(expected-written)
                    written = expected
                self.process.stdin.write(data)
                written += len(data)//sample_bytes
        except Exception as exc:
            self.error = str(exc)
        finally:
            try:
                self.process.stdin.close()
            except OSError:
                pass

    def start(self):
        self.start_time = time.monotonic()
        self.stream.start_stream()

    def stop(self):
        self.end_time = time.monotonic()
        try:
            self.stream.stop_stream()
            self.stream.close()
        finally:
            if self.writer.is_alive():
                self.frames.put(None, timeout=10)
            self.writer.join(timeout=15)
            try:
                code = self.process.wait(timeout=20)
            except subprocess.TimeoutExpired:
                self.process.kill(); self.process.wait()
                code = -1
            self.log.close()
        if code or self.error:
            raise RuntimeError(self.error or '音訊編碼失敗')


class Recorder:
    def __init__(self, folder, rect, height=720, compact=True, system=True, microphone=False):
        self.folder = Path(folder).expanduser().resolve()
        self.folder.mkdir(parents=True, exist_ok=True)
        stamp = time.strftime('%Y%m%d-%H%M%S') + '-' + uuid.uuid4().hex[:6]
        self.output = self.folder / f'會議錄屏-{stamp}.mp4'
        self.work = self.folder / f'.錄製中-{stamp}'
        self.work.mkdir()
        self.rect, self.height, self.compact = rect, height, compact
        self.system, self.microphone = system, microphone
        self.segments = []
        self.active = False
        self.process = None
        self.duration = 0
        self.started = None
        self.tracks = []
        self.pa = None
        self.log = None
        self.last_error = None
        (self.work/'恢復說明.txt').write_text('錄製或合併意外中斷時請保留此資料夾。segment-*.mp4 是已完成片段；video-*.mkv 是原始畫面，audio-* 是對應聲音。\n', encoding='utf-8')

    def elapsed(self):
        return self.duration + (time.monotonic()-self.started if self.active else 0)

    def start(self):
        if self.active:
            return
        if shutil.disk_usage(self.folder).free < 256 * 1024 * 1024:
            raise RuntimeError('儲存磁碟剩餘空間不足 256 MB，請更換目錄後重試')
        import pyaudiowpatch as p
        n = len(self.segments)
        self.video = self.work / f'video-{n}.mkv'
        self.tracks = []
        self.pa = p.PyAudio() if self.system or self.microphone else None
        try:
            devices = []
            if self.system:
                try:
                    devices.append(self.pa.get_default_wasapi_loopback())
                except Exception as exc:
                    raise RuntimeError('未找到系統聲音裝置，請連線揚聲器/耳機，或關閉“系統聲音”後重試') from exc
            if self.microphone:
                try:
                    info = self.pa.get_host_api_info_by_type(p.paWASAPI)
                    devices.append(self.pa.get_device_info_by_index(info['defaultInputDevice']))
                except Exception as exc:
                    raise RuntimeError('未找到預設麥克風，請在 Windows 聲音設定中選擇輸入裝置') from exc
            for i, device in enumerate(devices):
                path = self.work / f'audio-{n}-{i}.m4a'
                self.tracks.append((AudioTrack(self.pa, device, path), path))
            self.log = open(self.work/f'video-{n}.log', 'wb')
            self.started = time.monotonic()
            self.process = subprocess.Popen(video_command(self.rect, self.height, self.compact, self.video),
                stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=self.log, creationflags=FLAGS)
            for track, path in self.tracks:
                track.start()
            time.sleep(.6)
            if self.process.poll() is not None:
                raise RuntimeError('無法錄製所選螢幕，請重新選擇範圍。詳情：'+str(self.work))
            self.active = True
        except Exception:
            self._close_inputs()
            raise

    def _close_inputs(self):
        errors = []
        if self.process and self.process.poll() is None:
            try:
                self.process.stdin.write(b'q\n'); self.process.stdin.flush()
                self.process.wait(timeout=20)
            except Exception:
                self.process.kill(); self.process.wait()
                errors.append('畫面錄製未正常結束，原始檔案已保留')
        for track, path in self.tracks:
            try:
                track.stop()
            except Exception as exc:
                errors.append(str(exc))
        self.tracks_closed = True
        if self.pa:
            self.pa.terminate(); self.pa = None
        if self.log:
            self.log.close(); self.log = None
        return errors

    def pause(self, progress=None):
        if not self.active:
            return
        if progress: progress(.10, '正在結束螢幕與聲音錄製…')
        self.duration = self.elapsed()
        self.active = False
        errors = self._close_inputs()
        if self.process.returncode or errors:
            self.last_error = '; '.join(errors) or '螢幕錄製意外結束'
            raise RuntimeError(self.last_error + f'。原始檔案：{self.work}')
        output = self.work / f'segment-{len(self.segments)}.mp4'
        duration = media_duration(self.video)
        if progress: progress(.36, '正在合併畫面與聲音…')
        args = ['-i', str(self.video)]
        filters = []
        for index, (track, path) in enumerate(self.tracks, 1):
            args += ['-i', str(path)]
            delay = max(0, int(((track.start_time or self.started)-self.started)*1000))
            filters.append(f'[{index}:a]aresample=48000,adelay={delay}:all=1,apad=whole_dur={duration}[a{index}]')
        args += ['-map', '0:v', '-c:v', 'copy']
        if filters:
            names = ''.join(f'[a{i}]' for i in range(1, len(filters)+1))
            filters.append(names+f'amix=inputs={len(self.tracks)}:normalize=1:duration=longest[mix]')
            args += ['-filter_complex', ';'.join(filters), '-map', '[mix]', '-c:a', 'aac',
                     '-b:a', '96k', '-ac', '2', '-ar', '48000', '-shortest']
        args += ['-t', str(duration), '-movflags', '+faststart', str(output)]
        try:
            run_ffmpeg(args, self.work/'merge.log')
        except Exception as exc:
            self.last_error = str(exc)
            raise
        self.segments.append(output)
        self.video.unlink(missing_ok=True)
        for track, path in self.tracks:
            path.unlink(missing_ok=True)
        if progress: progress(.72, '目前錄製片段已完成整理…')

    def finish(self, progress=None):
        if self.last_error:
            raise RuntimeError(self.last_error + f'。原始檔案：{self.work}')
        if progress: progress(.03, '正在完成錄製，請勿關閉程式…')
        self.pause(progress)
        if not self.segments:
            raise RuntimeError('沒有可儲存的錄製片段。請保留恢復資料夾：'+str(self.work))
        listing = self.work/'concat.txt'
        listing.write_text(''.join(f"file '{p.name}'\n" for p in self.segments), encoding='utf-8')
        # Work on a temporary MP4 so an interrupted merge never masquerades as a finished recording.
        staging = self.work/'final.mp4'
        if progress: progress(.78, '正在合併錄製片段…')
        run_ffmpeg(['-f', 'concat', '-safe', '0', '-i', str(listing), '-c', 'copy',
                    '-movflags', '+faststart', str(staging)], self.work/'merge.log')
        if progress: progress(.94, '正在寫入最終 MP4…')
        staging.replace(self.output)
        # Only remove this session's directory after the MP4 is safely published.
        if self.work.parent == self.folder and self.work.name.startswith('.錄製中-'):
            shutil.rmtree(self.work)
        if progress: progress(1, 'MP4 已儲存完成')
        return self.output
