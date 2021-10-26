from tkinter import StringVar, messagebox
import tkinter.font as tkFont
import tkinter as tk

from ..config import *
from ..TopLevelObject import *

from .LimitOrder import *

class OrderForm(TopLevelObject):
    def __init__(self, master, **kwargs):
        super().__init__(master)

        self.tradingSide = TradingSide.Buy
        self.orderType = OrderType.Limit

        self.Buy, self.Sell = None, None
        self.limitOrder, self.marketOrder, self.stopLimitOrder = None, None, None


    def Grid(self, **options):
        super().Grid(options)

        pady = 10

        # Caption = 'Place Order'
        tk.Label(self.frame, text='Place Order').grid(row=1, column=1, sticky='EW', pady=pady)

        # BUY SELL
        self.tradingSideFrame = tk.Frame(self.frame)
        if self.Buy is None: self.Buy = tk.Button(self.tradingSideFrame, text='BUY')
        if self.Sell is None: self.Sell = tk.Button(self.tradingSideFrame, text='SELL')
        if self.tradingSide == TradingSide.Buy:
            self.Buy.configure(bg = Color.Bid.value, fg = Color.HighFG.value)
            self.Sell.configure(bg = Color.BG3.value, fg = Color.LowFG.value)
        else:
            self.Buy.configure(bg = Color.BG3.value, fg = Color.LowFG.value)
            self.Sell.configure(bg = Color.Ask, fg = Color.HighFG.value)
        self.Buy.grid(row=1, column=1, sticky='EW')
        self.Sell.grid(row=1, column=2, sticky='EW')
        self.tradingSideFrame.grid(row=2, column=1, sticky='EW', pady=pady)

        # Limit Market Stop-Limit
        orderTypeFrame = tk.Frame(self.frame)
        self.limit = tk.Button(orderTypeFrame, text='Limit').grid(row=1, column=1, sticky='EW')
        self.narket = tk.Button(orderTypeFrame, text='Market').grid(row=1, column=2, sticky='EW')
        self.stopLimit = tk.Button(orderTypeFrame, text='Stop-Limit').grid(row=1, column=3, sticky='EW')
        orderTypeFrame.grid(row=3, column=1, sticky='EW', pady=pady)

        # Limiting-Amount Available. Base amount available when buying, quote amount available when selling.
        self.amountAvailable = tk.Label(self.frame, text = '{:f} {}'.format(45.12345678, 'USDT'))
        self.amountAvailable.grid(row=4, column=1, pady=pady)

        # Price
        priceFrame = tk.Frame(self.frame)
        tk.Label(priceFrame, text='Price').grid(row=1, column=1)
        self.price = tk.Entry(priceFrame, text = '{}'.format('USDT')).grid(row=1, column=2)
        tk.Label(priceFrame, text='{}'.format('USDT')).grid(row=1, column=3)
        priceFrame.grid(row=5, column=1, pady = pady)

        # Base Amount Chosen
        amountChosenFrame = tk.Frame(self.frame)
        tk.Label(amountChosenFrame, text='Amount').grid(row=1, column=1)
        self.amountChosen = tk.Entry(amountChosenFrame, text='THETA').grid(row=1, column=2)
        tk.Label(amountChosenFrame, text='{}'.format('THETA')).grid(row=1, column=3)
        amountChosenFrame.grid(row=6, column=1, pady=pady)

        self.slider = tk.Label(self.frame, text='----A slider here------')
        self.slider.grid(row=7, column=1, pady=pady)

        self.quoteTotalFrame = tk.Frame(self.frame)
        tk.Label(self.quoteTotalFrame, text='Total').grid(row=1, column=1)
        self.quoteTotal = tk.Entry(self.quoteTotalFrame, text='USDT').grid(row=1, column=2)
        tk.Label(self.quoteTotalFrame, text='{}'.format('USDT')).grid(row=1, column=3)
        self.quoteTotalFrame.grid(row=8, column=1, pady=pady)

        self.orderButton = tk.Button( self.frame, text = 'Buy {}'.format('THETA'), bg = Color.Bid.value, fg = Color.HighFG.value)
        self.orderButton.grid(row=9, column=1, sticky='EW', pady=pady)




     

    def Pack(self, **options):
        super().Pack(options)

        #tk.Button(self.master, text='Header button1').pack(side='top')
        
        self.button1 = tk.Button(self.frame, text='OrderForm button top')
        self.button1.pack(side='top')

        self.button2 = tk.Button(self.frame, text='OrderForm button bottom')
        self.button2.pack(side='bottom')
