import os, sys, re, shutil, time
import threading
import json
from pathlib import Path
import datetime as dt
import time as tm
import pytz
import urllib.request
import binance
from numpy.lib.npyio import save
import pandas as pd
from argparse import ArgumentParser, RawTextHelpFormatter, ArgumentTypeError
from pandas.core.frame import DataFrame
import patoolib
from .enums import *
from ..config import *
from ..Utility import *


def from_dt_local_to_dt_utc( dt_local ):
  now_timestamp = tm.time()
  offset = dt.datetime.fromtimestamp(now_timestamp) - dt.datetime.utcfromtimestamp(now_timestamp)
  dt_utc = dt_local - offset
  if dt_utc.tzinfo is None or dt_utc.tzinfo.utcoffset(dt_utc) is None:
      dt_utc = dt_utc.replace(tzinfo=pytz.utc)
  return dt_utc


def from_dt_utc_to_dt_local( dt_utc ):
  now_timestamp = tm.time()
  offset = dt.datetime.fromtimestamp(now_timestamp) - dt.datetime.utcfromtimestamp(now_timestamp)
  dt_local = dt_utc + offset
  if dt_local.tzinfo is None or dt_local.tzinfo.utcoffset(dt_utc) is None: # ?
      dt_local = dt_local.replace(tzinfo=None) # ?
  return dt_local


def get_current_day_start( dt_any ):
  return dt.datetime(dt_any.year, dt_any.month, dt_any.day).replace(tzinfo=dt_any.tzinfo)

def get_next_day_start( dt_any ):
  sample_dt = get_current_day_start(dt_any) + dt.timedelta(hours=25)
  return dt.datetime(sample_dt.year, sample_dt.month, sample_dt.day).replace(tzinfo=sample_dt.tzinfo)

def get_current_month_start( dt_any ):
  return dt.datetime(dt_any.year, dt_any.month, 1).replace(tzinfo=dt_any.tzinfo)

def get_nest_month_start( dt_any ):
  sample_dt = get_current_month_start(dt_any) + dt.timedelta(days=32)
  return dt.datetime(sample_dt.year, sample_dt.month, 1).replace(tzinfo=dt_any.tzinfo)


def Extend_Stream(dataType, symbols, intervals, folder, lastIds):
 
  symbolcounter = 0

  paths = {}
  for symbol in symbols:
    print("[{}/{}] - start extend daily {} {}.".format(symbolcounter+1, len(symbols), symbol, dataType))
    for interval in intervals:
      now_utc = dt.datetime.utcnow().replace(tzinfo = pytz.utc)
      base_path, file_name = get_base_path(now_utc, dataType, symbol, interval)
      path = extend_today_file(base_path, file_name, folder)
      paths[symbol+'.'+interval] = path
    symbolcounter += 1

  return paths


def extend_today_file(path, file_name, folder):
  pass

def get_base_path(datetime_utc, dataType, symbol, interval):
  if dataType == 'klines':
    base_path = "data/spot/daily/klines/{}/{}/".format(symbol.upper(), interval)
    file_name = "{}-{}-{}.zip".format(symbol.upper(), interval, datetime_utc.strftime("%Y-%m-%d"))
  elif dataType == 'trades':
    base_path = "data/spot/daily/trades/{}/".format(symbol.upper())
    file_name = "{}-trades-{}.zip".format(symbol.upper(),  datetime_utc.strftime("%Y-%m-%d"))
  elif dataType == 'aggTrades':
    base_path = "data/spot/daily/aggTrades/{}/".format(symbol.upper())
    file_name = "{}-aggTrades-{}.zip".format(symbol.upper(),  datetime_utc.strftime("%Y-%m-%d"))
  else: raise Exception('Invalid dataType.')

  return base_path, file_name

def get_download_url(file_url):
  return "{}{}".format(BASE_URL_DOWNLOAD, file_url)

def get_all_symbols():
  response = urllib.request.urlopen("https://api.binance.com/api/v3/exchangeInfo").read()
  return list(map(lambda symbol: symbol['symbol'], json.loads(response)['symbols']))


def get_file_location(datetime_utc, dataType, symbol, interval):
  base_folder, file_name = get_base_path(datetime_utc, dataType, symbol, interval)
  save_folder = os.path.join(os.environ.get('STORE_DIRECTORY'), base_folder)
  save_path = os.path.join(save_folder, file_name)

  return base_folder, file_name, save_folder, save_path


def download_file(current_utc, dataType, symbol, interval): #base_path, file_name, folder=None):
  base_folder, file_name, save_folder, save_path = get_file_location(current_utc, dataType, symbol, interval)
  download_path = os.path.join(base_folder, file_name)
  
  csv_path = str(Path(save_path).with_suffix('.csv'))
  if os.path.exists(csv_path):
    print("\nfile already exists! {}".format(csv_path))
  else:
    # make the directory
    if not os.path.exists(save_folder):
      Path(save_folder).mkdir(parents=True, exist_ok=True)

    try:
      if not os.path.exists(save_path):
        download_url = get_download_url(download_path)
        dl_file = urllib.request.urlopen(download_url)
        length = dl_file.getheader('content-length')
        if length:
          length= int(length)
          blocksize = max(4096,length//100)

        with open(save_path, 'wb') as out_file:
          dl_progress = 0
          print("\nFile Download: {}".format(save_path))
          while True:
            buf = dl_file.read(blocksize)   
            if not buf:
              break
            dl_progress += len(buf)
            out_file.write(buf)
            done= round(50 * dl_progress / length)
            sys.stdout.write("\r[%s%s]" % ('#' * done, '.' * (50-done)) )    
            sys.stdout.flush()

      if not os.path.exists(csv_path):
        try:
          patoolib.extract_archive(save_path, outdir=save_folder)
        except:
          os.remove(save_path)
          # download_file(current_utc, dataType, symbol, interval)

      #Commented out, as it would leads to sudden termination. 
      #os.remove(save_path)

    except urllib.error.HTTPError:
      print("\nFile not found: {}".format(download_url))
      csv_path = None     

  return csv_path

def is_valid_dataframe(dataType, interval, dataframe):
  valid = False

  if dataframe.shape[0] <= 0:
    valid = True
  else:
    interval_mili = intervalToMilliseconds(interval)
    start_mili = dataframe.loc[0,0]
    end_mili = dataframe.loc[dataframe.shape[0]-1,0] + interval_mili
    valid = ( end_mili - start_mili <= (dataframe.shape[0]+1) * interval_mili ) # Prove that shape[0] is large enough and not row is missing.

  return valid


def get_lastIds(paths): # This function knows some of the file structure.
  lastIds = {}

  for key, paths in paths.items():
    if len(paths) <= 0: continue
    path = paths[-1]
    if path is not None and os.path.exists(path):
      [dataType, symbol, interval] = key.split('.')
      dataframe = read_csv_file(dataType, path) # pd.read_csv(path, header=None, index_col=None)
      if dataframe.shape[0] > 0 and dataframe.shape[1] > 0:
        lastIds[key] = dataframe.loc[dataframe.shape[0]-1, 0] # dataframe.loc[dataframe.shape[0]-1][0]
      del dataframe
    else:
      lastIds[key] = None
  
  return lastIds


def load_nonempty_frame_file(clientPool, dataType, symbol, interval):
  utcnow = dt.datetime.utcnow().replace(tzinfo = pytz.utc)
  base_folder, file_name, _, _ = get_file_location(utcnow, dataType, symbol, interval)
  file_name = '_' + file_name #----------------------
  folder = os.path.join(os.environ.get('STORE_DIRECTORY'), base_folder)
  t_filepath = str(Path(os.path.join(folder, file_name)).with_suffix('.csv'))

  t_dataframe = None
  
  if os.path.exists(t_filepath) and os.path.getsize(t_filepath) > 0:
    t_dataframe = read_csv_file(dataType, t_filepath) #pd.read_csv(t_filepath, header=None, index_col=None)
  else:
    t_dataframe = pd.DataFrame()
    create_or_append_csv_file(t_filepath, '')

  if t_dataframe.shape[0] <= 0: t_dataframe = None

  return (t_dataframe, t_filepath)


def create_nonempty_frame_file(clientPool, dataType, symbol, interval, lastId_yeday):
  """
  If there is no today file, create one with '_' name prefix. Fill in the file up to 'now'. Create a dataframe from the file.
  """
  utcnow = dt.datetime.utcnow().replace(tzinfo = pytz.utc)
  base_folder, file_name, _, _ = get_file_location(utcnow, dataType, symbol, interval)
  file_name = '_' + file_name #----------------------
  folder = os.path.join(os.environ.get('STORE_DIRECTORY'), base_folder)
  t_filepath = str(Path(os.path.join(folder, file_name)).with_suffix('.csv'))

  
  t_dataframe = None
  
  if os.path.exists(t_filepath) and os.path.getsize(t_filepath) > 0:
    t_dataframe = read_csv_file(dataType, t_filepath) #pd.read_csv(t_filepath, header=None, index_col=None)
  else:
    t_dataframe = pd.DataFrame()
    create_or_append_csv_file(t_filepath, '')
  
  if t_dataframe.shape[0] <= 0:
    with clientPool.lock:
      dataline = get_data_for_single_id(clientPool.Next(), dataType, symbol, interval, lastId_yeday + 1 )
    if dataline is not None:
      df = pd.DataFrame([dataline])
      df = correct_dataframe_dtypes(dataType, df)
      create_or_append_csv_file(t_filepath, df.to_csv(columns=None, header=False, index=False))
      t_dataframe = read_csv_file(dataType, t_filepath)
    else:
      print('Inconsistent Binance Response 05.')
      t_dataframe, t_filepath = None, None
  
  # Do NOT do it here.
  #(t_dataframe, t_filepath, _) = extend_frontier_today_file(clientPool, dataType, symbol, interval, t_dataframe, t_filepath)

  return (t_dataframe, t_filepath)


def correct_dataframe_dtypes(dataType, df):
  if dataType == 'klines':
    # https://github.com/binance/binance-spot-api-docs/blob/master/rest-api.md#klinecandlestick-data
    df[0] = df[0].astype('int64')     # Open time
    df[1] = df[1].astype('float64')   # Open
    df[2] = df[2].astype('float64')   # High
    df[3] = df[3].astype('float64')   # Low
    df[4] = df[4].astype('float64')   # Close
    df[5] = df[5].astype('float64')   # Volume
    df[6] = df[6].astype('int64')     # Close time
    df[7] = df[7].astype('float64')   # Quote asset volume
    df[8] = df[8].astype('int64')     # Number of trades
    df[9] = df[9].astype('float64')   # Taker buy base asset volume
    df[10] = df[10].astype('float64') # Taker buy quote asset volume
    df[11] = df[11].astype('float64') # Ignore
  return df

def parse_datalines_to_datalines(dataType, datalines):
  if dataType == 'klines':
    # https://github.com/binance/binance-spot-api-docs/blob/master/rest-api.md#klinecandlestick-data
    length = len(datalines)
    for idx in range(length):
      dl = datalines[idx]
      dl[0]= round(dl[0])     # Open time. You can't use 'int64' here. Lucky, 'int' works as 'int64' here.
      dl[1] = float(dl[1])   # Open
      dl[2] = float(dl[2])   # High
      dl[3] = float(dl[3])   # Low
      dl[4] = float(dl[4])   # Close
      dl[5] = float(dl[5])   # Volume
      dl[6]= round(dl[6])     # Close time You can't use 'int64' here. Lucky, 'int' works as 'int64' here.
      dl[7] = float(dl[7])   # Quote asset volume
      dl[8]= round(dl[8])     # Number of trades
      dl[9] = float(dl[9])   # Taker buy base asset volume
      dl[10] = float(dl[10]) # Taker buy quote asset volume
      dl[11] = float(dl[11]) # Ignore
      datalines[idx] = dl
  return datalines


def fetch_save_csv_data(clientPool, binance_wait_sec, sample_utc, dataType, symbol, interval, filepath):
  today_first_ts_mili= round(dt.datetime.timestamp(get_current_day_start(sample_utc))*1000)
  tomorrow_first_ts_mili= round(dt.datetime.timestamp(get_next_day_start(sample_utc))*1000)
  nRowsToFetch = round((tomorrow_first_ts_mili-today_first_ts_mili) / intervalToMilliseconds(interval))
  
  successful = False
  rows = exact_fetch(clientPool, binance_wait_sec, dataType, symbol, interval, today_first_ts_mili, tomorrow_first_ts_mili, nRowsToFetch)
  if rows is not None:
    rows = parse_datalines_to_datalines(dataType, rows)
    dataframe = pd.DataFrame(rows)
    successful = create_or_append_csv_file(filepath, dataframe.to_csv(header = False, index = False)) 
  return successful

def select_from_single_historic_file_by_time(clientPool, binance_wait_sec, sample_utc, dataType, symbol, interval, start_utc, end_utc, lock = None):
  base_folder, file_name, _, _ = get_file_location(sample_utc, dataType, symbol, interval)
  folder = os.path.join(os.environ.get('STORE_DIRECTORY'), base_folder)
  filepath = str(Path(os.path.join(folder, file_name)).with_suffix('.csv'))

  successful = True
  if not os.path.exists(filepath):
    path = download_file(sample_utc, dataType, symbol, interval)
    successful = False if path is None else True
    if not successful:
      successful = fetch_save_csv_data(clientPool, binance_wait_sec, sample_utc, dataType, symbol, interval, filepath)
  if not successful:
    raise Exception('Unable to get day data.')

  dataframe = read_csv_file(dataType, filepath) #pd.read_csv(file_path)
  if dataframe is not None:
    return select_from_dataframe_by_time(dataType, dataframe, start_utc, end_utc, lock = lock )
  else:
    return None


def select_from_dataframe_by_time(dataType, dataframe, start_utc, end_utc, lock = None ):
  timeslot = get_timeslot(dataType)
  start_timestamp= round(dt.datetime.timestamp(start_utc)*1000)
  end_timestamp= round(dt.datetime.timestamp(end_utc)*1000)
  
  if lock is not None: lock.acquire()
  
  if dataframe.shape[0] > 0:
    df = dataframe.loc[ ( start_timestamp <= dataframe[timeslot] ) & ( dataframe[timeslot] < end_timestamp ) ] # note "start<=" and "< end".
  else: df = pd.DataFrame()

  if lock is not None: lock.release()

  df.index = [*range(df.shape[0])]

  return df


def select_from_single_historic_file_by_id(sample_utc, dataType, symbol, interval, start_id, end_id):
  base_folder, file_name, _, _ = get_file_location(sample_utc, dataType, symbol, interval)
  folder = os.path.join(os.environ.get('STORE_DIRECTORY'), base_folder)
  filepath = str(Path(os.path.join(folder, file_name)).with_suffix('.csv'))

  if not os.path.exists(filepath):
    download_file(sample_utc, dataType, symbol, interval)

  dataframe = pd.read_csv(dataType, filepath)
  return select_from_dataframe_by_id(dataType, dataframe, start_id, end_id )

def select_from_dataframe_by_id(dataType, dataframe, start_id, end_id ): # end_id EXCLUSIVE.
  dataframe = dataframe.loc[ ( start_id <= dataframe[0] ) & ( dataframe[0] < end_id ) ]
  return dataframe


def full_prepend_frame(lock, clientPool, dataType, symbol, interval, t_dataframe, t_filepath):
  
  shape = t_dataframe.shape
  if shape[0] <= 0: return

  if dataType == 'klines':

    slot = get_timeslot(dataType)
    endtime_ts = t_dataframe.loc[shape[0]-1][slot]
    dt_today_utc = dt.datetime.utcfromtimestamp(endtime_ts/1000 - 1) # - 1 for safety.
    dt_today_utc.replace(tzinfo=pytz.utc)
    starttime_ts= round( dt.datetime.timestamp( get_current_day_start(dt_today_utc) ) * 1000 )

    print("cheching time conversions. start of today_utc: ",  dt.datetime.utcfromtimestamp( starttime_ts/1000) )

    lastId = starttime_ts - 1
    maxLimit = 500
    nToReceive_plan= round( (endtime_ts - starttime_ts) / intervalToMilliseconds(interval))
    nToReceive = nToReceive_plan
    datalines = []

    trials = 0

    while nToReceive > 0:
      maxLimit = min(nToReceive, 500)

      try:
        if dataType == 'klines':
          with clientPool.lock:
            tm.sleep(Config['binance_wait_sec'])
            lines = clientPool.Next().get_klines(symbol = symbol, interval = interval, limit = maxLimit, startTime = lastId + 1, endTime = None)
        elif dataType == 'trafes':
          lines = None
    
        elif dataType == 'aggTrades':
          with clientPool.lock: 
            tm.sleep(Config['binance_wait_sec'])
            lines = clientPool.Next().get_aggregate_trades(symbol = symbol, fromId = lastId + 1, startTime = None, endTime = None, limit = maxLimit)
      except:
        trials += 1
        if trials < 3: continue
        else: raise Exception('Failed in an attemp to full_prepend_frame.')

      nReceived = len(lines)
      if nReceived > 0: 
        lastId = lines[-1][0]
        datalines += lines

      nToReceive -= nReceived
      trials = 0 

  if len(datalines) != nToReceive_plan:
    raise Exception('Inconsistendy')
  datalines = parse_datalines_to_datalines(dataType, datalines)

  t_dataframe = pd.concat([pd.DataFrame(datalines), t_dataframe])

  return


def max_grow_frame_file(lock, clientPool, dataType, symbol, interval, t_dataframe, t_filepath):
  """
  Be aware of date change. 
  If date change is detected, save yesterday file and renew the today file.
  """
  lastId = None
  if t_dataframe.shape[0] > 0: lastId = t_dataframe.loc[t_dataframe.shape[0]-1, 0]
  if lastId is None: return (t_dataframe, t_filepath, None)

  datalines_new = max_fetch_data_from_last(clientPool, dataType, symbol, interval, lastId)
  if len(datalines_new) <= 0: return (t_dataframe, t_filepath, None)

  now_utc = dt.datetime.utcnow().replace(tzinfo = pytz.utc)
  today_start_ts_mili= round(dt.datetime.timestamp(get_current_day_start(now_utc))*1000)
  df_new = pd.DataFrame(datalines_new)

  timeslot = get_timeslot(dataType)
  df_yeday = df_new.loc[ df_new[timeslot] < today_start_ts_mili ]
  df_today = df_new.loc[ df_new[timeslot] >= today_start_ts_mili ]
  
  if df_yeday.shape[0] > 0 and df_today.shape[0] > 0: # date change is detected. ======================
    # Note less than today_start_ts does NOT necessarily mean yesterday. Improve the code later.
    t_dataframe, t_filepath = change_date(dataType, symbol, interval, t_dataframe, t_filepath, df_yeday, df_today, now_utc )

  elif df_today.shape[0] > 0: # No date change detected. Regular.
    with lock:
      create_or_append_csv_file(t_filepath, df_today.to_csv(header = False, index = False))
      t_dataframe = read_csv_file(dataType, t_filepath)

  elif df_yeday.shape[0] > 0: # Although the clock tells today, the data time is yesterday.
    print('Check this-----------.')
    with lock:
      create_or_append_csv_file(t_filepath, df_today.to_csv(header = False, index = False))
      t_dataframe = read_csv_file(dataType, t_filepath)

  else:
    t_dataframe, t_filepath = t_dataframe, t_filepath

  return (t_dataframe, t_filepath, df_new)


def insert_rows(dataframe, row_number, rows):
    # Slice the upper half of the dataframe
    df1 = dataframe[0:row_number]
   
    # Store the result of lower half of the dataframe
    df2 = dataframe[row_number:]
   
    # Inser the row in the upper half dataframe
    for row in rows:
      df1.loc[row_number]=row
      row_number += 1
   
    # Concat the two dataframes
    df_result = pd.concat([df1, df2])
   
    # Reassign the index labels
    df_result.index = [*range(df_result.shape[0])]
   
    # Return the updated dataframe
    return df_result


def insert_rows_safely(dataframe, row_number, rows):
    assert len(rows) > 0

    delta = 0.9 / len(rows)
    for idx in range(len(rows)):
        dataframe.loc[row_number + delta * idx + 0.05] = rows[idx]

    dataframe.sort_index(inplace=True)
    dataframe.index = [*range(dataframe.shape[0])]

    return dataframe


def update_with_stream_data_v2(lock, dataType, symbol, interval, t_dataframe, t_filepath, tickbuffer, data, granular = False):

  report = 'success'

  if dataType == 'klines':
    pass
    """
    # https://github.com/binance/binance-spot-api-docs/blob/master/rest-api.md#klinecandlestick-data
    df[0] = df[0].astype('int64')     # Open time
    df[1] = df[1].astype('float64')   # Open
    df[2] = df[2].astype('float64')   # High
    df[3] = df[3].astype('float64')   # Low
    df[4] = df[4].astype('float64')   # Close
    df[5] = df[5].astype('float64')   # Volume --- guess it's base voluem + quote volume. This guess is wrong. It's purely base volume.
    df[6] = df[6].astype('int64')     # Close time
    df[7] = df[7].astype('float64')   # Quote asset volume
    df[8] = df[8].astype('int64')     # Number of trades
    df[9] = df[9].astype('float64')   # Taker buy base asset volume
    df[10] = df[10].astype('float64') # Taker buy quote asset volume
    df[11] = df[11].astype('float64') # Ignore
    """
    """
    # https://github.com/binance/binance-spot-api-docs/blob/master/web-socket-streams.md#klinecandlestick-streams
    {
      "e": "kline",     // Event type
      "E": 123456789,   // Event time
      "s": "BNBBTC",    // Symbol
      "k": {
        "t": 123400000, // Kline start time
        "T": 123460000, // Kline close time
        "s": "BNBBTC",  // Symbol
        "i": "1m",      // Interval
        "f": 100,       // First trade ID
        "L": 200,       // Last trade ID
        "o": "0.0010",  // Open price
        "c": "0.0020",  // Close price
        "h": "0.0025",  // High price
        "l": "0.0015",  // Low price
        "v": "1000",    // Base asset volume
        "n": 100,       // Number of trades
        "x": false,     // Is this kline closed?
        "q": "1.0000",  // Quote asset volume
        "V": "500",     // Taker buy base asset volume
        "Q": "0.500",   // Taker buy quote asset volume
        "B": "123456"   // Ignore
      }
    }
    """
    ts_mili, price = None, None

    eventtime = data['E']
    kstream = data['k']
    starttime_stream = kstream['t']
    closetime_stream = kstream['T']
    closed = kstream['x']
    intervalmili = intervalToMilliseconds(interval)

    def get_new_row():
      (open, close, high, low, ntrades, vbase, vquote, vbasetakerbuy, vquotetakerbuy) = \
        (kstream['o'], kstream['c'], kstream['h'], kstream['l'], kstream['n'], kstream['v'], kstream['q'], kstream['V'], kstream['Q'])
      volume = float(kstream['v'])
      ignore = kstream['B']
      new_row_raw = [starttime_stream, open, high, low, close, volume, closetime_stream, vquote, ntrades, vbasetakerbuy, vquotetakerbuy, ignore]
      [new_row] = parse_datalines_to_datalines(dataType, [new_row_raw])
      return new_row

    new_row = None

    with lock:
      if not bool(granular) and not closed and t_dataframe.shape[0] <= 0:
        if new_row is None: new_row = get_new_row()
        for col in range(len(new_row)): t_dataframe.loc[0, col] = new_row[col]
        correct_dataframe_dtypes(dataType, t_dataframe)


    if bool(granular) or closed:  
      #========================= Update dataframe

      with lock:
        if not bool(granular) and t_dataframe.shape[0] == 1: # This row is a <temporary> row and it's time to remove it. It was not used yet to prepend data to the dataframe.
          t_dataframe.drop([0], inplace=True)

        if new_row is None: new_row = get_new_row()

        ts_mili = starttime_stream
        price = new_row[4]

        shape = t_dataframe.shape       
        if shape[0] <= 0:
          for col in range(len(new_row)): t_dataframe.loc[0, col] = new_row[col]
          correct_dataframe_dtypes(dataType, t_dataframe)
          #del t_dataframe
          #t_dataframe = pd.DataFrame([new_row]) # You can't prepend a row to an empty dataframe.

        else:
          opentime_framelast = t_dataframe.loc[t_dataframe.shape[0]-1][0].astype(t_dataframe.dtypes[0])

          if opentime_framelast >= starttime_stream: # Time to update the last row.
            # Stream is talking about the same candle as the frame last candle.        
            t_dataframe.loc[t_dataframe.shape[0]-1] = new_row # closed or not.

          else: # Time to append with a new row.
            # Stream is talking about a candle that is later than the frame last candle.
            if opentime_framelast < starttime_stream - intervalmili : # some candles are missing in the frame.
              report = 'frame_lagging'

            if not is_date_changing(starttime_stream):
              t_dataframe.loc[t_dataframe.shape[0]] = new_row # closed or not.
              # commented out for speed. t_dataframe = correct_dataframe_dtypes(dataType, t_dataframe)
            else:
              df_inc_yeday = pd.DataFrame()
              df_inc_today = pd.DataFrame([new_row])
              today_utc = dt.datetime.utcfromtimestamp(starttime_stream/1000 + 1) # + 1 for safety.
              today_utc.replace(tzinfo=pytz.utc)
              change_date(dataType, symbol, interval, t_dataframe, t_filepath, df_inc_yeday, df_inc_today, today_utc ) # closed or not.

      #======================= Append and pop from tickbuffer.
      if bool(granular):
        if new_row is None: new_row = get_new_row()
        tickbuffer.append((eventtime, new_row[1], new_row[4], new_row[2], new_row[3], new_row[8], kstream['v'], new_row[7], new_row[9], new_row[10]))
        # tickbuffer.append((eventtime, open, close, high, low, ntrades, vbase, vquote, vbasetakerbuy, vquotetakerbuy))

        # Ugly but fastest way to remove some first elements in an ordered list.
        fromtime = eventtime - intervalmili # ---------- Design decision: one interval of streaming data will be maintained in the tickbuffer.
        length_initial = len(tickbuffer)
        max_idx = 0
        while max_idx < length_initial:
          if tickbuffer[max_idx][0] >= fromtime: break # [0] for eventtime. Note eventtime is not exactly same with open even when closed == True. Slightly larger.
          else: max_idx += 1
        with lock: del tickbuffer[: max_idx]

    #======================= Check for lagging.

    shape = t_dataframe.shape
    if shape[0] > 0:
      last = t_dataframe.loc[t_dataframe.shape[0]-1]
      opentime_framelast = last[0].astype(t_dataframe.dtypes[0])
      if opentime_framelast < starttime_stream - intervalmili :
        report = 'frame_lagging'
    else:
      report = 'frame_empty'

  else:
    raise Exception('Unsupported dataType: {}'.format(dataType))

  return report, dt.datetime.fromtimestamp(starttime_stream/1000), ts_mili, price



def fill_in_missing_slots(lock, clientPool, binance_wait_sec, dataType, symbol, interval, t_dataframe):
    # We assume t_dataframe stores unique time slots in the increading order.
    # We assume that at most one instance of this function is working at a time
    # We assume that this is the only function that modifies t_dataframe everywhere except the last row.

    successful = True
    held_on_io = False

    slot = get_timeslot(dataType)
    interval_mili = intervalToMilliseconds(interval)

    search_start_row = 0; search_end_row = 0

    shape = t_dataframe.shape
    if shape[0] > 0:
        today_first_ts_mili= round(dt.datetime.timestamp(get_current_day_start(dt.datetime.utcnow().replace(tzinfo=pytz.utc)))*1000)
        first_ts_mili= round(t_dataframe.loc[0][slot]) # Type is not stable in Pandas dataframes.
        if today_first_ts_mili < first_ts_mili: # We need to prepend the dataframe with stuff.
        # Prepend with exchage_rows[ today_first_ts_mili, first_ts_mili ).
            nRowsToFetch= round((first_ts_mili - today_first_ts_mili) / interval_mili)
            if nRowsToFetch > 0:
                rows = exact_fetch(clientPool, binance_wait_sec, dataType, symbol, interval, today_first_ts_mili, first_ts_mili, nRowsToFetch)
                held_on_io = True
                if rows is not None:
                    rows = parse_datalines_to_datalines(dataType, rows)
                    with lock: insert_rows_safely(t_dataframe, -1, rows)
                    search_start_row = nRowsToFetch
                else: successful = False
            else:
                debug = 3
        # assert int(t_dataframe.loc[search_start_row][slot]) == first_ts_mili, "asseertion error: int(t_dataframe.loc[search_start_row][slot]) == first_ts_mili"

        #if search_start_row > 0: # We just held the lock long time.
        #    tm.sleep(Config['binance_wait_sec'])
        
        #----------------- Fill in the missing, intermidate rows.

        if successful: # Not tested.

            shape = t_dataframe.shape
            search_end_row = shape[0] - 1

            if (round(t_dataframe.loc[search_end_row][slot]) - round(t_dataframe.loc[search_start_row][slot])) == (search_end_row - search_start_row) * interval_mili:
                pass # no missing.
            else:
                row_prev = search_start_row
                ts_prev= round(t_dataframe.loc[row_prev][slot])
                row_number = search_start_row + 1
                while row_number <= search_end_row:
                    ts= round(t_dataframe.loc[row_number][slot])
                    if ts_prev + interval_mili == ts:
                        ts_prev = ts; row_number += 1
                    elif ts_prev + interval_mili > ts:
                        raise Exception('time slot is not in increasing order.')
                    else: # ts_prev + interval_mili < ts
                        # tetch exchange_rows[ts_prev + interval_mili, ts) to dataframe.loc[row_number: ?)
                        nRowsToFetch= round((ts - ts_prev - interval_mili) / interval_mili)
                        if nRowsToFetch > 0:
                          rows = exact_fetch(clientPool, binance_wait_sec, dataType, symbol, interval, ts_prev + interval_mili, ts, nRowsToFetch)
                          held_on_io = True
                          if rows is not None:
                              rows = parse_datalines_to_datalines(dataType, rows)
                              with lock: insert_rows_safely(t_dataframe, row_number, rows)
                              ts_prev = ts
                              row_number += (ts - ts_prev - interval_mili) / interval_mili + 1
                          else: 
                              successful = False
                              break
    else:
        successful = False # Design decision.
  
    return successful, held_on_io



def accept_stream_data(lock, dataType, symbol, interval, t_dataframe, t_filepath, tickbuffer, data, granular = False):
  print(data['s'], data['k']['i'], 'granular' if granular else '')

  report = 'success'

  if dataType == 'klines':
    pass
    """
    # https://github.com/binance/binance-spot-api-docs/blob/master/rest-api.md#klinecandlestick-data
    df[0] = df[0].astype('int64')     # Open time
    df[1] = df[1].astype('float64')   # Open
    df[2] = df[2].astype('float64')   # High
    df[3] = df[3].astype('float64')   # Low
    df[4] = df[4].astype('float64')   # Close
    df[5] = df[5].astype('float64')   # Volume --- guess it's base voluem + quote volume. This guess is wrong. It's purely base volume.
    df[6] = df[6].astype('int64')     # Close time
    df[7] = df[7].astype('float64')   # Quote asset volume
    df[8] = df[8].astype('int64')     # Number of trades
    df[9] = df[9].astype('float64')   # Taker buy base asset volume
    df[10] = df[10].astype('float64') # Taker buy quote asset volume
    df[11] = df[11].astype('float64') # Ignore
    """
    """
    # https://github.com/binance/binance-spot-api-docs/blob/master/web-socket-streams.md#klinecandlestick-streams
    {
      "e": "kline",     // Event type
      "E": 123456789,   // Event time
      "s": "BNBBTC",    // Symbol
      "k": {
        "t": 123400000, // Kline start time
        "T": 123460000, // Kline close time
        "s": "BNBBTC",  // Symbol
        "i": "1m",      // Interval
        "f": 100,       // First trade ID
        "L": 200,       // Last trade ID
        "o": "0.0010",  // Open price
        "c": "0.0020",  // Close price
        "h": "0.0025",  // High price
        "l": "0.0015",  // Low price
        "v": "1000",    // Base asset volume
        "n": 100,       // Number of trades
        "x": false,     // Is this kline closed?
        "q": "1.0000",  // Quote asset volume
        "V": "500",     // Taker buy base asset volume
        "Q": "0.500",   // Taker buy quote asset volume
        "B": "123456"   // Ignore
      }
    }
    """
    eventtime = data['E']
    kstream = data['k']
    starttime_stream = kstream['t']
    closetime_stream = kstream['T']
    closed = kstream['x']

    if granular or closed:

      (open, close, high, low, ntrades, vbase, vquote, vbasetakerbuy, vquotetakerbuy) = \
        (kstream['o'], kstream['c'], kstream['h'], kstream['l'], kstream['n'], kstream['v'], kstream['q'], kstream['V'], kstream['Q'])

      #======================= Append and pop from tickbuffer.
      tickbuffer.append((eventtime, open, close, high, low, ntrades, vbase, vquote, vbasetakerbuy, vquotetakerbuy))
      # Ugly but fastest way to remove some first elements in an ordered list.
      intervalmili = intervalToMilliseconds(interval)
      fromtime = eventtime - intervalmili # ---------- Design decision: one interval of streaming data will be maintained in the tickbuffer.
      length_initial = len(tickbuffer)
      max_idx = 0
      while max_idx < length_initial:
        if tickbuffer[max_idx][0] >= fromtime: break # [0] for eventtime. Note eventtime is not exactly same with open even when closed == True. Slightly larger.
        else: max_idx += 1

      with lock: del tickbuffer[: max_idx]

      #========================= Update dataframe
      volume = float(kstream['v']) # + float(kstream['q'])  This guess is wrong.
      ignore = kstream['B']
      new_row_raw = [starttime_stream, open, high, low, close, volume, closetime_stream, vquote, ntrades, vbasetakerbuy, vquotetakerbuy, ignore]
      [new_row] = parse_datalines_to_datalines(dataType, [new_row_raw])


      with lock:
          shape = t_dataframe.shape[0]
          if shape[0] <= 0:
            t_dataframe.loc[0] = new_row

          else:
            opentime_framelast = t_dataframe.loc[t_dataframe.shape[0]-1][0].astype(t_dataframe.dtypes[0])

            if opentime_framelast >= starttime_stream:
              # Stream is talking about the same candle as the frame last candle.        
              t_dataframe.loc[t_dataframe.shape[0]-1] = new_row # closed or not.

            else:
              # Stream is talking about a candle that is later than the frame last candle.
              if opentime_framelast + intervalmili < starttime_stream: # some candles are missing in the frame.
                report = 'frame_lagging'

              if not is_date_changing(starttime_stream):
                t_dataframe.loc[t_dataframe.shape[0]] = new_row # closed or not.
                # commented out for speed. t_dataframe = correct_dataframe_dtypes(dataType, t_dataframe)
              else:
                df_inc_yeday = pd.DataFrame()
                df_inc_today = pd.DataFrame([new_row])
                today_utc = dt.datetime.utcfromtimestamp(1,0 * starttime_stream/1000 + 1) # + 1 for safety.
                change_date(dataType, symbol, interval, t_dataframe, t_filepath, df_inc_yeday, df_inc_today, today_utc ) # closed or not.

    #======================= Check for lagging.
    last = t_dataframe.loc[t_dataframe.shape[0]-1]
    opentime_framelast = last[0].astype(t_dataframe.dtypes[0])
    if opentime_framelast < starttime_stream - intervalToMilliseconds(interval):
      report = 'frame_lagging'


  else:
    raise Exception('Unsupported dataType: {}'.format(dataType))

  return report


def is_date_changing(timestampmili):
  dt_utc = dt.datetime.utcfromtimestamp(timestampmili/1000)
  return timestampmili == int(dt.datetime.timestamp(get_current_day_start(dt_utc))*1000)


def change_date(dataType, symbol, interval, t_dataframe, t_filepath, df_inc_yeday, df_inc_today, today_utc ):

  if dataType == 'klines':
    # Close t_dataframe and t_filepath with df_yeday, and make them yesterday.
    create_or_append_csv_file(t_filepath, df_inc_yeday.to_csv(header = False, index = False))
    t_dataframe = read_csv_file(dataType, t_filepath) # Just try the file.
    yeday_utc = today_utc - dt.timedelta(days=1)
    base_folder, file_name, save_folder, save_path = get_file_location(yeday_utc, dataType, symbol, interval)
    folder = os.path.join(os.environ.get('STORE_DIRECTORY'), base_folder)
    yeday_path = str(Path(os.path.join(folder, file_name)).with_suffix('.csv'))

    os.remove(yeday_path) # Just in case.
    os.rename(t_filepath, yeday_path)
    del t_dataframe, t_filepath

    # Open a new t_dataframe and t_filepath, and fill in them with df_today.
    base_folder, file_name, _, _ = get_file_location(today_utc, dataType, symbol, interval)
    file_name = '_' + file_name #----------------------
    folder = os.path.join(os.environ.get('STORE_DIRECTORY'), base_folder)
    t_filepath = str(Path(os.path.join(folder, file_name)).with_suffix('.csv'))

    os.remove(t_filepath) # In case.
    create_or_append_csv_file(t_filepath, df_inc_today.to_csv(header = False, index = False))
    t_dataframe = read_csv_file(dataType, t_filepath)
    
  else:
    raise Exception('Unsupported dataType: {}'.format(dataType))

  return t_dataframe, t_filepath


def get_utctime_by_id(client, dataType, symbol, interval, id):

  utctime = None
  
  if id is None: 
    utctime = None
  else:
    data = get_data_for_single_id(client, dataType, symbol, interval, id)
    if data is None:
      utctime = None
    else:
      if dataType == 'klines':
        ts = data[0]
        utctime = dt.datetime.utcfromtimestamp(ts/1000)
      elif dataType == 'trades':
        ts = data['time']
        utctime = dt.datetime.utcfromtimestamp(ts/1000)
      elif dataType == 'aggTrades':
        ts = data['T']
        utctime = dt.datetime.utcfromtimestamp(ts/1000)
      else:
        raise Exception('Invalid dataType.')

  if utctime is not None: utctime.replace(tzinfo=pytz.utc)
  
  return utctime


def get_data_for_single_id(client, dataType, symbol, interval, id):
  dataline = None
  
  if dataType == 'klines':
    #klines = client.get_historical_klines(symbol, interval, start_str = str(id), end_str = None, limit = 1) #  Defaults to SPOT.
    klines = client.get_klines(symbol=symbol, interval=interval, limit=1, startTime=id, endTime=None)

    if len(klines) != 1:
      raise Exception('Inconsistent response from Binance - 00.')
    else:
      dataline = klines[0]
  elif dataType == 'trades':
    trades = client.get_historical_trades( symbol, 1, id )
    if len(trades) != 1: 
      raise Exception('Inconsistent response from Binance - 01.')
    else:
      dataline = trades[0]
  elif dataType == 'aggTrades':
    aggTrades = client.get_aggregate_trades(symbol, id, None, None, 1)
    if len(aggTrades) != 1:
      raise Exception('Inconsistent response from Binance - 02.')
    else:
      dataline = aggTrades[0]
  else:
    raise Exception('Invalid dataType.')
  
  return dataline


def max_fetch_data_from_last(clientPool, dataType, symbol, interval, lastId):

  #dataframe = pd.DataFrame()
  maxLimit = 500
  nReceived = maxLimit
  datalines = []

  print("------- max_fetch_data_from_last called. {} lastId: {}".format(symbol, lastId))

  trials = 0

  while nReceived >= maxLimit:

    try:
      if dataType == 'klines':
        with clientPool.lock:
          tm.sleep(Config['binance_wait_sec'])
          lines = clientPool.Next().get_klines(symbol = symbol, interval = interval, limit = maxLimit, startTime = lastId + 1, endTime = None)
      elif dataType == 'trafes':
        lines = None
  
      elif dataType == 'aggTrades':
        with clientPool.lock:
          tm.sleep(Config['binance_wait_sec'])
          lines = clientPool.Next().get_aggregate_trades(symbol = symbol, fromId = lastId + 1, startTime = None, endTime = None, limit = maxLimit)
    except:
      trials += 1
      print("Binance client was disconnectd.")
      if trials <= 3: continue

    nReceived = len(lines)
    if len(lines) > 0: 
      lastId = lines[-1][0]
      datalines += lines

  # Note: Most of the time, the last line is under construction if dataType == 'klines' or 'aggTrades'?
  # Do NOT remove them, though, because it sometimes has just been completed.

  return datalines


def fetch_full_day_data_from_last(clientPool, dataType, symbol, interval, lastId):
  maxLimit = 500
  nToReceive= round(24*60*60*1000 / intervalToMilliseconds(interval))
  datalines = []

  print("------- fetch_full_day_data_from_last called. {} lastId: {}".format(symbol, lastId))

  trials = 0
  nReceived = maxLimit

  while nToReceive > 0:
    maxLimit = min(nToReceive, 500)

    try:
      if dataType == 'klines':
        with clientPool.lock:
          tm.sleep(Config['binance_wait_sec'])
          lines = clientPool.Next().get_klines(symbol = symbol, interval = interval, limit = maxLimit, startTime = lastId + 1, endTime = None)
      elif dataType == 'trafes':
        lines = None
  
      elif dataType == 'aggTrades':
        with clientPool.lock:
          tm.sleep(Config['binance_wait_sec'])
          lines = clientPool.Next().get_aggregate_trades(symbol = symbol, fromId = lastId + 1, startTime = None, endTime = None, limit = maxLimit)
    except:
      trials += 1
      if trials < 3: continue

    nReceived = len(lines)
    if len(lines) > 0: 
      lastId = lines[-1][0]
      datalines += lines

    nToReceive -= nReceived

  return datalines


def create_full_day_data(clientPool, dataType, symbol, interval, prev_day_lastId, sampletime_utc):
  lines = fetch_full_day_data_from_last(clientPool, dataType, symbol, interval, prev_day_lastId)
  if len(lines) > 0:
    dataframe = pd.DataFrame(lines)

    base_folder, file_name, save_folder, save_path = get_file_location(sampletime_utc, dataType, symbol, interval)
    #download_path = os.path.join(base_folder, file_name)
    csv_path = str(Path(save_path).with_suffix('.csv'))

    create_or_append_csv_file(csv_path, dataframe.to_csv(header = False, index = False))
    dataframe = read_csv_file(dataType, csv_path)

    lastId= round( dataframe.loc[dataframe.shape[0]-1][0] )# for klines only.

    return lastId


def get_timeslot(dataType):
  return 0 if dataType == 'klines' else 3 if dataType == 'trades' else 5 if dataType == 'aggTrades' else None


def read_csv_file(dataType, file_path):
  dataframe = None
  try:
    dataframe = pd.read_csv(file_path, header=None, index_col=None)
  except:
    datetime = None

  return dataframe

def write_csv_file(dataframe, filepath):
  dataframe.to_csv(filepath, columns=None, header=False, index=False)

def create_or_append_csv_file(file_path, csv_data):
  if os.path.exists(file_path):
    append_write = 'a'
  else:
    append_write = 'w'
  
  successful = True
  try:
    file = open(file_path, append_write)
    #last_line = file.readlines()[-1]
    #if not (last_line is '\n' or last_line is '\n\r'):
    #  file.write('\n\r')
    file.write(csv_data)
    #file.write('\n\r')
    file.close()
  except:
    successful = False

  return successful


def intervalToMilliseconds(interval):
    """Convert a Binance interval string to milliseconds

    :param interval: Binance interval string 1m, 3m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 8h, 12h, 1d, 3d, 1w
    :type interval: str

    :return:
        None if unit not one of m, h, d or w
        None if string not in correct format
        int value of interval in milliseconds
    """
    ms = None
    seconds_per_unit = {
        "m": 60,
        "h": 60 * 60,
        "d": 24 * 60 * 60,
        "w": 7 * 24 * 60 * 60
    }

    unit = interval[-1]
    if unit in seconds_per_unit:
        try:
            ms= int(interval[:-1]) * seconds_per_unit[unit] * 1000
        except ValueError:
            pass
    return ms

def convert_to_date_object(d):
  year, month, day = [int(x) for x in d.split('-')]
  date_obj = dt.datetime.date(year, month, day)
  return date_obj

def match_date_regex(arg_value, pat=re.compile(r'\d{4}-\d{2}-\d{2}')):
  if not pat.match(arg_value):
    raise ArgumentTypeError
  return arg_value

def check_directory(arg_value):
  if os.path.exists(arg_value):
    while True:
      option = input('Folder already exists! Do you want to overwrite it? y/n  ')
      if option != 'y' and option != 'n':
        print('Invalid Option!')
        continue
      elif option == 'y':
        shutil.rmtree(arg_value)
        break
      else:
        break
  return arg_value

"""
def get_parser(parser_type):
  parser = ArgumentParser(description=("This is a script to download historical {} data").format(parser_type), formatter_class=RawTextHelpFormatter)
  parser.add_argument(
      '-s', dest='symbols', nargs='+',
      help='Single symbol or multiple symbols separated by space')
  parser.add_argument(
      '-y', dest='years', default=YEARS, nargs='+', choices=YEARS,
      help='Single year or multiple years separated by space\n-y 2019 2021 means to download {} from 2019 and 2021'.format(parser_type))
  parser.add_argument(
      '-m', dest='months', default=MONTHS,  nargs='+', type=int, choices=MONTHS,
      help='Single month or multiple months separated by space\n-m 2 12 means to download {} from feb and dec'.format(parser_type))
  parser.add_argument(
      '-d', dest='dates', nargs='+', type=match_date_regex,
      help='Date to download in [YYYY-MM-DD] format\nsingle date or multiple dates separated by space\ndownload past 35 days if no argument is parsed')
  parser.add_argument(
      '-startDate', dest='startDate', type=match_date_regex,
      help='Starting date to download in [YYYY-MM-DD] format')
  parser.add_argument(
      '-endDate', dest='endDate', type=match_date_regex,
      help='Ending date to download in [YYYY-MM-DD] format')
  parser.add_argument(
      '-folder', dest='folder', type=check_directory,
      help='Directory to store the downloaded data')
  parser.add_argument(
      '-c', dest='checksum', default=0, type=int, choices=[0,1],
      help='1 to download checksum file, default 0')

  if parser_type == 'klines':
    parser.add_argument(
      '-i', dest='intervals', default=INTERVALS, nargs='+', choices=INTERVALS,
      help='single kline interval or multiple intervals separated by space\n-i 1m 1w means to download klines interval of 1minute and 1week')

  return parser

"""




#https://code.luasoftware.com/tutorials/cryptocurrency/python-connect-to-binance-api/

import time
import json
import hmac
import hashlib
import requests
from urllib.parse import urljoin, urlencode

API_KEY = 'UIGu...'
SECRET_KEY = 'VyX...'
BASE_URL_API = 'https://api.binance.com/'

headers = {
    'X-MBX-APIKEY': API_KEY
}

class BinanceException(Exception):
    def __init__(self, status_code, data):

        self.status_code = status_code
        if data:
            self.code = data['code']
            self.msg = data['msg']
        else:
            self.code = None
            self.msg = None
        message = f"{status_code} [{self.code}] {self.msg}"

        # Python 2.x
        # super(BinanceException, self).__init__(message)
        super().__init__(message)

def Get_Server_time():
  PATH =  '/api/v1/time'
  params = None

  timestamp= round(time.time() * 1000)

  url = urljoin(BASE_URL_API, PATH)
  r = requests.get(url, params=params)
  if r.status_code == 200:
      # print(json.dumps(r.json(), indent=2))
      data = r.json()
      print(f"diff={timestamp - data['serverTime']}ms")
  else:
      raise BinanceException(status_code=r.status_code, data=r.json())


def Get_Price():
  PATH = '/api/v3/ticker/price'
  params = {
      'symbol': 'BTCUSDT'
  }

  url = urljoin(BASE_URL_API, PATH)
  r = requests.get(url, headers=headers, params=params)
  if r.status_code == 200:
      print(json.dumps(r.json(), indent=2))
  else:
      raise BinanceException(status_code=r.status_code, data=r.json())


def Get_Order_Book():
  PATH = '/api/v1/depth'
  params = {
      'symbol': 'BTCUSDT',
      'limit': 5
  }

  url = urljoin(BASE_URL_API, PATH)
  r = requests.get(url, headers=headers, params=params)
  if r.status_code == 200:
      print(json.dumps(r.json(), indent=2))
  else:
      raise BinanceException(status_code=r.status_code, data=r.json())


def Create_Order():

  PATH = '/api/v3/order'
  timestamp= round(time.time() * 1000)
  params = {
      'symbol': 'ETHUSDT',
      'side': 'SELL',
      'type': 'LIMIT',
      'timeInForce': 'GTC',
      'quantity': 0.1,
      'price': 500.0,
      'recvWindow': 5000,
      'timestamp': timestamp
  }

  query_string = urlencode(params)
  params['signature'] = hmac.new(SECRET_KEY.encode('utf-8'), query_string.encode('utf-8'), hashlib.sha256).hexdigest()

  url = urljoin(BASE_URL_API, PATH)
  r = requests.post(url, headers=headers, params=params)
  if r.status_code == 200:
      data = r.json()
      print(json.dumps(data, indent=2))
  else:
      raise BinanceException(status_code=r.status_code, data=r.json())

def Get_Order():
  PATH = '/api/v3/order'
  timestamp= round(time.time() * 1000)
  params = {
      'symbol': 'ETHUSDT',
      'orderId': '336683281',
      'recvWindow': 5000,
      'timestamp': timestamp
  }

  query_string = urlencode(params)
  params['signature'] = hmac.new(SECRET_KEY.encode('utf-8'), query_string.encode('utf-8'), hashlib.sha256).hexdigest()

  url = urljoin(BASE_URL_API, PATH)
  r = requests.get(url, headers=headers, params=params)
  if r.status_code == 200:
      data = r.json()
      print(json.dumps(data, indent=2))
  else:
      raise BinanceException(status_code=r.status_code, data=r.json())


def Delete_Order():
  PATH = '/api/v3/order'
  timestamp= round(time.time() * 1000)
  params = {
      'symbol': 'ETHUSDT',
      'orderId': '336683281',
      'recvWindow': 5000,
      'timestamp': timestamp
  }

  query_string = urlencode(params)
  params['signature'] = hmac.new(SECRET_KEY.encode('utf-8'), query_string.encode('utf-8'), hashlib.sha256).hexdigest()

  url = urljoin(BASE_URL_API, PATH)
  r = requests.delete(url, headers=headers, params=params)
  if r.status_code == 200:
      data = r.json()
      print(json.dumps(data, indent=2))
  else:
      raise BinanceException(status_code=r.status_code, data=r.json())

