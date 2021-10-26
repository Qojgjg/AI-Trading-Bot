import sys
import time as tm
from .config import *
from binance.client import Client as BinanceClient


def Call_Binance_API_v2(clientPool, method_name, nTrials, wait_sec, *args, **kwargs):
    result = None

    successful = False

    while not successful and nTrials > 0:
        try:
            now_utc = dt.datetime.utcnow().replace(tzinfo = pytz.utc)
            ts_mili= round(dt.datetime.timestamp(now_utc)*1000)
            client = clientPool.Next()
            method = getattr(BinanceClient, method_name)
            tm.sleep(wait_sec)
            result = method(client, *args, **kwargs) # I doubt Binance sometimes holds this call and wouldn't return, as a penalty.
            successful = True
        except:
            print("Oops!", sys.exc_info()[0], "occurred.")
            clientPool.Repair(client)
            nTrials -= 1
            if nTrials > 0: continue

    return result, ts_mili


def exact_fetch(clientPool, binance_wait_sec, dataType, symbol, interval, startId, endId, nToFetch):

  nFetched = 0
  datalines = []
  lastId = startId - 1
  endId -=1 # endId is Exclusive for callers, inclusive for Binance exchange.

  while 0 < nToFetch:
    maxLimit = min(500, nToFetch)

    if dataType == 'klines':
        lines, ts_mili = Call_Binance_API_v2(clientPool, "get_klines", 3, binance_wait_sec, symbol = symbol, interval = interval, limit = maxLimit, startTime = lastId + 1, endTime = endId)
        #lines = clientPool.Next().get_klines(symbol = symbol, interval = interval, limit = maxLimit, startTime = lastId + 1, endTime = endId)
    elif dataType == 'trafes':
      lines = None

    elif dataType == 'aggTrades':
        lines = clientPool.Next().get_aggregate_trades(symbol = symbol, fromId = lastId + 1, startTime = lastId + 1, endTime = endId, limit = maxLimit)

    if lines is not None:
        nFetched = len(lines)
        if nFetched > 0:
            lastId = lines[-1][0]
            datalines += lines
            nToFetch -= nFetched
    else:
        datalines = None
        break

  # Note: Most of the time, the last line is under construction if dataType == 'klines' or 'aggTrades'?
  # Do NOT remove them, though, because it sometimes has just been completed.

  return datalines


