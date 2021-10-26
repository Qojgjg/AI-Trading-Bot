from tkinter import StringVar, messagebox
import tkinter.font as tkFont
import tkinter as tk

from ..config import *
from ..TopLevelObject import *

class Switch(TopLevelObject):
    def __init__(self, master):
        super().__init__(master)

    def Grid(self, **options):
        super().Grid(options)

        # Selection button
        self.selectButton = tk.Button(self.frame, text='{}{} {}x'.format('THETA', 'USDT', 5)).grid(row=1, column=1, sticky='W')

        # Price frame
        priceFrame = tk.Frame(self.frame)
        value = 9.123; dir = Direction.Up
        fg = Color.Bid.value if dir == Direction.Up else Color.Ask.value if dir == Direction.Down else Color.HighFG.value
        self.priceInQuote = tk.Label(priceFrame, text='{}'.format(value), fg = fg).grid(row=1, column=1, sticky='NEW')
        value = 9.10
        fg = Color.Bid.value if value >= 0 else Color.Ask.value
        self.priceInDollar = tk.Label(priceFrame, text='${:.2f}'.format(value), fg = fg).grid(row=2, column=1, sticky='SEW')
        priceFrame.grid(row=1, column=2, sticky='W')

        # Change frame
        changeFrame = tk.Frame(self.frame)
        tk.Label(changeFrame, text='24h Change', fg=Color.LowFG.value).grid(row=1, column=1, columnspan=2, sticky='NW')
        value = -0.086
        fg = Color.Bid.value if value >= 0 else Color.Ask.value
        self.changeInQuote = tk.Label(changeFrame, text='{}'.format(value), fg = fg).grid(row=2, column=1, sticky='NW')
        value = -0.81
        fg = Color.Bid.value if value >= 0 else Color.Ask.value
        self.changeInPercent = tk.Label(changeFrame, text='{}%'.format(value), fg = fg).grid(row=2, column=1, sticky='SW')
        changeFrame.grid(row=1, column=3, sticky='W')



    def Pack(self, **options):
        super().Pack(options)

        #tk.Button(self.master, text='Header button1').pack(side='top')
        
        self.button1 = tk.Button(self.frame, text='Switch button top')
        self.button1.pack(side='top')

        self.button2 = tk.Button(self.frame, text='Switch button bottom')
        self.button2.pack(side='bottom')