from tkinter import StringVar, messagebox
import tkinter.font as tkFont
import tkinter as tk

from ..config import *
from ..TopLevelObject import *


class OrderBook(TopLevelObject):
    def __init__(self, master):
        super().__init__(master)

    def Grid(self, **options):
        super().Grid(options)

        tk.Label(self.frame, text='Order Book').grid(row=1, column=1, sticky='NEW')

        for label in range(17):
            tk.Label(self.frame, text='OrderBook label, OrderBook label ' + str(label).zfill(2)).grid(row=label+2, column=1)
        

    def Pack(self, **options):
        super().Pack(options)

        #tk.Button(self.master, text='Header button1').pack(side='top')
        
        self.button1 = tk.Button(self.frame, text='OrderBook button top')
        self.button1.pack(side='top')

        self.button2 = tk.Button(self.frame, text='OrderBook button bottom')
        self.button2.pack(side='bottom')
