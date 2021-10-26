import math
from math import sqrt
import numpy as np
from Engine.config import Config
from tkinter import StringVar, messagebox
import tkinter.font as tkFont
import tkinter as tk

from matplotlib.backends.backend_tkagg import (
    FigureCanvasTkAgg, NavigationToolbar2Tk)
# Implement the default Matplotlib key bindings.
#from matplotlib.backend_bases import key_press_handler
import matplotlib.pyplot as plt
#from matplotlib.figure import Figure

import numpy as np

from ..config import *
from ..TopLevelObject import *


class Chart(TopLevelObject):
    def __init__(self, master):
        super().__init__(master, width=300, height=250)

        self.fig = None
        self.canvas = None
        self.symbol_ax_map = {}

    def Grid(self, **options):
        super().Grid(options)

        #tk.Button(self.master, text='Header button1').pack(side='top')
        
        self.interval = tk.Frame(self.frame)
        for idx, interval in enumerate(['Time', '15m', '1H', '4H', '1D', '1W', 'V...']):
            tk.Button(self.interval, text=interval).grid(row=1, column=idx+1, sticky='W')
        self.interval.grid(row=1, column=1, columnspan=2, sticky='NW')

        self.view = tk.Frame(self.frame)
        tk.Button(self.view, text='Original', command=self.Initially_Chart_All_Prices).grid(row=1, column=1, sticky='E')
        tk.Button(self.view, text='TradingView').grid(row=1, column=2, sticky='E')
        tk.Button(self.view, text='Depth').grid(row=1, column=3, sticky='E')
        self.view.grid(row=1, column=3, sticky='NE')

        self.tools = tk.Frame(self.frame)
        for tool in range(10):
            tk.Label(self.tools, text='T'+str(tool)).grid(row=tool+1, column=1, sticky='N')
        self.tools.grid(row=2, column=1, sticky='NW')

        self.Initialize_Canvas()

        return


    def Initialize_Canvas(self):
        if self.fig is not None: del self.fig
        if self.canvas is not None: del self.canvas

        self.dpi = 100
        self.fig = plt.figure(figsize=(13.5, 7.5), dpi=self.dpi)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.frame)  # A tk.DrawingArea for matplotlib.
        self.canvas.draw()
        canvas_widget = self.canvas.get_tk_widget()
        canvas_widget.grid(row=2, column=2, columnspan=2) #, sticky='NEWS')
        # self.fig.set_size_inches( canvas_widget.winfo_width()/self.dpi, canvas_widget.winfo_height()/self.dpi )


    def Pack(self, **options):
        super().Pack(options)

        #tk.Button(self.master, text='Header button1').pack(side='top')
        
        self.button1 = tk.Button(self.frame, text='Chart button top')
        self.button1.pack(side='top')

        self.button2 = tk.Button(self.frame, text='Chart button bottom')
        self.button2.pack(side='bottom')

    def Adjust_Figure_Size(self):
        debut = 3
        pass

    def Initially_Chart_All_Prices(self):
        interval = Config['ginterval']

        nCharts = TopLevelObject.engine.Get_N_Products(dataType = 'klines', symbols_to_include = None, interval = interval)
        if nCharts <= 0:
            print('No products to chart. Quiting.')
            return

        Nx, Ny = self.Get_Ax_Matrix_Size(nCharts)

        self.Initialize_Canvas()
        plt.subplots_adjust(left=0, bottom=0, right=1, top=1, wspace=0, hspace=0)
        plt.tick_params(axis='x', which='both', bottom=False, top=False, labelbottom=False)
        plt.tick_params(axis='y', which='both', left=False, right=False, labelleft=False)

        prices = {}
        min = float('inf'); max = -float('inf')

        nRows = int( 1440 / int(interval[:-1]) ) # 1440 min, or one day.
        symbols_done = []
        while True:
            products_prices = TopLevelObject.engine.Get_Recent_Prices(dataType = 'klines', symbols_to_include = None, interval = interval, nRows = nRows, nProducts = 1, symbols_to_exclude = symbols_done)
            if len(products_prices) <= 0: break
            symbols_done += list(products_prices.keys())
            symbol = list(products_prices.keys())[0]
            df_candles = list(products_prices.values())[0]
            ts = np.array(df_candles[0])
            log_price = np.log10( np.array(df_candles[2]) / 2 + np.array(df_candles[3]) / 2 ) # 1: Open, 2: High, 3: Low, 4: Close
            log_price = log_price - np.min(log_price)
            _min = np.min(log_price)
            if min > _min: min = _min
            _max = np.max(log_price); 
            if max < _max: max = _max
            prices[symbol] = (ts, log_price)


        Nx, Ny = self.Get_Ax_Matrix_Size(len(prices))
        ax_array = self.fig.subplots( Ny, Nx, sharex = True, sharey = True)

        self.symbol_ax_map[symbol] = {}
        idx = 0; idy = 0; index = 1
        for symbol, (ts, log_price) in prices.items():
            ax = ax_array[idy, idx]
            ax.set_ylim([min, max])
            idx = idx + 1 if idx < Nx-1 else 0
            idy = idy + 1 if idy < Ny-1 and idx == 0 else idy
            ax.text(0,0, symbol[:-4]) # 4 hard-coded for 'USDT'
            ax.text(0.5, 0.5, symbol[:-4], transform=ax.transAxes, fontsize=8)
            ax.plot(ts, log_price)
            self.symbol_ax_map[symbol] = ax
        #plt.show()

        self.engine.Start_Add_To_Plot(self.Add_To_Plot)

        return


    def Add_To_Plot(self, symbol, x, y):
        if self.symbol_ax_map.get(symbol, None) is not None:
            ax = self.symbol_ax_map[symbol]
            ax.plot(x, y)
        return


    def Get_Ax_Matrix_Size(self, nCharts):
        canvas_widget = self.canvas.get_tk_widget()
        X = canvas_widget.winfo_width()
        Y = canvas_widget.winfo_height()
        Nx = X / sqrt( 4 * X * Y / 3 / nCharts )
        Ny = nCharts / Nx

        Nx = round(Nx); Ny = round(Ny)

        if Nx * Ny > nCharts:
            if (Nx-1) * Ny < nCharts and Nx * (Ny-1) < nCharts:
                Nx = Nx; Ny = Ny
            elif (Nx-1) * Ny >= nCharts:
                Nx = Nx-1; Ny = Ny
            else:
                Nx = Nx; Ny = Ny - 1
        elif nCharts <= (Nx+1) * Ny and (Nx+1) * Ny <= Nx * (Ny+1):
            Nx = Nx+1; Ny = Ny
        elif nCharts <= Nx * (Ny+1) and (Nx+1) * Ny >= Nx * (Ny+1):
            Nx = Nx; Ny = Ny + 1
        else:
            Nx = Nx+1; Ny = Ny+1

        return Nx, Ny