from .Binance import *

from ..config import *

class ExchangeFactory():

    def CreateExchange(exchangeParams):
        exchange = None
        if exchangeParams['Type'] == 'Binance':
            exchange = Binance.instantiate(exchangeParams)
        else:
            raise Exception('Invalid exchange type')                  
        return exchange