from .Indicator import *
from .Utility import *
from ..Exchange.Utility import *

from ..config import *

class ProductsPrices_Stream(Indicator):
    def __init__(self, structuralParams, timingParams):
        super().__init__(structuralParams, timingParams)

    def __setInstance__(self, structuralParams, timingParams):
        super().__setInstance__(structuralParams, timingParams)

        self.quote = structuralParams['Quote']
        self.maxStreams = structuralParams['MaxStreams']
        self.interval = structuralParams['Interval']

        self.prices = {}
        self.products = []
        self.products_prices = {}

        self.products, self.products_prices = self.Add_Products(self.maxStreams)

        return

    def SingleStep(self, stepId):
        super().SingleStep(stepId)

        if Binance.gstreams_ready:
            self.products, self.products_prices = self.Add_Products()
        
        return


    def Add_Products(self, nMaxStreams = None):

        products = collect_products(Binance.clientPool, self.quote)
        products_prices = {}

        count = 0
        for product in products:
            count += 1
            if nMaxStreams is not None and count > nMaxStreams: break
            Binance._singleton.Add_GStream('klines', product['s'], self.interval, granular = True)  # False
            products_prices[product['s']] = []

        return products, products_prices
