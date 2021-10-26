from tkinter import StringVar, messagebox
import tkinter.font as tkFont
import tkinter as tk

from ..config import *
from ..TopLevelObject import *


class Account(TopLevelObject):
    def __init__(self, master):
        super().__init__(master)

    def Grid(self, **options):
        super().Grid(options)

        self.menuFrame = tk.Frame(self.frame)
        self.openOrders = tk.Button(self.menuFrame, text='Open Orders').grid(row=1, column=1, sticky='NWE')
        self.oderHistory = tk.Button(self.menuFrame, text='Order History').grid(row=1, column=2, sticky='NWE')
        self.tradeHistory = tk.Button(self.menuFrame, text='Trade History').grid(row=1, column=3, sticky='NWE')
        self.funds = tk.Button(self.menuFrame, text='Funds').grid(row=1, column=4, sticky='NWE')
        self.menuFrame.grid(row=1, column=1)

        for label in range(7):
            tk.Button(self.frame, text='Account button ' + str(label).zfill(2)).grid(row=label+2, column=1)
        

    def Pack(self, **options):
        super().Pack(options)

        #tk.Button(self.master, text='Header button1').pack(side='top')
        
        self.button1 = tk.Button(self.frame, text='Account button top')
        self.button1.pack(side='top')

        self.button2 = tk.Button(self.frame, text='Account button bottom')
        self.button2.pack(side='bottom')
