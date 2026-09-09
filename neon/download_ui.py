"""繁體中文桌面介面與背景程式控制。"""
import json, os, sys, queue, subprocess, threading, time, tempfile
from pathlib import Path
from .runtime import ROOT
from .urls import valid_urls, platform_name
from .downloader import QUALITY_CHOICES

def build_download(parent):
    import customtkinter as ctk
    from tkinter import filedialog, messagebox
    ctk.set_appearance_mode('light')
    ctk.set_default_color_theme('blue')
    BG, PANEL, MUTED, GREEN = '#F3F6FB', '#FFFFFF', '#52657B', '#087F8C'
    class App(ctk.CTkFrame):
        def __init__(self):
            super().__init__(parent, fg_color=BG)
            self.events = queue.Queue(); self.process = None; self.busy = False; self.cancelled = False
            self.ok = self.failed = 0
            self.grid_columnconfigure(0,weight=1); self.grid_rowconfigure(0,weight=1)
            main=ctk.CTkFrame(self,fg_color='transparent'); main.grid(row=0,column=0,sticky='nsew',padx=30,pady=25)
            main.grid_columnconfigure(0,weight=1); main.grid_rowconfigure(7,weight=1)
            ctk.CTkLabel(main,text='影音下載',font=('Microsoft YaHei UI',28,'bold')).grid(row=0,column=0,sticky='w')
            ctk.CTkLabel(main,text='YouTube / 抖音 / Facebook / TikTok / Instagram / 更多平臺',text_color=MUTED,font=('Microsoft YaHei UI',13)).grid(row=1,column=0,sticky='w',pady=(5,20))
            card=ctk.CTkFrame(main,fg_color=PANEL,corner_radius=16); card.grid(row=2,column=0,sticky='ew'); card.grid_columnconfigure(0,weight=1)
            top=ctk.CTkFrame(card,fg_color='transparent'); top.grid(row=0,column=0,sticky='ew',padx=20,pady=(15,8))
            ctk.CTkLabel(top,text='01  /  影片連結',font=('Microsoft YaHei UI',15,'bold')).pack(side='left')
            ctk.CTkButton(top,text='貼上連結',width=110,fg_color='#3568AC',hover_color='#27538D',command=self.paste).pack(side='right')
            self.links=ctk.CTkTextbox(card,height=95,fg_color='#F7F9FC',border_width=1,border_color='#D8E1EC',font=('Segoe UI',13)); self.links.grid(row=1,column=0,sticky='ew',padx=20)
            self.links.bind('<<Paste>>', lambda event: self.after(120, self.auto_paste), add='+')
            ctk.CTkLabel(card,text='可直接貼分享文字 • 先選畫質再貼上 • 自動識別平臺',text_color=MUTED,font=('Microsoft YaHei UI',11)).grid(row=2,column=0,sticky='w',padx=20,pady=(5,12))
            settings=ctk.CTkFrame(main,fg_color=PANEL,corner_radius=16); settings.grid(row=3,column=0,sticky='ew',pady=14); settings.grid_columnconfigure(0,weight=1)
            ctk.CTkLabel(settings,text='02  /  下載偏好',font=('Microsoft YaHei UI',15,'bold')).grid(row=0,column=0,sticky='w',padx=20,pady=(12,8))
            row=ctk.CTkFrame(settings,fg_color='transparent'); row.grid(row=1,column=0,sticky='ew',padx=20)
            self.quality=ctk.CTkOptionMenu(row,values=QUALITY_CHOICES,fg_color='#3568AC',button_color='#27538D',width=155); self.quality.pack(side='left')
            self.sub=ctk.CTkCheckBox(row,text='下載字幕（中 / 英）',font=('Microsoft YaHei UI',12),fg_color='#258E7B'); self.sub.pack(side='left',padx=25)
            self.auto=ctk.CTkCheckBox(row,text='貼上即下載',font=('Microsoft YaHei UI',12),fg_color='#258E7B',width=110)
            self.auto.pack(side='left'); self.auto.select()
            folderrow=ctk.CTkFrame(settings,fg_color='transparent'); folderrow.grid(row=2,column=0,sticky='ew',padx=20,pady=(12,16)); folderrow.grid_columnconfigure(0,weight=1)
            self.folder=ctk.CTkEntry(folderrow,height=34); self.folder.grid(row=0,column=0,sticky='ew'); self.folder.insert(0,str(Path.home()/'Downloads'/'NEON MeetStudio'))
            ctk.CTkButton(folderrow,text='選擇資料夾',width=105,fg_color='#3568AC',command=self.choose).grid(row=0,column=1,padx=(10,0))
            actions=ctk.CTkFrame(main,fg_color='transparent'); actions.grid(row=4,column=0,sticky='ew',pady=(0,15))
            self.start=ctk.CTkButton(actions,text='↓   開始下載',height=44,width=190,fg_color=GREEN,text_color='white',hover_color='#066976',font=('Microsoft YaHei UI',15,'bold'),command=self.run); self.start.pack(side='left')
            self.inspect=ctk.CTkButton(actions,text='解析資訊',height=44,width=105,fg_color='#3568AC',command=lambda:self.run(True)); self.inspect.pack(side='left',padx=10)
            self.stop=ctk.CTkButton(actions,text='停止',height=44,width=75,fg_color='#4A2B3D',state='disabled',command=self.cancel); self.stop.pack(side='left')
            ctk.CTkButton(actions,text='開啟資料夾 ↗',height=44,width=120,fg_color='#3568AC',command=self.open_folder).pack(side='right')
            self.status=ctk.CTkLabel(main,text='準備就緒',anchor='w',font=('Microsoft YaHei UI',13),text_color=GREEN); self.status.grid(row=5,column=0,sticky='ew')
            self.progress=ctk.CTkProgressBar(main,progress_color=GREEN,fg_color='#DCE6F3',height=7); self.progress.grid(row=6,column=0,sticky='ew',pady=(8,12)); self.progress.set(0)
            self.log=ctk.CTkTextbox(main,fg_color='#FFFFFF',font=('Microsoft YaHei UI',12),height=115); self.log.grid(row=7,column=0,sticky='nsew'); self.log.configure(state='disabled')
            ctk.CTkLabel(main,text='請僅下載你有權儲存的內容。網站支援依 yt-dlp 而定；不支援 DRM 保護影片。',text_color=MUTED,font=('Microsoft YaHei UI',10)).grid(row=8,column=0,sticky='w',pady=(10,0))
            self.after(100,self.poll)
        def addlog(self,text):
            self.log.configure(state='normal'); self.log.insert('end',time.strftime('%H:%M:%S')+'  '+text+'\n'); self.log.see('end'); self.log.configure(state='disabled')
        def paste(self):
            try:
                text=self.clipboard_get().strip()
                self.links.delete('1.0','end')
                self.links.insert('end',text)
                self.auto_paste()
            except Exception: pass
        def auto_paste(self):
            if self.auto.get() and not self.busy:
                try: valid_urls(self.links.get('1.0','end'))
                except ValueError: return
                self.run()
        def choose(self):
            p=filedialog.askdirectory()
            if p: self.folder.delete(0,'end'); self.folder.insert(0,p)
        def open_folder(self):
            try:
                p=Path(self.folder.get()).expanduser(); p.mkdir(parents=True,exist_ok=True); os.startfile(p)
            except Exception as e: messagebox.showerror('無法開啟',str(e))
        def run(self,inspect=False):
            if self.busy:return
            try:
                urls=valid_urls(self.links.get('1.0','end')); folder=Path(self.folder.get()).expanduser().resolve(); folder.mkdir(parents=True,exist_ok=True)
            except Exception as e: messagebox.showerror('請檢查輸入',str(e)); return
            job=dict(urls=urls,folder=str(folder),quality=self.quality.get(),subtitles=bool(self.sub.get()),inspect=inspect)
            self.busy=True; self.cancelled=False; self.ok=self.failed=0; self.total=len(urls); self.progress.set(0)
            self.quality.configure(state='disabled')
            self.start.configure(state='disabled'); self.inspect.configure(state='disabled'); self.stop.configure(state='normal')
            self.status.configure(text='正在解析影片…'); self.addlog(f'開始處理 {len(urls)} 個連結')
            threading.Thread(target=self.launch,args=(job,),daemon=True).start()
        def launch(self,job):
            try:
                cmd=[sys.executable,'--worker'] if getattr(sys,'frozen',False) else [sys.executable,str(ROOT / 'main.py'),'--worker']
                with tempfile.TemporaryDirectory(prefix='neon-') as temp:
                    config=Path(temp)/'job.json'; events=Path(temp)/'events.jsonl'
                    config.write_text(json.dumps(job),encoding='utf-8'); events.touch()
                    self.process=subprocess.Popen(cmd+[str(config),str(events)],creationflags=subprocess.CREATE_NO_WINDOW)
                    if self.cancelled:self.kill()
                    with events.open(encoding='utf-8') as stream:
                        while True:
                            line=stream.readline()
                            if line:
                                try:self.events.put(json.loads(line))
                                except ValueError:self.events.put(dict(kind='log',text=line.strip()))
                            elif self.process.poll() is not None:break
                            else:time.sleep(.08)
                    code=self.process.wait()
                self.events.put(dict(kind='exit',code=code))
            except Exception as e:self.events.put(dict(kind='error',text=str(e))); self.events.put(dict(kind='exit',code=1))
        def kill(self):
            p=self.process
            if p and p.poll() is None:
                subprocess.run(['taskkill','/PID',str(p.pid),'/T','/F'],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW)
        def cancel(self):
            self.cancelled=True; self.stop.configure(state='disabled'); self.status.configure(text='正在停止…'); threading.Thread(target=self.kill,daemon=True).start()
        def poll(self):
            for _ in range(200):
                try:d=self.events.get_nowait()
                except queue.Empty:break
                k=d['kind']
                if k=='item':self.addlog(f"[{d['index']+1}/{self.total}] {d.get('platform', '網站')} · 解析連結…")
                elif k=='progress':
                    self.progress.set(d['fraction']); eta=d.get('eta'); self.status.configure(text=('下載完成，正在合併 / 轉換…' if d['status']=='finished' else f"下載中  {d['fraction']:.0%}  ·  {d['speed']/1048576:.1f} MB/s  ·  剩餘 {eta if eta is not None else '—'} 秒"))
                elif k=='success':
                    self.ok+=1; self.addlog(('解析成功：' if d.get('inspect') else '下載完成：')+d['title'])
                    if d.get('inspect'):
                        labels=[f'{h}p' for h in d.get('heights', [])]
                        self.addlog('來源提供的影片高度：'+(' / '.join(labels) if labels else '網站未提供，仍可選最佳畫質'))
                elif k in ('log','error'):
                    self.addlog(d['text'])
                    if k=='error':self.failed+=1
                elif k=='exit':
                    self.busy=False; self.process=None; self.start.configure(state='normal'); self.inspect.configure(state='normal'); self.stop.configure(state='disabled')
                    self.quality.configure(state='normal')
                    msg='已停止；保留部分檔案供下次續傳。' if self.cancelled else f'處理結束  ·  成功 {self.ok}  /  失敗 {self.failed}'
                    if d['code'] and not self.cancelled: msg+='  ·  引擎異常退出'
                    self.status.configure(text=msg); self.addlog(msg)
                    if self.ok==self.total:self.progress.set(1)
            self.after(100,self.poll)
        def close(self):
            if self.busy:
                if not messagebox.askyesno('結束下載','正在處理下載，確定停止並關閉？'):return
                self.cancelled=True; self.kill()
            self.destroy()
    return App()
