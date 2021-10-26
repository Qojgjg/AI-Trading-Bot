

from asyncio.tasks import sleep
import time
from typing import Tuple
import win32api
import asyncio
import threading

from .config import *

from .TimeMachine import *
from .Exchange.Exchange import *
from .Exchange.Binance import *
from .ManualTrader.ManualTrader import *
from .AutoTrader.AutoTrader import *
from .AITrainer.AITrainer import *
from .TraderTrainer.TraderTrainer import *
from .ThreadOnTimeMachine import *

from .Trader.TraderFactory import *
from .Exchange.ExchangeFactory import *

from .Exchange.Utility import *

class Engine(threading.Thread):

    def __init__(self):
        print('Engine being created...')

        self.running = False

    def run(self):
        asyncio.run(Binance._singleton.Maintain_GStreams())

    def Start(self, structuralParams, timingParams):
        if not self.running:
            threading.Thread.__init__(self)
            print('Starting engine...')

            Binance.Initialize()
            self.name = structuralParams['Name']
            self.traders = [ TraderFactory.CreateTrader(traderParams, timingParams) for _, traderParams in structuralParams['Traders'].items() ]

            self.start() # run on thread.
            print('Streaming started.')
          
            ts_mili = round( dt.datetime.timestamp(dt.datetime.now()) * 1000 )
            interval_mili = round( BasicIntervalMin * 60 * 1000 )
            sleep_sec = (interval_mili - round(ts_mili) % round(interval_mili)) / 1000 + 5 # Binance streaming event time lags less than 5 seconds behind real time.
            self.Start_Traders(sleep_sec)
            print('Engine started.')
            self.running = True
        return True

    def Start_Traders(self, sleep_sec):
        print('Sleeping {:.1f} seconds before launching the time machine.'.format(sleep_sec))
        tm.sleep(sleep_sec)
        
        for trader in self.traders: trader.Start() # This will create Binance._singleton, among others.
        
        return

    def Stop(self):
        if self.running:
            stopped = None

            for trader in self.traders: trader.Stop()
            print('Signaled traders to stop.')
            for trader in self.traders: trader.Join()
            print('Traders stopped.')

            signaled = asyncio.run(Binance._singleton.Stop_Maintain_GStreams())
            print('Signaled the streams to stop.')

            if signaled:
                self.join()
                stopped = True
                self.running = False
                print('Streaming stopped.')
            else:
                stopped = False

            print('Engine stopped.')

        else:
            stopped = True

        return stopped


    def TestCall(self, message):
        print('Engine is called on TestCall: {}'.format(message))


    def Get_N_Products(self, dataType = 'klines', symbols_to_include = [], interval = '1m'):
        n_products = 0

        with Binance.lock_gstream:
            for key, (_, _, _, _, _, t_state) in Binance.gstreams.items():
                [_dataType, _symbol, _interval] = key.split('.')
                if dataType == _dataType and (symbols_to_include is None or _symbol in symbols_to_include) and interval == _interval and t_state & T_State.no_missing:
                    n_products += 1
        return n_products


    def Get_Recent_Prices(self, dataType, symbols_to_include, interval, nRows = None, nProducts = None, symbols_to_exclude = None):
        products_prices = {}

        gstreams = {}
        with Binance.lock_gstream:
            for key, (_, _, _, _, _, t_state) in Binance.gstreams.items():
                gstreams[key] = t_state

        for key, t_state in gstreams.items():
            [_dataType, _symbol, _interval] = key.split('.')
            if symbols_to_exclude is None or _symbol not in symbols_to_exclude:
                if dataType == _dataType and (symbols_to_include is None or _symbol in symbols_to_include) and interval == _interval and t_state & T_State.no_missing:
                    dataframe = Binance._singleton.Get_Recent_Prices(_dataType, _symbol, _interval, nRows)
                    products_prices[_symbol] = dataframe
                    if nProducts is not None and len(products_prices) >= nProducts:
                        break
        
        return products_prices

    def Start_Add_To_Plot(self, Add_To_Plot):
        Binance.Start_Add_To_Plot(Add_To_Plot)
    
#bn = Binance.instantiate()
#bn.Download_Daily_Data(['klines'], ['ETHUSDT'], ['1m'], dt.datetime(2021, 5, 23), dt.datetime(2021, 6, 5) )

#bn.Get_Data(['ETHUSDT'], ['1m'], datetime(2021, 5, 26), datetime(2021, 6, 2), Config['Data'])
#bn.Load_Stream(['ETHUSDT'], ['1m'], Config['Data'])
#n = bn.GetExchangeTimeMili()

# engine.Start()


