"""Brand-icon meeting picker shared by both language editions."""
import queue
import threading
import customtkinter as ctk
from PIL import Image
from tkinter import filedialog, messagebox
from .runtime import ROOT
from .meetings import PROVIDERS, BY_KEY, find_local, open_provider, load_overrides, save_override

FONT='Microsoft YaHei UI'


class MeetingPage(ctk.CTkScrollableFrame):
    def __init__(self, parent):
        super().__init__(parent,fg_color='#F3F6FB')
        self.results=queue.Queue(); self.scanning=False; self.images=[]; self.statuses={}
        self.grid_columnconfigure(0,weight=1)
        top=ctk.CTkFrame(self,fg_color='transparent');top.grid(row=0,column=0,sticky='ew',padx=25,pady=(23,4))
        ctk.CTkLabel(top,text='會議預約',font=(FONT,28,'bold'),text_color='#182D48').pack(side='left')
        self.refresh_button=ctk.CTkButton(top,text='重新偵測',width=95,height=34,command=self.refresh)
        self.refresh_button.pack(side='right')
        ctk.CTkLabel(self,text='選擇會議平台，登入後設定會議時間。',font=(FONT,13),text_color='#586C84').grid(row=1,column=0,sticky='w',padx=25,pady=(0,17))
        grid=ctk.CTkFrame(self,fg_color='transparent');grid.grid(row=2,column=0,sticky='ew',padx=17)
        for col in range(3):grid.grid_columnconfigure(col,weight=1,uniform='providers')
        for index, provider in enumerate(PROVIDERS):
            card=ctk.CTkFrame(grid,fg_color='white',corner_radius=14,border_width=1,border_color='#DFE7F1')
            card.grid(row=index//3,column=index%3,sticky='nsew',padx=8,pady=8);card.grid_columnconfigure(0,weight=1)
            with Image.open(ROOT/'assets'/'meetings'/provider.icon) as source:
                icon=ctk.CTkImage(light_image=source.copy(),dark_image=source.copy(),size=(44,44))
            self.images.append(icon)
            ctk.CTkButton(card,text=("Teams" if provider.key=="teams" else provider.name),image=icon,compound='left',anchor='w',
                          font=(FONT,17,'bold'),height=76,fg_color='white',hover_color='#EFF5FC',text_color='#182D48',
                          command=lambda k=provider.key:self.launch(k)).grid(row=0,column=0,sticky='ew',padx=12,pady=(8,0))
            hint=ctk.CTkLabel(card,text=provider.hint,font=(FONT,12),text_color='#586C84',justify='left',anchor='nw',wraplength=235,height=55)
            hint.grid(row=1,column=0,sticky='ew',padx=18,pady=(2,5))
            card.bind('<Configure>',lambda e,w=hint,c=card:w.configure(wraplength=max(160,c._reverse_widget_scaling(e.width)-36)),add='+')
            status=ctk.CTkLabel(card,text='正在偵測…',font=(FONT,11),text_color='#586C84',anchor='w')
            status.grid(row=2,column=0,sticky='ew',padx=18,pady=(0,6));self.statuses[provider.key]=status
            ctk.CTkButton(card,text='開啟並預約',height=37,fg_color=provider.color,hover_color='#244E79',font=(FONT,13),
                          command=lambda k=provider.key:self.launch(k)).grid(row=3,column=0,sticky='ew',padx=16)
            actions=ctk.CTkFrame(card,fg_color='transparent');actions.grid(row=4,column=0,sticky='ew',padx=12,pady=(6,10))
            actions.grid_columnconfigure((0,1),weight=1)
            for col,(text,cmd) in enumerate([('網頁登入',lambda k=provider.key:self.launch(k,True)),('設定路徑',lambda k=provider.key:self.configure_path(k))]):
                ctk.CTkButton(actions,text=text,command=cmd,height=30,width=80,fg_color='transparent',text_color='#3568AC',
                              hover_color='#EAF2FF',font=(FONT,12)).grid(row=0,column=col,sticky='ew',padx=2)
        helpcard=ctk.CTkFrame(grid,fg_color='#EAF2FF',corner_radius=14)
        helpcard.grid(row=1,column=2,sticky='nsew',padx=8,pady=8)
        ctk.CTkLabel(helpcard,text='優先使用本機程式',font=(FONT,17,'bold'),text_color='#182D48',anchor='w').pack(fill='x',padx=20,pady=(24,12))
        guide=ctk.CTkLabel(helpcard,text='已安裝 → 開啟本機程式\n未安裝 → 提示後開啟網頁\n\n安裝在其他磁碟？\n可用「設定路徑」指定。\n\nGoogle Meet 會偵測已安裝的網頁應用捷徑。',font=(FONT,13),text_color='#586C84',justify='left',wraplength=230,anchor='nw')
        guide.pack(fill='x',padx=20,pady=(0,20))
        helpcard.bind('<Configure>',lambda e:guide.configure(wraplength=max(160,helpcard._reverse_widget_scaling(e.width)-40)),add='+')
        self.feedback=ctk.CTkLabel(self,text='帳號登入與會議建立會在所選平台完成。',font=(FONT,12),text_color='#087F8C',anchor='w',wraplength=840,justify='left')
        self.feedback.grid(row=3,column=0,sticky='ew',padx=25,pady=(12,18))
        self.after(200,self.refresh);self.after(100,self.poll)

    def refresh(self):
        if self.scanning:return
        self.scanning=True;self.refresh_button.configure(state='disabled')
        def scan():
            try:
                overrides=load_overrides()
                self.results.put({p.key:find_local(p,overrides) for p in PROVIDERS})
            except Exception as exc:self.results.put(exc)
        threading.Thread(target=scan,daemon=True).start()

    def poll(self):
        try:results=self.results.get_nowait()
        except queue.Empty:results=None
        if results is not None:
            self.scanning=False;self.refresh_button.configure(state='normal')
            if isinstance(results,Exception):self.feedback.configure(text='偵測未完成，可直接點選平台或設定路徑。')
            else:
                for key,target in results.items():
                    text=('已設定本機路徑' if target.kind=='custom' else '已找到本機入口') if target else '將使用官方網頁'
                    self.statuses[key].configure(text=text,text_color='#087F8C' if target else '#586C84')
        self.after(150,self.poll)

    def launch(self,key,web_only=False):
        try:
            destination=open_provider(key,lambda title,text:messagebox.showinfo(title,text,parent=self.winfo_toplevel()),web_only)
            p=BY_KEY[key]
            self.feedback.configure(text=('已開啟本機入口：' if destination=='desktop' else '已開啟官方網頁：')+p.name+'。'+p.hint)
        except (OSError,ValueError) as exc:
            messagebox.showerror('無法開啟會議平台',str(exc),parent=self.winfo_toplevel())

    def configure_path(self,key):
        p=BY_KEY[key]
        dialog=ctk.CTkToplevel(self);dialog.title(p.name+' · 本機程式');dialog.geometry('540x270');dialog.resizable(False,False)
        ctk.CTkLabel(dialog,text=p.name+' 的本機入口',font=(FONT,20,'bold')).pack(anchor='w',padx=22,pady=(20,10))
        pathtext=ctk.CTkLabel(dialog,text=load_overrides().get(key,'自動偵測常見安裝位置與開始功能表捷徑'),font=(FONT,12),wraplength=490,justify='left')
        pathtext.pack(anchor='w',padx=22,pady=(0,16))
        def select():
            filename=filedialog.askopenfilename(parent=dialog,title='選擇 '+p.name+' 程式或捷徑',filetypes=[('Windows 程式或捷徑','*.exe *.lnk')])
            if filename:
                try:save_override(key,filename);pathtext.configure(text=filename);self.refresh()
                except (OSError,ValueError) as exc:messagebox.showerror('無法儲存路徑',str(exc),parent=dialog)
        def reset():
            try:save_override(key,None);pathtext.configure(text='已恢復自動偵測');self.refresh()
            except OSError as exc:messagebox.showerror('無法儲存路徑',str(exc),parent=dialog)
        buttons=ctk.CTkFrame(dialog,fg_color='transparent');buttons.pack(fill='x',padx=22)
        ctk.CTkButton(buttons,text='選擇 EXE / LNK',command=select).pack(side='left')
        ctk.CTkButton(buttons,text='恢復自動偵測',command=reset).pack(side='left',padx=10)
        ctk.CTkButton(dialog,text='完成',command=dialog.destroy,width=90).pack(anchor='e',padx=22,pady=20)
        dialog.after(150,lambda:(dialog.lift(),dialog.focus_force()))
