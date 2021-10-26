
from genericpath import exists
import threading
import time
import dateparser
from numpy.core.arrayprint import DatetimeFormat
import os
import time as tm
import datetime as dt # Use datetime only, NOT date. Every datetime is local datetime if it has no 'utc' tag.
import pytz
from binance.client import Client
import numpy as np
import pandas as pd
import requests
import json

from .Utility import *

import time
import win32api

from config import *
from Exchange.ExchangeFactory import *

from ThreadOnTimeMachine import *


class Channel(ThreadOnTimeMachine):

    def __init__(self, channelParams, timingParams):
        ThreadOnTimeMachine.__init__(self, channelParams, timingParams)
        self._step_run = -1
        self._running = False

        self.exchange = None
        self.today_frame = None
        self.today_path = None

    def __setInstance__(self, channelParams, timingParams):
        ThreadOnTimeMachine.__setInstance__(self, channelParams, timingParams)
        self.name = channelParams['Channel']
        [self.dataType, self.symbol, self.interval] = channelParams['Channel'].split('.')
        self.exchange = ExchangeFactory.CreateExchange(channelParams['Exchange'])

        return

    def SingleStep(self, stepId):
        if self._step_run < stepId:
            ThreadOnTimeMachine.SingleStep(self, stepId)
            #print('Indicator - {}: step {}, currInterval {}'.format(self.name, stepId, self.currentInterval))
            self._step_run = stepId

        return
  
    def Start(self):
        if self._running is False:
            Binance._singleton.Initial_Sync_Stream(self.dataTypes, self.symbols, self.intervals)
            ThreadOnTimeMachine.Start(self)
            self._running = True

    def Stop(self):
        if self._running is True:
            ThreadOnTimeMachine.Stop(self)
            self._running = False


    def Download_Data(dataType, symbol, interval, start, end):
        """
        There is now performance requirements, as is the case for Download_Data.
        """
        paths = []
        # Over 5GB of data per monthly file. Perforamance degradation when traversing between them.
        # self.Download_Monthly_Data(dataTypes, symbols, intervals, start, end, folder, checksum=0)
        #start2 = end.replace(day=1)

        start2 = start
        paths += Download_Daily_Data(dataType, symbol, interval, start2, end )

        return paths

    def Download_Monthly_Data(dataType, symbol, interval, start, end):
        """
        start:  local datetime
        end:    local datetime, or None representing now.
        """
        
        start_utc = from_dt_local_to_dt_utc(start)
        if end is None: end = dt.datetime.now()
        end_utc = from_dt_local_to_dt_utc(end)

        start_utc = datetime( start_utc.year, start_utc.month, 1 ) - dt.timedelta(days=1)
        end_utc = datetime( end_utc.year, end_utc.month + 1, 1 )

        paths_list = []
        for year in range( start_utc.year, end_utc.year + 1):
            for month in range(1, 13):
                current_utc = datetime(year, month, 2) # 2 not 1.
                if start_utc <= current_utc and current_utc <= end_utc:
                    path = download_file(current_utc, dataType, symbol, interval)
                    paths_list.append(path)

        return paths_list


    def Download_Daily_Data(dataType, symbol, interval, start, end):

        start_utc = from_dt_local_to_dt_utc(start)
        if end is None: end = dt.datetime.now()
        end_utc = from_dt_local_to_dt_utc(end)

        start_utc = datetime( start_utc.year, start_utc.month, start_utc.day ) - dt.timedelta(hours=1)
        end_utc = datetime( end_utc.year, end_utc.month, end_utc.day ) + dt.timedelta(hours=1)

        paths_list = []
        for days in range( (end_utc-start_utc).days + 2 ):  
            current_utc = datetime(start_utc.year, start_utc.month, start_utc.day) + dt.timedelta(days=days)
            if start_utc <= current_utc and current_utc <= end_utc:
                path = download_file(current_utc, dataType, symbol, interval)
                paths_list.append(path)

        return paths_list



    def Initial_Sync_Stream(client, dataType, symbol, interval, channel):
        """
        This is called on a program launch, NOT a date change.
        There is now performance requirements, as is the case for Download_Data.
        """
        
        today = dt.datetime.now()
        yesterday = today - dt.timedelta(days=1)

        # To make sure to have yesterday's data if called on start.
        paths_yeday = Download_Data(channel, yesterday, yesterday)
        lastId_yeday = get_lastId(paths_yeday)

        # If there is no today file, create one with '_' name prefix. Fill in the file up to 'now'. Create a dataframe from the file.
        (dataframe, filepath) = initial_sync_today_file(client, dataType, symbol, interval, lastId_yeday)
        return (dataframe, filepath)

    def Sync_Stream_Present_Tense(self):
        (self.today_frame, self.today_path, _) = extend_frontier_today_file(self.exchange.client, self.dataType, self.symbol, self.interval, self.today_frame, self.today_path)
        return

    def get_lastId(self, paths): # This function knows some of the file structure.
        lastId = None
        path = paths[-1]
        if path is not None and os.path.exists(path):
            dataframe = read_csv_file(self.dataType, path) # pd.read_csv(path, header=None, index_col=None)
            if dataframe.shape[0] > 0 and dataframe.shape[1] > 0:
                lastId = dataframe.loc[dataframe.shape[0]-1, 0] # dataframe.loc[dataframe.shape[0]-1][0]
            del dataframe
        
        return lastId

