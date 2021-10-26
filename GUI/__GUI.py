from sys import platform
from selenium import webdriver
from tkinter import StringVar, messagebox
import tkinter.font as tkFont
import tkinter as tk
import locale

import Engine

from .config import *
from .Header.Header import *
from .Switch.Switch import *
from .Chart.Chart import *
from .Account.Account import *
from .OrderBook.OrderBook import *
from .Trades.Trades import *
from .OrderForm.OrderForm import *
from .Assets.Assets import *

if platform == "win32":
    # Windows formatting
    locale.setlocale(locale.LC_ALL, 'English_United States.1252')
else: 
    # Linux/OS X formatting
    locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')


# Create main app tkinter frame.
class GUI(tk.Frame):

    def __init__(self, root):
        super().__init__(root)
        
        self.engine = None

        self.root = root

        self.header, self.switch, self.chart, self.account, self.orderbook, self.trades, self. orderform, self.assets = self.Create_TLOs()
        self.tlbs = (self.header, self.switch, self.chart, self.account, self.orderbook, self.trades, self.orderform, self.assets)
        self.Place_TLOs(self.tlbs)
        #self.Pack_TLOs(self.tlbs)


    def Create_TLOs(self):
        header = Header(self.root)
        switch = Switch(self.root)
        chart = Chart(self.root)
        account = Account(self.root)
        orderbook = OrderBook(self.root)
        trades = Trades(self.root)
        orderform = OrderForm(self.root)
        assets = Assets(self.root)

        return header, switch, chart, account, orderbook, trades, orderform, assets

    def Place_TLOs(self, tlos, mode = 'full'):
        header, switch, chart, account, orderbook, trades, orderform, assets = tlos #, account, orderbook, trades, orderform = tlbs

        if mode == 'full':
            header.Grid(row=1, column=1, columnspan=3, padx=1, pady=1, sticky='NEW')
            switch.Grid(row=2, column=1, columnspan=2, padx=1, pady=1, sticky='NEW')
            chart.Grid(row=3, column=1, rowspan=2, padx=1, pady=1, sticky='NEWS')
            account.Grid(row=5, column=1, padx=1, pady=1, sticky='SEW')
            orderbook.Grid(row=3, column=2, rowspan=2, padx=1, pady=1, sticky='NEW')
            trades.Grid(row=5, column=2, padx=1, pady=1, sticky='NEW')
            orderform.Grid(row=2, column=3, rowspan=2, sticky='NEW')
            assets.Grid(row=4, column=3, columnspan=2, sticky='NEW')

            top = self.root.winfo_toplevel()
            top.rowconfigure(0, weight=1)
            top.columnconfigure(0, weight=1)
            self.root.rowconfigure(4, weight=1)
            self.root.columnconfigure(1, weight=1)

        elif mode == 'chart_only':
            header.Grid(row=1, column=1, columnspan=3, padx=1, pady=1, sticky='NEW')
            switch.Grid(row=2, column=1, columnspan=2, padx=1, pady=1, sticky='NEW')
            chart.Grid(row=3, column=1, rowspan=2, padx=1, pady=1, sticky='NEW')
            account.Grid(row=5, column=1, padx=1, pady=1, sticky='NEW')
            orderbook.Grid(row=3, column=2, rowspan=2, padx=1, pady=1, sticky='NEW')
            trades.Grid(row=5, column=2, padx=1, pady=1, sticky='NEW')
            orderform.Grid(row=2, column=3, rowspan=2, sticky='NEW')
            assets.Grid(row=4, column=3, sticky='NEW')


    def PackTLOs(self, tlos):
        header, switch, chart = tlos #, switch, chart, account, orderbook, trades, orderform = tlbs

        header.Pack()
        switch.Pack()
        chart.Pack()
