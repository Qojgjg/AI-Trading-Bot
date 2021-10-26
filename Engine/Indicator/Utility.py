import time as tm

#import binance
from ..config import *
from ..Utility import *

def collect_prices(clientPool, endswith, prices):
    """
    collect_selected_prices(client, '', prices) produced 1543 tickers, on July 15, 2021, while
    collect_selected_prices(client, '', prices) produced 305.

    """
    #height = None
    #if len(prices) == 0:
    #    height = 0
    #else:
    #    for symbol, price_list in prices.items():
    #        if height is None:
    #            height = len(price_list)
    #        elif height != len(price_list):
    #            raise Exception('Inconsistent number of prices.')
    
    tickers, ts_mili = Call_Binance_API_v2(clientPool, "get_all_tickers", 3, Config['binance_wait_sec']) # nTrials

    if tickers is not None:

        for ticker in tickers:
            if ticker['symbol'].endswith( endswith, len(ticker['symbol'])-len(endswith) ):
                price = float(ticker['price'])
                if prices.get(ticker['symbol'], None) is None:
                    prices[ticker['symbol']] = [(ts_mili, price)]
                else:
                    prices[ticker['symbol']].append((ts_mili, price))

        #height += 1
        #delete = [symbol for symbol, prices in prices.items() if len(prices) != height]
        #for symbol in delete: del prices[symbol]

    else:
        prices = prices #============= Design decision!

    return prices


def collect_products(clientPool, endswith):

    products = None
    products_collected = []

    trials = 3
    successful = False

    products, ts_mili = Call_Binance_API_v2(clientPool, "get_products", 3, Config['binance_wait_sec'])

    if products is not None:
        for product in products['data']:
            if product['s'].endswith( endswith, len(product['s'])-len(endswith) ) \
                and product['c'] is not None and product['cs'] is not None \
                and product['c'] * product['cs'] > 0 :
                products_collected.append( product )

        def take_market_cap(elem):
            return elem['c'] * elem['cs']

        products_collected = sorted( products_collected, key = take_market_cap,  reverse=True )
    
    return products_collected


def get_products_prices(products, prices):
    products_prices = {}

    for product in products:
        if prices.get(product['s'], None) is not None:
            products_prices[product['s']] = prices[product['s']]
    
    return products_prices
