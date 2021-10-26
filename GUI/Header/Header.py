from tkinter import StringVar, messagebox
from tkinter.constants import SUNKEN
import tkinter.font as tkFont
import tkinter as tk

from ..config import *
from ..TopLevelObject import *

#import Engine
import Engine.config
import Engine.___Engine
from Engine.___Engine import Engine
from Engine.config import *

class Header(TopLevelObject):
    def __init__(self, master):
        super().__init__(master)

        self.engine = None
        self.engine_stopped = True
        self.engine_text = tk.StringVar()
        self.engine_text.set('Start engine')

    def Grid(self, **options):
        super().Grid(options)

        leftFrame = tk.Frame()
        self.bnEngine = tk.Button(leftFrame, textvariable = self.engine_text, command=self.Toggle_Start_Engine, bg = 'orange', fg = 'navy blue').grid(row=1, column=1, sticky='W')
        self.buyCrypto = tk.Button(leftFrame, text='Buy Crypto', bg=Color.BG2.value, fg=Color.HighFG.value).grid(row=1, column=2, sticky='W')
        self.markets = tk.Button(leftFrame, text='Markets').grid(row=1, column=3, sticky='W')
        self.trade = tk.Button(leftFrame, text='Trade').grid(row=1, column=4, sticky='W')
        self.derivatives = tk.Button(leftFrame, text='Derivatives').grid(row=1, column=5, sticky='W')
        self.finance = tk.Button(leftFrame, text='Finance').grid(row=1, column=6, sticky='W')
        leftFrame.grid(row=1, column=1, sticky='W')
        
        rightFrame = tk.Frame()
        self.wallet = tk.Button(rightFrame, text='Wallet').grid(row=1, column=1, sticky='E')
        self.orders = tk.Button(rightFrame, text='Orders').grid(row=1, column=2, sticky='E')
        self.account = tk.Button(rightFrame, text='Account').grid(row=1, column=3, sticky='E')
        self.language = tk.Button(rightFrame, text='English').grid(row=1, column=4, sticky='E')
        self.currency = tk.Button(rightFrame, text='USD').grid(row=1, column=5, sticky='E')
        self.theme = tk.Button(rightFrame, text='***').grid(row=1, column=6, sticky='E')
        rightFrame.grid(row=1, column=2, sticky='E')


    def Pack(self, **options):
        super().Pack(options)

        #tk.Button(self.master, text='Header button1').pack(side='top')
        
        self.button1 = tk.Button(self.frame, text='Header button top')
        self.button1.pack(side='top')

        self.button2 = tk.Button(self.frame, text='Header button bottom')
        self.button2.pack(side='bottom')
    
    def Toggle_Start_Engine(self):
        if self.engine_stopped:
            if self.engine is None:
                self.engine = Engine() # A TopLevelObject property.
            TopLevelObject.engine = self.engine # so engine is now shared between all TopLevelObjects.
            self.engine.Start(Config['structure'], Config['timing'])
            self.engine_stopped = False
            self.engine_text.set('Stop engine')
        else:
            stopped = self.engine.Stop()
            if stopped:
                self.engine_stopped = True
                self.engine_text.set('Start engine')
        return
