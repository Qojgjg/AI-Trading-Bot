
from genericpath import exists
import threading, multiprocessing
from typing import Tuple
import dateparser
import os
import copy
import time as tm
import datetime as dt # Use datetime only, NOT date. Every datetime is local datetime if it has no 'utc' tag.
import pytz
from binance.client import Client
import numpy as np
import pandas as pd
import requests
import json
from enum import Enum
import asyncio
from awaits.awaitable import awaitable

from unicorn_binance_websocket_api.unicorn_binance_websocket_api_manager import BinanceWebSocketApiManager as UnicornSockets
import logging


from .Utility import *

import win32api

from ..config import *
from ..Exchange.Exchange import *

from ..ThreadOnTimeMachine import *

class ClientPool():

    def __init__(self, total):
        self.total = total
        self.clients = []
        self.clientIdUsed = 0
        self.lock = threading.Lock()
        for n in range(total): self.clients.append( Client() )

    def Next(self):
        self.clientIdUsed = 0 if self.clientIdUsed >= len(self.clients) - 1 else self.clientIdUsed + 1
        return self.clients[self.clientIdUsed]

    def Repair(self, client):
        if client in self.clients:
            idx = self.clients.index(client)
        else: idx = self.clientIdUsed
        del self.clients[idx]
        self.clients[idx] = Client()
        return

class T_State():
    none = 0
    in_sync = 1
    syncing = 2
    granular = 4
    no_missing = 8

class Binance(Exchange):

    _singleton = None
    _step_run = 0
    _running = False

    client = None   
    clientPool = None
    unicorn_sockets_manager = None
    gstream_transceiver_thread = None
    gstream_integrator_thread = None

    stop_flag_Maintain_GStreams = None
    stop_GStream_Transceiver_Thread_Function = None
    stop_GStream_Integrator_Thread_Function = None

    gstreams = {}
    lock_gstream = None
    gstreams_ready = False
    granualar_gstreams_ready = False
    gstream_datetime = None # local time.
    gstream_lag_sec = 0
    unicorn_sockets_manager = None #UnicornSockets(exchange="binance.com") # took 4 weeks to remove '-futures', till July 14.

    add_to_plot = None


    def __init__(self):
        raise RuntimeError('Call instance() instead')

    @classmethod
    def instantiate(cls, exchangeParams = None):
        if cls._singleton is None:

            Binance.Initialize()
            cls.lock_gstream = threading.Lock()
           
            cls._singleton = cls.__new__(cls)
            client = Client(Config['api_key'], Config['api_secret']) #, tld = 'us', testnet = False)
            #client.API_URL = 'https://testnet.binance.vision/api'
            #client = Client()
            cls.client = client #, tld = 'us', testnet = False)

            travel_lag_mili = 150 # Specific to my location. Experimental.
            # This value is chosen so that the following evalustes to be the equal negative value.
            #self.GetExchangeTimeMili() - (datetime.utcnow().replace(tzinfo = pytz.utc)-datetime.utcfromtimestamp(0)).total_seconds() * 1000
            #(datetime.utcnow().replace(tzinfo = pytz.utc)-datetime.utcfromtimestamp(0)).total_seconds() * 1000 - self.GetExchangeTimeMili()

            server_time = client.get_server_time()
            milisec_since_epoch = server_time["serverTime"] + travel_lag_mili
            gmtime=tm.gmtime(milisec_since_epoch/1000.0)
            mili= round(milisec_since_epoch) % 1000
            win32api.SetSystemTime(gmtime[0], gmtime[1], gmtime[6], gmtime[2], gmtime[3], gmtime[4], gmtime[5], mili) # Needed Administrator Permission

            Binance.clientPool = ClientPool(30)
            #Binance.clientPool.clients[0] = client
         
        return cls._singleton


    @classmethod
    def Initialize(cls):
        cls._singleton = None
        cls._step_run = 0
        cls._running = False

        cls.client = None   
        cls.clientPool = None
        cls.unicorn_sockets_manager = None
        cls.gstream_transceiver_thread = None
        cls.gstream_integrator_thread = None

        cls.stop_flag_Maintain_GStreams = None
        cls.stop_GStream_Transceiver_Thread_Function = None
        cls.stop_GStream_Integrator_Thread_Function = None

        cls.gstreams = {}
        cls.lock_gstream = None
        cls.gstreams_ready = False
        cls.granualar_gstreams_ready = False
        cls.gstream_datetime = None # local time.
        cls.gstream_lag_sec = 0
        cls.unicorn_sockets_manager = None #UnicornSockets(exchange="binance.com") # took 4 weeks to remove '-futures', till July 14.
        cls.integrator_heartbeat = None

        cls.add_to_plot = None

        return


    async def Stop_Maintain_GStreams(self):
        signaled = None
        if Binance.stop_flag_Maintain_GStreams is not None:
            Binance.stop_flag_Maintain_GStreams = True
            signaled = True
        else:
            signaled = False

        return signaled

    async def Maintain_GStreams(self):
        # The order in which the these two are called is a know-how.
        await self.Start_GStreams_Integrator(restore = False)
        await self.Start_GStreams_Transceiver(restore = False)

        Binance.stop_flag_Maintain_GStreams = False

        try:
            while True:
                await asyncio.sleep(3)

                if Binance.stop_flag_Maintain_GStreams is None:
                    pass
                elif not Binance.stop_flag_Maintain_GStreams:
                    if Binance.gstream_lag_sec < 3 and dt.datetime.timestamp(dt.datetime.now()) - Binance.integrator_heartbeat > 60:
                    #if Binance.gstream_integrator_thread is not None and Binance.gstream_integrator_thread._is_stopped:
                        print('Re-Starting GStreams Integrator ------------------------------------------------------------------- ')
                        await self.Start_GStreams_Integrator(restore = True)

                    if dt.datetime.timestamp(dt.datetime.now()) - Binance.transceiver_heartbeat > 3:
                    #if Binance.gstream_transceiver_thread is not None and Binance.gstream_transceiver_thread._is_stopped:
                        print('Re-Starting GStreams Transceiver ------------------------------------------------------------------- ')
                        await self.Start_GStreams_Transceiver(restore = True)
                elif Binance.stop_flag_Maintain_GStreams:
                    if Binance.stop_GStream_Transceiver_Thread_Function is not None:
                        Binance.stop_GStream_Transceiver_Thread_Function = True
                        Binance.gstream_transceiver_thread.join()
                        print('gstream_transceiver_thread joined.')

                    if Binance.stop_GStream_Integrator_Thread_Function is not None:
                        Binance.stop_GStream_Integrator_Thread_Function = True
                        Binance.gstream_integrator_thread.join()
                        print('gstream_integrator_thread joined.')

                    break
        except Exception as e:
            print('Maintain_GStreams() with exception.')
            sys.exit(1) # This thread will be relaunched later.


        # Do NOT sys.exit(0), as join() is waiting.
        print('Maintain_GStreams() stopped.')

        return


    async def Start_GStreams_Transceiver(self, restore = False):

        if Binance.unicorn_sockets_manager is not None: del Binance.unicorn_sockets_manager
        Binance.unicorn_sockets_manager = UnicornSockets(exchange="binance.com") # took 4 weeks to remove '-futures', till July 14.

        Binance.gstream_transceiver_thread = threading.Thread(target=self.GStream_Transceiver_Thread_Function, args=())
        Binance.gstream_transceiver_thread.start()

        await self.Dynamize_Static_GStreams_v2( granular = True, restore = restore )
        await self.Dynamize_Static_GStreams_v2( granular = False, restore = restore )

        return


    def GStream_Transceiver_Thread_Function(self):
        # Design requirements: Make it light. Don't let it halt on io.
        Binance.stop_GStream_Transceiver_Thread_Function = False
        sleepSec = 0.001

        try:

            while True:
                Binance.transceiver_heartbeat = dt.datetime.timestamp(dt.datetime.now())

                nSleepSec = 0
                if Binance.stop_GStream_Transceiver_Thread_Function is None:
                    pass
                elif not Binance.stop_GStream_Transceiver_Thread_Function:
                    if Binance.unicorn_sockets_manager.is_manager_stopping(): 
                        print('Unicorn Manage is stopping. GStream_Thread_Function is quiting...')
                        # sys.exit(0) Do NOT exit. Join() is waiting for this normal quiting.
                    oldest_data = Binance.unicorn_sockets_manager.pop_stream_data_from_stream_buffer()
                    if oldest_data is False:
                        time.sleep(sleepSec) #============= Expensive OS switching.!!!!!!!!!! so frequent.
                        nSleepSec += sleepSec
                    else:
                        data_consumed = self.Dispatch_Streaming_Data(oldest_data)
                        # time.sleep(0.01) # Yield chance to others.
                        if not data_consumed:
                            # logging
                            #Binance.unicorn_sockets_manager.delete_stream_from_stream_list(stream_id) # How to find stream_id?
                            pass
                else:
                    Binance.unicorn_sockets_manager.stop_manager_with_all_streams()
                    break

                if nSleepSec <= 0: tm.sleep(sleepSec) # This requires OS thread switching, which is resource-exspensive. Try await.

            # Do NOT sys.exit(), as join() is waiting.
            return

        except Exception as e:
            Binance.gstream_transceiver_thread._is_stopped = True
            sys.exit(1) # This thread will be relaunched later.


    async def Start_GStreams_Integrator(self, restore = False):
        Binance.gstream_integrator_thread = threading.Thread(target=self.GStream_Integrator_Thread_Function, args=())
        Binance.gstream_integrator_thread.start()


    def GStream_Integrator_Thread_Function(self):
        # Design requirements: Make it light. Don't let it halt on io.
        Binance.stop_GStream_Integrator_Thread_Function = False
        nGS_With_Missings = 0

        try:
            while True:
                Binance.integrator_heartbeat = dt.datetime.timestamp(dt.datetime.now())

                if Binance.stop_GStream_Integrator_Thread_Function is None:
                    pass
                elif not Binance.stop_GStream_Integrator_Thread_Function: # not Binance.stop_GStream_Integrator_Thread_Function:
                    #if not Binance.gstreams_ready:
                    counter = 0
                    with Binance.lock_gstream: copy_gstreams = Binance.gstreams.copy()

                    for key, (lock, t_dataframe, t_filepath, stream_id, tickbuffer, t_state) in copy_gstreams.items():
                        (dataType, symbol, interval) = key.split('.')
                        counter += 1
                        binance_wait_sec = 0 # if counter < 180 else 1 if counter < 200 else Config['binance_wait_sec']

                        if Binance.gstream_lag_sec < 2.0 or not bool(t_state & T_State.no_missing):
                            no_missing, held_on_io = fill_in_missing_slots(lock, self.clientPool, binance_wait_sec, dataType, symbol, interval, t_dataframe)
                            if Binance.gstreams.get( key, None) is not None:
                                if no_missing and not bool(t_state & T_State.no_missing):
                                    Binance.gstreams[key][5] = t_state | T_State.no_missing
                                elif not no_missing:
                                    Binance.gstreams[key][5] = t_state & ~T_State.no_missing
                                    nGS_With_Missings += 1

                        # with Binance.lock_gstream: Degrades performance too much.
                        #with Binance.lock_gstream:
                        #    if Binance.gstreams.get(key, None) is not None:
                        #        Binance.gstreams[key] = [lock, t_dataframe, t_filepath, stream_id, tickbuffer, t_state]

                        #============= This is VERY important design decision to yield time resources to Transceiver thread. Transceiver would increasingly lag behind the stream.
                        if held_on_io: # Thread has already yield to others.
                            pass
                        else:
                            tm.sleep(0.3 + 0.1 * Binance.gstream_lag_sec)

                        if Binance.stop_GStream_Integrator_Thread_Function:
                            break # For responsiveness.

                    if nGS_With_Missings <= 0:
                        print('----------------------------------------------------------------------------------- GStreams Ready --------\n')
                        Binance.gstreams_ready = True
                        Binance.granualar_gstreams_ready = True
                    else:
                        Binance.gstreams_ready = False
                        Binance.granualar_gstreams_ready = False

                    nGS_With_Missings = 0

                elif Binance.stop_GStream_Integrator_Thread_Function:
                    break

                if Binance.gstreams_ready or Binance.granualar_gstreams_ready: 
                    tm.sleep(10 + 0.1 * Binance.gstream_lag_sec)
           
            # Do NOT sys.exit(), as join() is waiting.
            return

        except Exception as e:
            Binance.gstream_integrator_thread._is_stopped = True
            sys.exit(1) # This thread will be relaunched later.



    async def Dynamize_Static_GStreams_v2(self, granular = True, restore = False):

        with Binance.lock_gstream:
            Binance.gstreams = { key: value for (key, value) in sorted( Binance.gstreams.items(), key=lambda x: x[1][5] & T_State.granular, reverse=True) }

        slot_groups =[]
        with Binance.lock_gstream: # Fast enough is this block.
            for key, (_, _, _, _, _, t_state) in Binance.gstreams.items():
                if ( bool(t_state & T_State.granular) == granular ) and ( not ( restore or t_state & (T_State.in_sync | T_State.syncing) ) or restore ) :
                    [dataType, symbol, interval] = key.split('.')
                    market, channel = Binance.Unicorn_Market_Channle(dataType, symbol, interval)

                    group_shared = False
                    for slot_group in slot_groups:
                        channels = slot_group['channels']
                        markets = slot_group['markets']
                        if len(channels) * len(markets) < Config['max_slots_per_stream']:
                            if len(channels) == 1 and channels[0] == channel:
                                markets.append(market)
                                group_shared = True
                            elif len(markets) == 1 and markets[0] == market:
                                channels.append[channel]
                                group_shared = True
                        if group_shared: break
                        
                    if not group_shared:
                        group = {'channels': [channel], 'markets' : [market] }
                        slot_groups.append(group)       

        for group in slot_groups:
            tm.sleep(Config['binance_wait_sec'])
            stream_id = self.unicorn_sockets_manager.create_stream( group['channels'], group['markets'] )
            if stream_id is not None:
                with Binance.lock_gstream:
                    for channel in group['channels']:
                        for market in group['markets']:
                            dataType, symbol, interval = Binance.Unicorn_dataType_Symbol_Interval_From_Channel_Market(channel, market)
                            key = dataType + '.' + symbol + '.' + interval
                            if Binance.gstreams.get(key, None) is not None:
                                (lock, totay_dataframe, t_filepath, _, tickbuffer, t_state) = Binance.gstreams[key]
                                Binance.gstreams[key] = [lock, totay_dataframe, t_filepath, stream_id, tickbuffer, t_state]
            else:
                raise Exception('Failed in an attempt to create stream.')
        return


    def Dynamize_Single_GStream_v2(self, key):
        (lock, totay_dataframe, t_filepath, stream_id, tickbuffer, t_state) = Binance.gstreams[key]

        if stream_id is None:
            stream_id = self.Tap_Static_GStream_Into_Dynamic_Streams( key )
            if stream_id is not None and Binance.gstreams.get(key, None) is not None:
                Binance.gstreams[key] = [lock, totay_dataframe, t_filepath, stream_id, tickbuffer, t_state]
            else:
                raise Exception('Unable to tap a gstream to dynamic streams.')

        #while True:
        #    tm.sleep(0.1)
        #    (_, _, _, _, _, t_state) = Binance.gstreams[key]
        #    if t_state & T_State.in_sync: break

        return

    @classmethod
    def Start_Add_To_Plot(cls, add_to_plot):
        cls.add_to_plot = add_to_plot

    def GetExchangeTimeMili(cls):
        super().GetExchangeTimeMili()
        server_time = cls.client.get_server_time() # Miliseconds since epoch.
        miliseconds_from_epoch= round(server_time["serverTime"])

        return miliseconds_from_epoch


    def Download_Data(self, dataTypes, symbols, intervals, start, end):
        """
        There is now performance requirements, as is the case for Download_Data.
        """
        paths = {}
        # Over 5GB of data per monthly file. Perforamance degradation when traversing between them.
        # self.Download_Monthly_Data(dataTypes, symbols, intervals, start, end, folder, checksum=0)
        #start2 = end.replace(day=1)

        start2 = start
        paths = self.Download_Daily_Data(dataTypes, symbols, intervals, start2, end )

        return paths

    def Download_Monthly_Data(self, dataTypes, symbols, intervals, start, end):
        """
        start:  local datetime
        end:    local datetime, or None representing now.
        """
        
        start_utc = from_dt_local_to_dt_utc(start)
        if end is None: end = dt.datetime.now()
        end_utc = from_dt_local_to_dt_utc(end)

        start_utc = dt.datetime( start_utc.year, start_utc.month, 1 ) - dt.timedelta(days=1)
        end_utc = dt.datetime( end_utc.year, end_utc.month + 1, 1 )

        paths = {}
        symbolcounter = 0
        for dataType in dataTypes:
            for symbol in symbols:
                print("[{}/{}] - start download monthly {} {}.".format(symbolcounter+1, len(symbols), symbol, dataType))
                for interval in intervals:
                    paths_list = []
                    for year in range( start_utc.year, end_utc.year + 1):
                        for month in range(1, 13):
                            current_utc = dt.datetime(year, month, 2) # 2 not 1.
                            if start_utc <= current_utc and current_utc <= end_utc:
                                path = download_file(current_utc, dataType, symbol, interval)
                                paths_list.append(path)
                    paths[dataType+'.'+symbol+'.'+interval] = paths_list       
                symbolcounter += 1

        return paths


    def Download_Daily_Data(self, dataTypes, symbols, intervals, start, end):

        start_utc = from_dt_local_to_dt_utc(start)
        if end is None: end = dt.datetime.now()
        end_utc = from_dt_local_to_dt_utc(end)

        start_utc = dt.datetime( start_utc.year, start_utc.month, start_utc.day ) - dt.timedelta(hours=1)
        end_utc = dt.datetime( end_utc.year, end_utc.month, end_utc.day ) + dt.timedelta(hours=1)

        paths = {}
        symbolcounter = 0
        for dataType in dataTypes:
            for symbol in symbols:
                print("[{}/{}] - start download daily {} {}.".format(symbolcounter+1, len(symbols), symbol, dataType))
                for interval in intervals:
                    paths_list = []
                    for days in range( (end_utc-start_utc).days + 2 ):  
                        current_utc = dt.datetime(start_utc.year, start_utc.month, start_utc.day) + dt.timedelta(days=days)
                        if start_utc <= current_utc and current_utc <= end_utc:
                            path = download_file(current_utc, dataType, symbol, interval)
                            paths_list.append(path)
                    paths[dataType+'.'+symbol+'.'+interval] = paths_list  
                symbolcounter += 1

        return paths


    def Add_GStream(self, dataType, symbol, interval, granular = False):
        symbol = str.upper(symbol)
        interval = str.lower(interval)

        ret = None

        key = dataType + '.' + symbol + '.' + interval
        if Binance.gstreams.get(key, None) is None:

            gstream = self.Create_Static_GStream_v2(dataType, symbol, interval, granular=granular)
    
            if gstream is not None:

                with Binance.lock_gstream:
                    Binance.gstreams[key] = gstream

                (lock, t_dataframe, t_filepath, stream_id, tickbuffer, t_state ) = gstream

                if Binance._running:

                    self.Dynamize_Single_GStream_v2(self, key)

                ret = key

            else:
                print('Failed in an attempt to create a stream: {}, {}, {}'.format(dataType, symbol, interval))
                ret = None
        else:
            # Give a chance to change granularity.
            (lock, t_dataframe, t_filepath, stream_id, tickbuffer, t_state) = Binance.gstreams[key]
            Binance.gstreams[key] = [lock, t_dataframe, t_filepath, stream_id, tickbuffer, t_state | (T_State.granular if granular else T_State.none) ]
            ret = key

        return ret


    def Create_Static_GStream(self, dataType, symbol, interval, granular=False):
        
        today = dt.datetime.now()

        (dataframe, filepath) = load_nonempty_frame_file(self.clientPool, dataType, symbol, interval)

        if dataframe is None:

            yesterday = today - dt.timedelta(days=1)

            # Not guranteed to download even if yesterday is yesterday. Yesterday data is not available soon. 2 hours?
            paths_yeday = self.Download_Data([dataType], [symbol], [interval], yesterday, yesterday)

            lastId = None 
            if len(paths_yeday) == 1:
                lastIds = get_lastIds(paths_yeday)
                lastId = list(lastIds.values())[0]
            
            # lastId = None #============================== fictitious.
            if lastId is None: 
                daybeforeyesterday = yesterday - dt.timedelta(days=1)
                paths_beyeday = self.Download_Data([dataType], [symbol], [interval], daybeforeyesterday, daybeforeyesterday)
                if len(paths_yeday) == 1:
                    lastIds = get_lastIds(paths_beyeday)
                    lastId = list(lastIds.values())[0]

                    if lastId is not None:
                        dt_utc = from_dt_local_to_dt_utc(yesterday)
                        lastId = create_full_day_data(self.clientPool, dataType, symbol, interval, lastId, dt_utc)

            if lastId is not None:
                # If there is no today file, create one with '_' name prefix. Fill in the file up to 'now'. Create a dataframe from the file.
                (dataframe, filepath) = create_nonempty_frame_file(self.clientPool, dataType, symbol, interval, lastId)


        tickbuffer, t_state = [], T_State.none | (T_State.granular if granular else T_State.none)

        if dataframe is not None and filepath is not None: 
            stream_id = None
            return [threading.Lock(), dataframe, filepath, stream_id, tickbuffer, t_state] #stream_str (eg, 'ethusdt@kline_1m')
        else:
            print('Failed in an attempt to create a stream: {}, {}, {}'.format(dataType, symbol, interval))
            return None


    def Create_Static_GStream_v2(self, dataType, symbol, interval, granular=False):
        
        dataframe, filepath = pd.DataFrame(), None
        stream_id, tickbuffer, t_state = None, [], T_State.none | (T_State.granular if granular else T_State.none)

        return [threading.Lock(), dataframe, filepath, stream_id, tickbuffer, t_state] #stream_str (eg, 'ethusdt@kline_1m')


    def Remove_GStream(self, dataType, symbol, interval):
        symbol = str.upper(symbol)
        interval = str.lower(interval)

        removed = False

        key = dataType + '.' + symbol + '.' + interval

        unsubscribed = True


        if Binance.gstreams.get(key, None) is not None:
            gstream = Binance.gstreams[key]
            (lock, t_dataframe, t_filepath, stream_id, tickbuffer, t_state ) = gstream

            if stream_id is not None:
                market, channel = Binance.Unicorn_Market_Channle(dataType, symbol, interval)

                stream_info = Binance.unicorn_sockets_manager.get_stream_info(stream_id)
                if stream_info['channels'] is not None and len(stream_info['channels']) == 1 and stream_info['channels'][0] == channel :
                    unsubscribed = Binance.unicorn_sockets_manager.unsubscribe_from_stream(stream_id, [], [market])
                elif stream_info['markets'] is not None and len(stream_info['market']) == 1 and stream_info['markets'][0] == market :
                    unsubscribed = Binance.unicorn_sockets_manager.unsubscribe_from_stream(stream_id, [channel], [])
        
        if unsubscribed:
            with Binance.lock_gstream:
                removed = self.Remove_Static_GStream( key )
        else:
            raise Exception('Failed in an attempt to  unsubscribe from stream.')       
 
        return removed


    def Remove_Static_STream(self, key):

        if Binance.gstreams.get(key, None) is not None:
            (lock, t_dataframe, t_filepath, stream_id, tickbuffer, t_state) = Binance.gstreams[key]
            if lock is not None: del lock
            if t_dataframe is not None: del t_dataframe
            if os.path.exists(t_filepath): os.remove(t_filepath)
            if tickbuffer is not None: del tickbuffer
            del Binance.gstreams[key]

        return True


    def Max_Grow_Static_GStream(self, key):
        (lock, t_dataframe, t_filepath, stream_id, tickbuffer, t_state ) = Binance.gstreams[key]
        [dataType, symbol, interval] = key.split('.')
        (totay_dataframe, t_filepath, _) = max_grow_frame_file(lock, self.clientPool, dataType, symbol, interval, t_dataframe, t_filepath)
        Binance.gstreams[key] = [lock, totay_dataframe, t_filepath, stream_id, tickbuffer, t_state] #stream_str (eg, 'ethusdt@kline_1m')

        return totay_dataframe


    def Launch_Max_Grow_Static_GStream(self, key):
        thread = threading.Thread(target = self.Max_Grow_Static_GStream, args=(key))
        thread.start()
        # Design decision D: Do NOT join(), and leave it open.
        # Design decision C: This function doesn't have to manage the state, thanks to Design decision B.
        print('Delagging thread launched.')

        return


    def Dispatch_Streaming_Data(self, data):
        # Design requirements: Make it light. Don't let it halt on io.
        
        if type(data) == str: data = json.loads(data)
        assert type(data) == dict

        data_dispatched = False
        stream_str = data.get('stream', None)
        if stream_str is not None:
            dataType, symbol, interval = Binance.Unicorn_dataType_Symbol_Interval(stream_str)
            key = dataType + '.' + symbol + '.' + interval

            if Binance.gstreams.get(key, None) is None:
                raise Exception('Inconsistency')
            else:
                data_dispatched = True
                data = data['data']

                eventtime = data['E']
                starttime_stream = data['k']['t']

                utcnow = dt.datetime.utcnow()

                #===================================================================================== Temporary to save time. 
                #closed = data['k']['x']
                #if not closed:
                #    print( data['s'].ljust(10),  data['k']['i'].zfill(3), utcnow.strftime('%H:%M:%S'), '{:4.0f}'.format((utcnow.replace(tzinfo=pytz.utc)-Config['start_time_utc']).total_seconds()/60), str(int((utcnow - dt.datetime.utcfromtimestamp(eventtime/1000)).total_seconds())).zfill(3), dt.datetime.utcfromtimestamp(starttime_stream/1000).strftime('%M:%S'), dt.datetime.utcfromtimestamp(eventtime/1000).strftime('%M:%S') )
                #    return data_dispatched
                #======================================================================================

                (lock, t_dataframe, t_filepath, stream_id, tickbuffer, t_state) = Binance.gstreams[key]

                #=============================================================================================================
                granular = t_state & T_State.granular
                no_missing = t_state & T_State.no_missing
                Binance.gstream_lag_sec = (dt.datetime.utcnow() - dt.datetime.utcfromtimestamp(eventtime/1000)).total_seconds()
                print( data['s'].ljust(10),  data['k']['i'].zfill(3), '\tintrgral' if no_missing else '\t        ', utcnow.strftime('%H:%M:%S'), '{:4.0f}'.format((utcnow.replace(tzinfo=pytz.utc)-Config['start_time_utc']).total_seconds()/60), str(round(Binance.gstream_lag_sec)).zfill(3), dt.datetime.utcfromtimestamp(starttime_stream/1000).strftime('%M:%S'), dt.datetime.utcfromtimestamp(eventtime/1000).strftime('%M:%S'), '-g-' if granular else '' )
                #=============================================================================================================

                update_report, Binance.gstream_datetime, ts_mili, price = \
                    update_with_stream_data_v2(lock, dataType, symbol, interval, t_dataframe, t_filepath, tickbuffer, data, granular = t_state & T_State.granular)
                # Design decision A: I intentionally drop gstreamspath here. It would stop this streaming thread long to update the file.
                # Design decision B: It makes attempt to update_with_stream_date no matter what the state is. This frees other functions from having to manage the state.

                if Binance.add_to_plot is not None and ts_mili is not None and price is not None:
                    Binance.add_to_plot(symbol, ts_mili, price)

                launching_frame_delagging_required = None

                if update_report == 'success':
                    if t_state & T_State.syncing:
                        t_state = t_state & ~T_State.syncing
                        print("State: syncing -> in_sync !!!")
                    else:
                        if t_state & T_State.in_sync:
                            pass
                        else:
                            print("State: out_sync -> in_sync !!!")

                    t_state = t_state | T_State.in_sync # Perfectly availeble to data consumers.
                    launching_frame_delagging_required = False

                elif update_report == 'frame_lagging':

                    if t_state & T_State.syncing: # frame_delagging has already been lanuched and in progress.
                        print("State: syncing -> syncing ...")
                    else:
                        if t_state & T_State.in_sync:
                            t_state = t_state & ~T_State.in_sync
                            print("State: in_sync -> syncing ...")
                        else:
                            print("State: out_sync -> syncing ...")

                        t_state = t_state | T_State.syncing # Change state.
                        launching_frame_delagging_required = True

                elif update_report == 'frame_empty':
                    if t_state & T_State.in_sync:
                        t_state = t_state & ~T_State.in_sync
                        print ("State: in_sync -> empty ???")
                    else:
                        print ("frame still empty.")
                    
                else:
                    pass
                
                Binance.gstreams[key][5] = t_state # = [lock, t_dataframe, t_filepath, stream_id, tickbuffer, t_state]

                #TODO. Temporarilly commented out.
                #if launching_frame_delagging_required: #=====================================================================
                #    self.Launch_Max_Grow_Static_GStream(key) # This will take care of t_state

        else: # this is a control signal.
            pass
        
        return data_dispatched


    @staticmethod
    def Unicorn_Market_Channle(dataType, symbol, interval):
        market = str.lower(symbol)
        if dataType == 'klines': 
            channel = 'kline_' + interval
        elif dataType == 'aggTrades':
            channel = 'aggTrade'
        else:
            raise Exception('Unhandled data type: {}'.format(dataType))
        
        return market, channel

    @staticmethod
    def Unicorn_dataType_Symbol_Interval_From_Channel_Market(channel, market):
        symbol = str.upper(market)
        if '_' in channel:
            [dataType, interval] = channel.split('_')
            if dataType == 'kline': dataType = 'klines'
        elif channel == 'aggTrades':
            dataType = 'aggTrade'
            interval = None
        else:
            raise Exception('Unhandled channel: {}'.format(channel))
        
        return dataType, symbol, interval

    @staticmethod
    def Unicorn_dataType_Symbol_Interval(stream_str):
        dataType, symbol, interval = None, None, None

        [market, channel] = stream_str.split('@')
        symbol = str.upper(market)
        if '_' in channel: [dataType, interval] = channel.split('_')
        else: dataType = channel

        if dataType == 'kline': dataType = 'klines'
        
        return dataType, symbol, interval


    def Tap_Static_GStream_Into_Dynamic_Streams(self, key):
        #(lock, t_dataframe, t_filepath, stream_id, tickbuffer, t_state ) = Binance.gstreams[key]
        [dataType, symbol, interval] = key.split('.')
        market, channel = Binance.Unicorn_Market_Channle(dataType, symbol, interval)

        stream_id = None

        stream_shared = False

        # Unicorn, and Binance, creates and allocates one additional thread to each newly created stream.
        # In order to reduce the total number of threads and the overhead of switching between threads, I choose to reuse streams as much as possible.
        # There will be hundreds of markets with the same single channel, for example.

        with Binance.lock_gstream: # Fast enough, exept the maximum single call to subscrive_to_stream().
            for key, (lock, t_dataframe, t_filepath, stream_id, tickbuffer, t_state) in Binance.gstreams.items():
                if stream_id is not None:
                    stream_info = Binance.unicorn_sockets_manager.get_stream_info(stream_id)
                    if stream_info['channels'] is not None and stream_info['markets'] is not None:
                        if len(stream_info['channels']) * len(stream_info['markets']) < Config['max_slots_per_stream']: #== Let a stream accommodate max 20 (market, channel)s.
                            if len(stream_info['channels']) == 1 and stream_info['channels'][0] == channel :
                                stream_shared = Binance.unicorn_sockets_manager.subscribe_to_stream(stream_id, [], [market])
                            elif len(stream_info['market']) == 1 and stream_info['markets'][0] == market :
                                stream_shared = Binance.unicorn_sockets_manager.subscribe_to_stream(stream_id, [channel], [])
                            if stream_shared: break
        
        if not stream_shared or stream_id is None:
            stream_id = Binance.unicorn_sockets_manager.create_stream( channel, market ) # Do not give stream_buffer_name, which defaults to False.

        return stream_id


    def Get_Recent_Prices(self, dataType, symbol, interval, nRows):
        end = Binance.gstream_datetime
        ts_end = round(dt.datetime.timestamp(end) * 1000)
        ts_start = ts_end - intervalToMilliseconds(interval) * ( nRows - 1 )
        start = dt.datetime.fromtimestamp(ts_start/1000)
        end = end + dt.timedelta(seconds=1)
        dataframe = self.Get_Filed_Data_By_Time(dataType, symbol, interval, start, end)

        return dataframe


    def Get_Filed_Data_By_Time(self, dataType, symbol, interval, start, end ): # read [start, end) NOT INCLUSIVE.

        dataframe = pd.DataFrame()

        #========== 1. Get data from historic files -----  Read (-infinity, today_start_utc) intersection [start_utc, end_utc), if not empty.

        if start > dt.datetime.now(): return None
        start_utc = from_dt_local_to_dt_utc(start)      

        if end is None: end = Binance.gstream_datetime + dt.timedelta(seconds=1)
        end_utc = from_dt_local_to_dt_utc(end)
        today_start_utc = get_current_day_start(dt.datetime.utcnow())
        today_start_utc = today_start_utc.replace(tzinfo=pytz.utc)

        if not start_utc < end_utc: return None

        sample_utc = start_utc

        while sample_utc < today_start_utc:
            from_utc = max( get_current_day_start(sample_utc), start_utc )
            to_utc = min( get_next_day_start(sample_utc), end_utc)
            if  not from_utc < to_utc: break
            # Thus, [from_utc, to_utc) = [ get_current_day_start(sample_utc), get_next_day_start(sample_utc) ) intersection [start_utc, end_utc)
            df = select_from_single_historic_file_by_time(self.clientPool, Config['binance_wait_sec'], sample_utc, dataType, symbol, interval, from_utc, to_utc) # read [from_utc, to_utc)
            if df is not None: 
                dataframe = dataframe.append(df)
                dataframe = dataframe.reset_index(drop=True)
            sample_utc += dt.timedelta(days=1)

            today_start_utc = get_current_day_start(dt.datetime.utcnow().replace(tzinfo = pytz.utc))


        #========== 2. Get data from the today dataframe ----- Read [today_start_utc, max_available_from_today_file] intersection [start_utx, end_utc)

        key = dataType+'.'+symbol+'.'+interval
        if Binance.gstreams.get(key, None) is None: 
            return None # ----------------------------------------------- Create an entry to streams.
        else: 
            (lock, t_dataframe, _, _, _, _) = Binance.gstreams[key]

        from_utc = max(today_start_utc, start_utc)
        to_utc = end_utc
        if from_utc < to_utc:
            df = select_from_dataframe_by_time(dataType, t_dataframe, from_utc, to_utc, lock = lock) # read [from_utc, to_utc)
            if df is not None: 
                dataframe = dataframe.append(df)
                dataframe = dataframe.reset_index(drop=True)

        interva_mili = intervalToMilliseconds(interval)
        start_mili= round(dt.datetime.timestamp(start_utc)*1000)
        end_mili= round(dt.datetime.timestamp(end_utc)*1000)
        nRowsExpected= round(end_mili / interva_mili) - int(start_mili / interva_mili)
        if start_mili % interva_mili > 0 : nRowsExpected -= 1
        if end_mili % interva_mili > 0 : nRowsExpected += 1

        tolerance = 2 # tolerance is sometimes required because of the lagging of streaming.

        # TODO
        print('------------- {} rows: {} / {}'.format(symbol, dataframe.shape[0], nRowsExpected))
        
        if dataframe.shape[0] < nRowsExpected - tolerance:
            print('Number of rows inconsistent.-------------------------------------- !!!')       
 
        return dataframe


    def Get_Filed_Data_By_Id(self, lock, dataType, symbol, interval, start_id, end_id):

        start_utc = get_utctime_by_id(self.client, dataType, symbol, interval, start_id)
        end_utc = get_utctime_by_id(self.client, dataType, symbol, interval, end_id)

        return self.Get_Filed_Data_By_Time( dataType, symbol, interval, start_utc, end_utc )


    def Get_Beyond_Filed_Data_By_Id(self, dataType, symbol, interval, start_id, end_id):
        pass


    def FindFromCache(self):
        return


    def Place_Order(self):
        return


    def GetUpdateData(self, kline):
        Time = kline[0] # time.strftime("%a, %d %b %Y %H:%M:%S", time.gmtime(kline[0]/1000))
        Open = kline[1]
        High = kline[2]
        Low = kline[3]
        Close = kline[4]
        Volume = kline[5]
        Close_time = kline[6] # time.strftime("%a, %d %b %Y %H:%M:%S", time.localtime(kline[6]/1000))
        Quote_asset_volume = kline[7]
        Number_of_trades = kline[8]  
        Taker_buy_base_asset_volume = kline[9] 
        Taker_buy_quote_asset_volume = kline[10] 
        return Time,Open,High,Low,Close,Volume,Close_time,Quote_asset_volume,Number_of_trades,Taker_buy_base_asset_volume,Taker_buy_quote_asset_volume


    def Get_Historical_Data(self, dataType, symbol, interval, start_str, end_str=None):
        #See dateparse docs for valid start and end string formats http://dateparser.readthedocs.io/en/latest/
        #If using offset strings for dates add "UTC" to date string e.g. "now UTC", "11 hours ago UTC"

        output_data = []

        # setup the max limit
        limit = 500

        timeframe = self.IntervalToMilliseconds(interval)

        start_ts_inclusive = self.TimeStrToMiliseconds(start_str)
        # if an end time was passed convert it
        end_ts_inclusive = None
        if end_str:
            end_ts_inclusive = self.TimeStrToMiliseconds(end_str) - 1 # -1 because this argument is inclusive.

        idx = 0
        start_ts = start_ts_inclusive
        # it can be difficult to know when a symbol was listed on Binance so allow start time to be before list date
        symbol_existed = False
        while True:
            # fetch the klines from start_ts up to max 500 entries or the end_ts if set

            timeSlot = None

            if dataType == 'klines':
                temp_data = self.client.get_klines(
                    symbol=symbol,
                    interval=interval,
                    limit=limit,
                    startTime=start_ts,
                    endTime=end_ts_inclusive
                )
                timeSlot = 0

            elif dataType == 'aggTrades':
                endTime_temp = min( start_ts + 59 * 60 * 1000, end_ts_inclusive) # The difference between start and end should be less than 1 hour.
                temps = self.client.get_aggregate_trades(
                    symbol=symbol,
                    fromId=245820273,
                    startTime=None, #start_ts,
                    endTime=None, #endTime_temp,
                    limit=limit,
                )
                temp_data = []
                for dic in temps:
                    temp_data.append( [ value for _, value in dic.items() ] )

                timeSlot = 5

            else:
                assert False

            # handle the case where our start date is before the symbol pair listed on Binance
            if not symbol_existed and len(temp_data) > 0:
                symbol_existed = True

            if symbol_existed:
                # append this loops data to our output data
                output_data += temp_data

                # update our start timestamp using the last value in the array and add the interval timeframe
                start_ts = temp_data[-1][timeSlot] + timeframe
            else:
                # it wasn't listed yet, increment our start date
                start_ts += timeframe

            idx += 1
            # check if we received less than the required limit and exit the loop
            if len(temp_data) < limit:
                # exit the while loop
                break

            # sleep after every 3rd call to be kind to the API
            time.sleep(Config['binance_wait_sec'])

        return output_data

    def _get_previous_month_last_day(self, dt):
        return dt.replace(day=1) + dt.timedelta(days=-1)
    def _get_next_month_last_day(self, dt):
        return ((dt.replace(day=1) + dt.timedelta(days=32)).replace(day=1) + dt.timedelta(days=32)).replace(day=1) + dt.timedelta(-1)
    def _get_previous_day(self, dt):
        return dt + dt.timedelta(days=-1)
    def _get_next_day(self, dt):
        return dt + dt.timedelta(days=1)


    def DownloadData(self, start, end = dt.datetime.now(), dataType = 'klines', fileUnit = 'monthly', symbols = 'ETH/USDT', interval = '1m'):

        start = datetime( start.year, start.month, 1 if fileUnit == 'monthly' else start.day )
        end = datetime( end.year, end.month if (fileUnit == 'daily') or (end.day == 1) else end.month + 1, end.day if (fileUnit == 'daily') or (end.day == 1) else 1 )


        for symbol in symbols:

            _end = start #start = get_previous_month_last_day(start).replace(day=1) if fileUnit == 'monthly' else get_previous_day(start)
            _pre_end = self._get_previous_month_last_day(end).replace(day=1) if fileUnit == 'monthly' else self._get_previous_day(end)

            while _end <= _pre_end:
                _start = _end #get_next_month_last_day(_start).replace(day=1) if fileUnit == 'monthly' else get_next_day(_start)
                _end = self._get_next_month_last_day(_start).replace(day=1) if fileUnit == 'monthly' else self._get_next_day(_start)

                _startstr = _start.strftime(Config['dateformat'])
                _endstr = _end.strftime(Config['dateformat'])


                filepath = self.GetDataFilePath(_start, exchange = 'Binance', assetType = 'spot', fileUnit = fileUnit, dataType = dataType, symbol = symbol, interval = interval)

                if os.path.exists(filepath): continue

                data = self.get_klines_iter(symbol, interval, _start, _end, limit=5000)

                data = self.Get_Historical_Data(dataType, symbol, interval, _startstr, _endstr)
                data_arr = np.array(data)
                if data_arr.shape[0] <= 0 : continue

                if dataType == 'klines':
                    dataDic = {
                        'Time': data_arr[:, 0].astype(np.int64),
                        'Open': data_arr[:, 1].astype(np.float32),
                        'Ligh': data_arr[:, 2].astype(np.float32),
                        'Low': data_arr[:, 3].astype(np.float32),
                        'Close': data_arr[:, 4].astype(np.float32),
                        'Volume': data_arr[:, 5].astype(np.float32),
                        'Close_time': data_arr[:, 6].astype(np.int64),
                        'Quote_asset_volume': data_arr[:, 7].astype(np.float32),
                        'Number_of_trades': data_arr[:, 8].astype(np.int),
                        'Taker_buy_base_asset_volume': data_arr[:, 9].astype(np.float32),
                        'Taker_buy_quote_asset_volume': data_arr[:, 10].astype(np.float32),
                    }
                elif dataType == 'aggTrades':
                    dataDic = {
                        'AggTradeId': data_arr[:, 0].astype(np.int64),
                        'Price': data_arr[:, 1].astype(np.float32),
                        'Quantity': data_arr[:, 2].astype(np.float32),
                        'FirstTradeId': data_arr[:, 3].astype(np.int64),
                        'LastTradeId': data_arr[:, 4].astype(np.int64),
                        'Timestamp': data_arr[:, 5].astype(np.int64),
                        'BuyerMaker': (data_arr[:, 6] == 'True').astype(np.bool),
                        'BestPriceMatch': (data_arr[:, 7] == 'True').astype(np.bool),
                    }

                else: 
                    assert False

                dataframe = pd.DataFrame( data = dataDic )

                dataframe.to_csv(path_or_buf = filepath, header = None, index = None)


    def GetDataFilePath(self, startTime, exchange = 'Binance', assetType = 'spot', fileUnit = 'monthly', dataType = 'klines', symbol = 'ETH/USDT', interval = '1m'):
        filename = None
        if fileUnit == 'monthly':
            filename = symbol + '-' + interval + '-' + str(startTime.year)+'-'+str(startTime.month).zfill(2) + '.csv'
        elif fileUnit == 'daily':
            filename = symbol + '-' + interval + '-' + str(startTime.year)+'-'+str(startTime.month).zfill(2) + '-' + str(startTime.day).zfill(2) + '.csv'

        if self.GetDateTimeToday() <= startTime:
            filename = '_' + filename #--------------------- Notational differentiation.

        path = Config['Data']
        for dir in ['', exchange, assetType, fileUnit, dataType, symbol, interval]:
            path = os.path.join(path, dir)
            if not os.path.exists(path): os.mkdir(path)

        filepath = os.path.join(path, filename)

        return filepath


    def get_klines_iter(self, symbol, interval, start, end, limit=5000):
        df = pd.DataFrame()
        startDate = end
        while startDate>start:
            url = 'https://api.binance.com/api/v3/klines?symbol=' + \
                symbol + '&interval=' + interval + '&limit='  + str(limit)
            #if startDate is not None:
            #    url += '&endTime=' + str(startDate)
            
            df2 = pd.read_json(url)
            df = pd.concat([df2, df], axis=0, ignore_index=True, keys=None)
            #startDate = df.Opentime[0]
        df.reset_index(drop=True, inplace=True)    
        return df 

        """
        root_url = 'https://api.binance.com/api/v1/klines'
        url = root_url + '?symbol=' + symbol + '&interval=' + interval
        data = json.loads(requests.get(url).text)
        df = pd.DataFrame(data)
        #df.index = [dt.datetime.fromtimestamp(x/1000.0) for x in df.close_time]
        return df
        """

    def FindCacheFiles(self, startTime, endTime, exchange, assetType, dataType, symbol, interval):
        
        filePaths = []

        fileUnit = 'monthly'
        start = datetime( time.year, time.month, 1 if fileUnit == 'monthly' else time.day )
        filePaths.append(self.GetDataFilePath(start, 'Binance', 'spot', fileUnit, 'klines', symbol, interval))

        fileUnit = 'daily'
        start = datetime( time.year, time.month, 1 if fileUnit == 'monthly' else time.day )
        filePaths.append(self.GetDataFilePath(start, 'Binance', 'spot', fileUnit, 'klines', symbol, interval))

        filePath = None
        for path in filePaths:
            if os.path.exists(path):
                filePath = path
                break
        
        return filePath




"""

bn = Binance.instantiate()

start = datetime(2021, 6, 25) # "01 January, 2021" datetime(2021, 1, 1).month, dt.datetime.strptime( datetime(2021, 3, 1).strftime("%b %d, %Y"), "%b %d, %Y")
end = datetime(2021, 6, 27)
dataType = 'aggTrades' #'klines'
symbols = ['ETHBTC'] #, 'BTCUSDT', 'ETHUSDT', 'MATICUSDT', '1INCHUSDT', 'XRPUSDT', 'DOTUSDT']
interval = '1m' #Client.KLINE_INTERVAL_15MIN

bn.DownloadData(start = start, end = end, dataType = dataType, fileUnit = 'daily', symbols = symbols, interval = interval)

"""
