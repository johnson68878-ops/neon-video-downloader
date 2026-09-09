"""NOVA Studio — Traditional Chinese native desktop shell."""
import ctypes
import json
import os
import queue
import sys
import threading
import time
from pathlib import Path
import customtkinter as ctk
from tkinter import filedialog, messagebox
from .runtime import ROOT
from .recorder import Recorder, monitors
from .download_ui import build_download
from .meeting_ui import MeetingPage

BG = '#F3F6FB'
INK = '#182D48'
MUTED = '#586C84'
BLUE = '#1262CC'
TEAL = '#087F8C'
FONT = 'Microsoft YaHei UI'
VERSION = '2.2.1'


def label(parent, text, size=14, color=INK, bold=False, **kw):
    return ctk.CTkLabel(parent, text=text, text_color=color,
                        font=(FONT, size, 'bold' if bold else 'normal'), **kw)


def button(parent, text, command, color=BLUE, **kw):
    return ctk.CTkButton(parent, text=text, command=command, fg_color=color if kw.get('state') != 'disabled' else '#E1E7EF', text_color_disabled='#8290A3',
                         hover_color='#244E79', height=40, corner_radius=9,
                         font=(FONT, 13), **kw)


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title('曜影 NOVA Studio · 錄屏與影音下載')
        scale = self._get_window_scaling()
        width = max(960, min(1180, int(self.winfo_screenwidth()/scale)-60))
        height = max(600, min(820, int(self.winfo_screenheight()/scale)-80))
        self.minsize(960, 600); self.geometry(f'{width}x{height}+20+20')
        if (ROOT/'assets'/'meetstudio.ico').exists():self.iconbitmap(str(ROOT/'assets'/'meetstudio.ico'))
        self.configure(fg_color=BG)
        self.events = queue.Queue(); self.recorder = None
        self.record_state = 'idle'; self.last_file = None; self.region = None
        self.countdown_id = None; self.floatbar = None
        self.grid_columnconfigure(1, weight=1); self.grid_rowconfigure(1, weight=1)
        header = ctk.CTkFrame(self, fg_color='white', corner_radius=0, height=68)
        header.grid(row=0, column=0, columnspan=2, sticky='ew'); header.pack_propagate(False)
        label(header, 'NOVA', 23, BLUE, True).pack(side='left', padx=(24, 22))
        label(header, '曜影工作站', 21, INK, True).pack(side='left')
        label(header, 'Studio', 13, MUTED).pack(side='left', padx=10)
        self.meeting_button = button(header, '會議預約', lambda:self.show('會議預約'), width=140)
        self.meeting_button.pack(side='right', padx=25)
        self.meeting_hint = label(header, 'Zoom · Teams · Meet · 更多', 12, MUTED)
        self.meeting_hint.pack(side='right')
        sidebar = ctk.CTkFrame(self, width=185, corner_radius=0, fg_color='#EAF0F8')
        sidebar.grid(row=1, column=0, sticky='nsew'); sidebar.grid_propagate(False)
        label(sidebar, '工作空間', 12, MUTED).pack(anchor='w', padx=22, pady=(27, 15))
        self.nav = {}
        for name in ['會議錄屏', '影音下載', '會議預約', '關於程式']:
            b = button(sidebar, name, lambda n=name: self.show(n), width=150)
            b.pack(padx=16, pady=5); self.nav[name] = b
        label(sidebar, f'版本 {VERSION}\nWindows · 本地儲存', 11, MUTED, justify='left').pack(side='bottom', anchor='w', padx=22, pady=16)
        self.body = ctk.CTkFrame(self, fg_color=BG, corner_radius=0)
        self.body.grid(row=1, column=1, sticky='nsew'); self.body.grid_columnconfigure(0, weight=1); self.body.grid_rowconfigure(0, weight=1)
        self.pages = {}
        self.record_page = self.make_record(); self.pages['會議錄屏'] = self.record_page
        self.download = build_download(self.body); self.pages['影音下載'] = self.download
        self.meeting_page = MeetingPage(self.body); self.pages['會議預約'] = self.meeting_page
        self.pages['關於程式'] = self.make_about()
        self.show('會議錄屏')
        self.protocol('WM_DELETE_WINDOW', self.close)
        self.after(100, self.poll)

    def show(self, name):
        for p in self.pages.values(): p.grid_remove()
        self.pages[name].grid(row=0, column=0, sticky='nsew')
        for title, b in self.nav.items():
            b.configure(fg_color=BLUE if title == name else '#EAF0F8',
                        text_color='white' if title == name else MUTED)
        self.current_page = name

    def make_record(self):
        page = ctk.CTkScrollableFrame(self.body, fg_color=BG)
        page.grid_columnconfigure(0, weight=1)
        label(page, '會議錄屏', 28, INK, True).grid(row=0, column=0, sticky='w', padx=28, pady=(23, 0))
        label(page, '適用於會議、培訓和操作演示。', 13, MUTED).grid(row=1, column=0, sticky='w', padx=28, pady=(4, 17))
        hero = ctk.CTkFrame(page, fg_color='#E4EEFF', corner_radius=18)
        hero.grid(row=2, column=0, sticky='ew', padx=28); hero.grid_columnconfigure(0, weight=1)
        label(hero, '錄製螢幕與會議聲音', 21, INK, True).grid(row=0, column=0, sticky='w', padx=24, pady=(20, 2))
        label(hero, 'MP4  ·  720p / 1080p  ·  系統聲音 + 麥克風', 12, MUTED).grid(row=1, column=0, sticky='w', padx=24, pady=(0, 18))
        self.timer = label(hero, '00:00:00', 31, BLUE, True)
        self.timer.grid(row=0, column=1, rowspan=2, padx=25)
        settings = ctk.CTkFrame(page, fg_color='white', corner_radius=16)
        settings.grid(row=3, column=0, sticky='ew', padx=28, pady=16)
        settings.grid_columnconfigure(1, weight=1)
        self.rects = monitors()
        self.monitor_names = [f'螢幕 {i+1}  ·  {r[2]} × {r[3]}' for i, r in enumerate(self.rects)]
        label(settings, '錄製範圍', 13, INK, True).grid(row=0, column=0, padx=20, pady=(20, 12), sticky='w')
        self.screen = ctk.CTkOptionMenu(settings, values=self.monitor_names, command=self.reset_region, fg_color=BLUE, width=245)
        self.screen.grid(row=0, column=1, sticky='w', pady=(20,12))
        self.select_region = button(settings, '框選區域', self.pick_region, color=TEAL, width=108)
        self.select_region.grid(row=0, column=2, padx=20, pady=(20,12))
        self.area_hint = label(settings, '錄製所選螢幕的完整畫面', 11, MUTED)
        self.area_hint.grid(row=1, column=1, columnspan=2, sticky='w', pady=(0, 10))
        label(settings, '畫面質量', 13, INK, True).grid(row=2, column=0, padx=20, pady=10, sticky='w')
        quality_row = ctk.CTkFrame(settings, fg_color='transparent'); quality_row.grid(row=2,column=1,columnspan=2,sticky='w')
        self.resolution = ctk.CTkSegmentedButton(quality_row, values=['720p 推薦', '1080p 清晰'], font=(FONT,13), selected_color=BLUE, height=35)
        self.resolution.pack(side='left'); self.resolution.set('720p 推薦')
        self.compact = ctk.CTkCheckBox(quality_row, text='優先小檔案', font=(FONT,12), width=135)
        self.compact.pack(side='left', padx=20); self.compact.select()
        label(settings, '聲音來源', 13, INK, True).grid(row=3, column=0, padx=20, pady=14, sticky='w')
        audio = ctk.CTkFrame(settings, fg_color='transparent'); audio.grid(row=3,column=1,columnspan=2,sticky='w')
        self.system = ctk.CTkSwitch(audio, text='系統聲音', font=(FONT,13)); self.system.pack(side='left'); self.system.select()
        self.mic = ctk.CTkSwitch(audio, text='麥克風', font=(FONT,13)); self.mic.pack(side='left', padx=28)
        label(settings, '使用 Windows 預設音訊裝置；會議建議佩戴耳機以減少回聲。', 11, MUTED).grid(row=4,column=1,columnspan=2,sticky='w',pady=(0,13))
        label(settings, '儲存位置', 13, INK, True).grid(row=5,column=0,padx=20,pady=(0,20),sticky='w')
        self.folder = ctk.CTkEntry(settings, height=35); self.folder.grid(row=5,column=1,sticky='ew',pady=(0,20))
        self.folder.insert(0, str(Path.home()/'Videos'/'NEON MeetStudio'))
        self.browse = button(settings, '更改目錄', self.choose_folder, width=108)
        self.browse.grid(row=5,column=2,padx=20,pady=(0,20))
        bar = ctk.CTkFrame(page, fg_color='transparent'); bar.grid(row=4,column=0,sticky='ew',padx=28)
        self.start = button(bar, '開始錄製', self.begin, color='#DA4254', width=170); self.start.pack(side='left')
        self.pause_button = button(bar, '暫停', self.pause_resume, width=95, state='disabled'); self.pause_button.pack(side='left',padx=10)
        self.stop_button = button(bar, '停止並儲存', self.stop_record, width=115, state='disabled'); self.stop_button.pack(side='left')
        button(bar, '開啟資料夾', self.open_folder, width=115).pack(side='right')
        self.status = label(page, '準備就緒 · 開始後倒計時 3 秒，可隨時暫停。', 13, TEAL)
        self.status.grid(row=5,column=0,sticky='w',padx=28,pady=(17,5))
        label(page, '會議模式：15 幀/秒，優先保留文字細節。成片大小隨時長和畫面變化而變化。', 11, MUTED).grid(row=6,column=0,sticky='w',padx=28)
        self.result = ctk.CTkFrame(page, fg_color='white', corner_radius=12)
        self.result.grid(row=7,column=0,sticky='ew',padx=28,pady=16); self.result.grid_columnconfigure(0,weight=1)
        self.result_text = label(self.result, '最近錄製\n完成後的 MP4 會顯示在這裡。', 12, MUTED, justify='left', anchor='w', wraplength=580)
        self.result_text.grid(row=0,column=0,sticky='ew',padx=18,pady=14)
        self.play = button(self.result,'播放',self.play_last,width=70,state='disabled'); self.play.grid(row=0,column=1,padx=16)
        self.controls = [self.screen,self.select_region,self.resolution,self.compact,self.system,self.mic,self.folder,self.browse]
        return page

    def make_about(self):
        page = ctk.CTkScrollableFrame(self.body, fg_color=BG)
        label(page, '關於曜影 NOVA Studio', 28, INK, True).pack(anchor='w',padx=28,pady=(25,5))
        label(page, '錄屏與影音下載  /  '+VERSION, 13, MUTED).pack(anchor='w',padx=28,pady=(0,24))
        author = ctk.CTkFrame(page, fg_color='white', corner_radius=18)
        author.pack(fill='x', padx=28, pady=(0,18))
        label(author, '開發者', 13, TEAL, True).pack(anchor='w', padx=28, pady=(22,8))
        label(author, '聯發科最後的清流 小胖老師帥哥凱', 19, BLUE, True, wraplength=580, justify='left').pack(anchor='w', padx=28, pady=(0,10))
        label(author, '黃仲凱  John Huang', 18, INK, True).pack(anchor='w', padx=28, pady=(0,12))
        label(author, '電話：+886-913229579\n郵件：kai.huang@msa.hinet.net', 14, MUTED, justify='left').pack(anchor='w', padx=28, pady=(0,22))
        card = ctk.CTkFrame(page, fg_color='white', corner_radius=18); card.pack(fill='x',padx=28)
        label(card, '一個工作站，處理會議與影音', 24, BLUE, True).pack(anchor='w',padx=28,pady=(25,15))
        for title, body in [
            ('會議錄屏', '整屏或框選區域，720p / 1080p MP4。支援系統聲音、麥克風、暫停與繼續錄製。'),
            ('影音下載', '貼上網址或分享文字，選擇畫質、音訊或字幕，並儲存到自己的資料夾。'),
            ('會議預約', '提供 Zoom、Teams、Google Meet、騰訊會議與 Webex。本機優先，未安裝時開啟官方網頁。'),
            ('檔案與隱私', '錄製檔案儲存在本機。程式不會自動上傳錄屏，也不會代替你建立會議。')]:
            section=ctk.CTkFrame(card,fg_color='#EAF2FF',corner_radius=12)
            section.pack(fill='x',padx=28,pady=8)
            label(section,title,17,INK,True).pack(anchor='w',padx=18,pady=(14,4))
            label(section,body,13,MUTED,wraplength=650,justify='left').pack(anchor='w',padx=18,pady=(0,14))
        label(card,'v'+VERSION+'  ·  Windows',12,MUTED).pack(anchor='w',padx=28,pady=20)
        label(page,'開源元件與許可見隨程式附帶的 licenses。',12,MUTED).pack(anchor='w',padx=28,pady=20)
        return page

    def reset_region(self, value=None):
        self.region=None; self.area_hint.configure(text='錄製所選螢幕的完整畫面')

    def pick_region(self):
        import tkinter as tk
        x,y,w,h=self.rects[self.monitor_names.index(self.screen.get())]
        overlay=tk.Toplevel(self); overlay.overrideredirect(True)
        overlay.geometry(f'{w}x{h}{x:+d}{y:+d}'); overlay.attributes('-topmost',True); overlay.attributes('-alpha',.40)
        canvas=tk.Canvas(overlay,bg='#10233D',cursor='crosshair',highlightthickness=0); canvas.pack(fill='both',expand=True)
        canvas.create_text(w//2,45,text='拖動選擇錄製區域  ·  Esc 取消',fill='white',font=(FONT,20))
        point={}
        def down(e):
            point['x'],point['y']=e.x,e.y
            canvas.delete('selection')
            point['item']=canvas.create_rectangle(e.x,e.y,e.x,e.y,outline='#9BDFFF',width=4,tags='selection')
        def drag(e):
            if 'item' in point: canvas.coords(point['item'],point['x'],point['y'],e.x,e.y)
        def up(e):
            if 'x' not in point:return
            a,b=sorted((max(0,min(w,e.x)),point['x'])); c,d=sorted((max(0,min(h,e.y)),point['y']))
            if b-a>=64 and d-c>=64:
                self.region=(x+a,y+c,b-a,d-c); self.area_hint.configure(text=f'自定義區域：{b-a} × {d-c} 畫素'); overlay.destroy()
        canvas.bind('<ButtonPress-1>',down); canvas.bind('<B1-Motion>',drag); canvas.bind('<ButtonRelease-1>',up)
        overlay.bind('<Escape>',lambda e:overlay.destroy()); overlay.grab_set(); overlay.focus_force()

    def choose_folder(self):
        p=filedialog.askdirectory(parent=self)
        if p:self.folder.delete(0,'end'); self.folder.insert(0,p)

    def open_folder(self):
        try:
            p=Path(self.folder.get()).expanduser(); p.mkdir(parents=True,exist_ok=True); os.startfile(p)
        except Exception as e:messagebox.showerror('無法開啟目錄',str(e),parent=self)

    def play_last(self):
        if self.last_file:
            try:os.startfile(self.last_file)
            except OSError as e:messagebox.showerror('無法播放',str(e),parent=self)

    def set_state(self,state,text):
        self.record_state=state; self.status.configure(text=text)
        for w in self.controls:w.configure(state='normal' if state=='idle' else 'disabled')
        self.start.configure(state='normal' if state=='idle' else 'disabled',fg_color='#DA4254' if state=='idle' else '#E1E7EF')
        self.pause_button.configure(state='normal' if state in ('recording','paused') else 'disabled',text='繼續錄製' if state=='paused' else '暫停',fg_color=BLUE if state in ('recording','paused') else '#E1E7EF')
        self.stop_button.configure(state='normal' if state in ('recording','paused','countdown') else 'disabled',fg_color=BLUE if state in ('recording','paused','countdown') else '#E1E7EF')
        if self.floatbar and self.floatbar.winfo_exists():
            self.float_pause.configure(state='normal' if state in ('recording','paused') else 'disabled',text='繼續' if state=='paused' else '暫停')
            self.float_stop.configure(state='normal' if state in ('recording','paused') else 'disabled')

    def background(self, action, success):
        def work():
            try:self.events.put((success,action()))
            except Exception as exc:self.events.put(('error',str(exc)))
        threading.Thread(target=work,daemon=True).start()

    def begin(self):
        if self.record_state!='idle':return
        if not self.folder.get().strip():
            messagebox.showerror('請選擇目錄','請先設定儲存位置。',parent=self); return
        rect=self.region or self.rects[self.monitor_names.index(self.screen.get())]
        self.pending=(self.folder.get(),rect,1080 if self.resolution.get().startswith('1080') else 720,bool(self.compact.get()),bool(self.system.get()),bool(self.mic.get()))
        self.set_state('countdown','3 秒後開始錄製…')
        self.countdown(3)

    def countdown(self,n):
        if self.record_state!='countdown':return
        if n:
            self.status.configure(text=f'{n} 秒後開始錄製… 點選“停止並儲存”可取消。')
            self.countdown_id=self.after(1000,lambda:self.countdown(n-1)); return
        self.set_state('starting','正在準備螢幕與聲音裝置…')
        def start():
            self.recorder=Recorder(*self.pending); self.recorder.start()
        self.background(start,'started')

    def floating(self):
        if self.floatbar and self.floatbar.winfo_exists():return
        self.floatbar=ctk.CTkToplevel(self); self.floatbar.title('NOVA Studio · 錄製中')
        self.floatbar.geometry('440x70+30+30'); self.floatbar.resizable(False,False); self.floatbar.attributes('-topmost',True)
        self.floatbar.configure(fg_color='white')
        self.float_time=label(self.floatbar,'錄製中  00:00:00',14,BLUE,True); self.float_time.pack(side='left',padx=15)
        self.float_pause=button(self.floatbar,'暫停',self.pause_resume,width=65); self.float_pause.pack(side='left',padx=5)
        self.float_stop=button(self.floatbar,'停止',self.stop_record,color='#DA4254',width=65); self.float_stop.pack(side='left')
        self.floatbar.protocol('WM_DELETE_WINDOW',self.restore)
        # Keep the controller out of captured pixels on supported Windows versions.
        self.floatbar.update_idletasks()
        try:
            hwnd=ctypes.windll.user32.GetParent(self.floatbar.winfo_id())
            ctypes.windll.user32.SetWindowDisplayAffinity(ctypes.c_void_p(hwnd),0x11)
        except Exception:pass
        self.iconify()

    def restore(self):
        self.deiconify(); self.lift()
        if self.floatbar:self.floatbar.destroy(); self.floatbar=None

    def pause_resume(self):
        if self.record_state=='recording':
            self.set_state('pausing','正在儲存當前片段…'); self.background(self.recorder.pause,'paused')
        elif self.record_state=='paused':
            self.set_state('starting','正在恢復錄製…'); self.background(self.recorder.start,'started')

    def stop_record(self):
        if self.record_state=='countdown':
            if self.countdown_id:self.after_cancel(self.countdown_id)
            self.set_state('idle','已取消錄製'); return
        if self.record_state not in ('recording','paused'):return
        self.set_state('saving','正在整理 MP4，請稍候…'); self.background(self.recorder.finish,'saved')

    def poll(self):
        for _ in range(20):
            try:kind,value=self.events.get_nowait()
            except queue.Empty:break
            if kind=='started':self.set_state('recording','正在錄製 · 暫停期間不會計入影片'); self.floating()
            elif kind=='paused':self.set_state('paused','已暫停 · 點選“繼續錄製”接著錄')
            elif kind=='saved':
                self.last_file=str(value); self.restore(); self.set_state('idle','已儲存 MP4')
                self.result_text.configure(text=f'最近錄製  ·  {Path(value).stat().st_size/1048576:.1f} MB\n{value}')
                self.play.configure(state='normal',fg_color=BLUE)
            elif kind=='error':
                self.restore(); self.set_state('idle','錄製未完成，請檢查提示後重試')
                messagebox.showerror('錄製提示',value,parent=self)
        if self.recorder and self.record_state!='idle':
            seconds=int(self.recorder.elapsed()); text=f'{seconds//3600:02d}:{seconds//60%60:02d}:{seconds%60:02d}'
            self.timer.configure(text=text)
            if self.floatbar:self.float_time.configure(text=('已暫停  ' if self.record_state=='paused' else '錄製中  ')+text)
            if self.record_state=='recording':
                failed=self.recorder.process.poll() is not None or any(t.error for t,p in self.recorder.tracks)
                if failed:self.stop_record()
        self.after(150,self.poll)

    def close(self):
        if self.record_state=='countdown':self.stop_record()
        if self.record_state!='idle':
            messagebox.showinfo('請先儲存錄制','請先點選“停止並儲存”，等待 MP4 儲存完成後再退出。',parent=self); return
        if self.download.busy:
            if not messagebox.askyesno('退出程式','下載仍在進行，停止下載並退出？',parent=self):return
            self.download.cancelled=True; self.download.kill()
        self.destroy()


def gui():
    ctk.set_appearance_mode('light'); ctk.set_default_color_theme('blue')
    app=App()
    if '--ui-test' in sys.argv:
        target=Path(sys.argv[sys.argv.index('--ui-test')+1])
        def check():
            from PIL import ImageGrab
            import pyaudiowpatch
            with pyaudiowpatch.PyAudio() as audio:
                device_count=audio.get_device_count()
            results={'audio_device_count':device_count}
            for name in app.pages:
                app.show(name); app.update()
                box=(app.winfo_rootx(),app.winfo_rooty(),app.winfo_rootx()+app.winfo_width(),app.winfo_rooty()+app.winfo_height())
                ImageGrab.grab(bbox=box).save(target.with_name(target.stem+'-'+name+'.png'))
                results[name]={'width':app.winfo_width(),'height':app.winfo_height()}
            target.write_text(json.dumps(results,ensure_ascii=False),encoding='utf-8'); app.destroy()
        app.after(1800,check)
    app.mainloop()
