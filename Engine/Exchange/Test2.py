from datetime import datetime
from unicorn_binance_websocket_api.unicorn_binance_websocket_api_manager import BinanceWebSocketApiManager
import logging
import time
import threading
import os
import json
import datetime as dt

# https://docs.python.org/3/library/logging.html#logging-levels
logging.basicConfig(level=logging.DEBUG,
                    filename=os.path.basename(__file__) + '.log',
                    format="{asctime} [{levelname:8}] {process} {thread} {module}: {message}",
                    style="{")


def print_stream_data_from_stream_buffer(sockets):
    while True:
        if sockets.is_manager_stopping():
            exit(0)
        data = sockets.pop_stream_data_from_stream_buffer()
        if data is False:
            time.sleep(0.01)
        else: 
            d = json.loads(data)
            d = d.get('data', None)
            if d is not None and d['e'] == 'kline':
                #print(d['k']['x'], d['E'], d['k']['t'], d['k']['T'])
                eventtime = d['E']
                kstream = d['k']
                starttime_stream = kstream['t']
                print( d['s'].ljust(10),  d['k']['i'].zfill(3), dt.datetime.utcnow().strftime('%H:%M:%S'), str(int((dt.datetime.utcnow() - dt.datetime.utcfromtimestamp(eventtime/1000)).total_seconds())).zfill(3), dt.datetime.utcfromtimestamp(starttime_stream/1000).strftime('%M:%S'), dt.datetime.utcfromtimestamp(eventtime/1000).strftime('%M:%S') )


# create instance of BinanceWebSocketApiManager for Binance.com Futures
binance_websocket_api_manager = BinanceWebSocketApiManager(exchange="binance.com")

# set api key and secret for userData stream
_API_KEY = os.getenv('Binance_API_Key')
_API_SECRET = os.getenv('Binance_API_Secret')

#userdata_stream_id = binance_websocket_api_manager.create_stream(["arr"], ["!userData"], api_key=binance_je_api_key, api_secret=binance_je_api_secret)
#bookticker_all_stream_id = binance_websocket_api_manager.create_stream(["arr"], ["!bookTicker"])


# https://binance-docs.github.io/apidocs/futures/en/#mark-price-stream-for-all-market
#binance_websocket_api_manager.create_stream(["!markPrice"], "arr@1s", stream_label="!markPrice@arr@1s")

markets = {'ethusdt', 'bchusdt', 'btcusdt', 'btceth', 'xrpusdt', 'dotusdt', 'aliceused', '1inchusdt', 'maticusdt', \
    'linkusdt', 'aaveusdt', 'adausdt', 'autousdt', 'algousdt', 'antusdt', 'arusdt', 'alphausdt', 'ardrusdt', 'neousdt', 'bakeusdt',\
        'cakeusdt', 'bnbusdt', 'bntusdt', 'neousdt', 'compusdt', 'nulsusdt', 'cosusdt', 'diausdt', 'akrousdt', 'balusdt' }
#binance_websocket_api_manager.create_stream(["trade"], markets) #, api_key=_API_KEY, api_secret=_API_SECRET)
#binance_websocket_api_manager.create_stream(["aggTrade"], markets) #, api_key=_API_KEY, api_secret=_API_SECRET)
#binance_websocket_api_manager.create_stream(["markPrice"], markets) #, api_key=_API_KEY, api_secret=_API_SECRET)
binance_websocket_api_manager.create_stream(["kline_1m"], markets) #, api_key=_API_KEY, api_secret=_API_SECRET)
binance_websocket_api_manager.create_stream(["kline_5m"], markets) #, api_key=_API_KEY, api_secret=_API_SECRET)
binance_websocket_api_manager.create_stream(["kline_15m"], markets)
binance_websocket_api_manager.create_stream(["kline_1h"], markets)
binance_websocket_api_manager.create_stream(["kline_12h"], markets)
binance_websocket_api_manager.create_stream(["kline_1w"], markets)
"""
binance_websocket_api_manager.create_stream(["ticker"], markets)
binance_websocket_api_manager.create_stream(["miniTicker"], markets)
binance_websocket_api_manager.create_stream(["bookTicker"], markets)
binance_websocket_api_manager.create_stream(["depth"], markets, stream_label='abc')
binance_websocket_api_manager.create_stream(["depth@2500ms"], markets)
binance_websocket_api_manager.create_stream(["depth5"], markets)
binance_websocket_api_manager.create_stream(["depth5@100ms"], markets)
binance_websocket_api_manager.create_stream(["depth10"], markets)
binance_websocket_api_manager.create_stream(["depth20"], markets)
binance_websocket_api_manager.create_stream(["compositeIndex"], markets, stream_label="compositeIndex")
"""

channels = {'aggTrade', 'markPrice' 'kline_1m', 'kline_5m', 'kline_15m', 'kline_30m', 'kline_1h', 'kline_12h',
            'miniTicker', 'depth20@100ms', 'bookTicker', 'forceOrder', '!forceOrder', 'kline_1w@250ms',
            'compositeIndex'}
#binance_websocket_api_manager.create_stream(channels, markets)

# start a worker process to move the received stream_data from the stream_buffer to a print function
worker_thread = threading.Thread(target=print_stream_data_from_stream_buffer, args=(binance_websocket_api_manager,))
worker_thread.start()

# show an overview
#while True:
    #binance_websocket_api_manager.print_summary()
#    time.sleep(1)