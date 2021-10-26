
import os
import datetime as dt
import pytz
from enum import Enum
import time as tm

Config = {}

Config['start_time_utc'] = dt.datetime.utcnow().replace(tzinfo = pytz.utc)

Root = os. getcwd()
Config['Root'] = Root
Config['Data'] = os.path.join( "D:", '\\Trading_Data' )
Config['History'] = os.path.join( Root, 'History' )

os.environ["STORE_DIRECTORY"] = Config['Data']

Config['.NCheck'] = 30

Config['api_key'] = os.getenv('Binance_API_Key')
Config['api_secret'] = os.getenv('Binance_API_Secret')

Config['dateformat'] = "%b %d, %Y"
Config['datefimeformat'] = "%b %d, %Y %H:%M:%S"

Config['binance_wait_sec'] = 3.0
Config['max_slots_per_stream'] = 30 # The larger it is, the more requests per stream. The smaller it is, the mare stream threads we have.
Config['max_streams'] = 180
Config['timeSnapSlippageSec'] = 10


class Tense(Enum):
    Past = 1
    Present = 2
    Future = 3

BasicIntervalMin = 3 #---------------------------------------------------------------------------------

Config['ginterval'] = str(BasicIntervalMin ) + 'm'

Config['timing'] = \
{
    'tense': Tense.Present,
    'intervalSec': 1.0,
    'originSec': 999,
    'intervalsPerStep': BasicIntervalMin * 60
}

Config['structure'] = \
{
    'Name': 'SimpleEngine',
    'Traders':
    {
        'Trader1': 
        {
            'Type': 'SimpleTrader',
            'Name': '(1 - SimpleTrader',
            'Cared': True,
            'Strategies':
            {
                'Strategy1':
                {
                    'Type': 'SimpleStrategy',
                    'Name': '(1, 1 - SimpleStrategy',
                    'Indicators':
                    {
                        'Indicator1':
                        {
                            'Type': 'SimpleIndicator',
                            'Name': '(1, 1, 1 - SimpleIndicator)',
                            'GStreams' :
                            {
                                'GStream.1.1.1.1':
                                {
                                    'Type': 'Binance',
                                    'Name': 'GSteram1 (1, 1, 1, 1)',
                                    'dataType': 'klines',
                                    'symbol':   'ALICEUSDT',
                                    'interval': Config['ginterval']
                                },
                                'GStream.2.1.1.1':
                                {
                                    'Type': 'Binance',
                                    'Name': 'GSteram1 (2, 1, 1, 1)',
                                    'dataType': 'klines',
                                    'symbol':   'DOTUSDT',
                                    'interval': Config['ginterval']
                                },
                            }
                        },
                        'Indicator2':
                        {
                            'Type': 'GoodIndicator',
                            'Name': '(2, 1, 1 - GoodIndicator)',
                            'GStreams' :
                            {
                                'GStream.1.2.1.1':
                                {
                                    'Type': 'Binance',
                                    'Name': 'GSteram1 (1, 2, 1, 1)',
                                    'dataType': 'klines',
                                    'symbol':   '1INCHUSDT',
                                    'interval': Config['ginterval']
                                },
                            }
                        },
                        'Indicator3':
                        {
                            'Type': 'ProductsPrices_Stream',
                            'Name': '(3, 1, 1 - Prices_Stream)',
                            'Quote': 'USDT',
                            'MaxStreams': Config['max_streams'],
                            'Interval': Config['ginterval'],
                            'GStreams' :
                            {
                            },
                        },
#                        'Indicator4':
#                        {
#                            'Type': 'ProductsPrices',
#                            'Name': '(4, 1, 1 - Prices)',
#                            'Quote': 'USDT',
#                            'StructuralParams_Price_Thread':
#                            {
#                                
#                            },
#                            'TimingParams_Price_Thread': 
#                            {
#                                'tense': Tense.Present,
#                               'intervalSec': 1.0,
#                                'originSec': 999,
#                                'intervalsPerStep': int(Config['binance_wait_sec']),
#                            },
#                            'Interval': Config['ginterval'],
#                            'GStreams' :
#                            {
#                            },
#                        },
                    },
                },
                'Strategy2':
                {
                    'Type': 'SimpleStrategy',
                    'Name': '(2, 1 - SimpleStrategy',
                    'Indicators':
                    {
                        'Indicator1':
                        {
                            'Type': 'GoodIndicator',
                            'Name': '(1, 2, 1 - GoodIndicator)',
                            'GStreams' :
                            {
                                'GStream.1.1.2.1':
                                {
                                    'Type': 'Binance',
                                    'Name': 'GSteram1 (1, 1, 2, 1)',
                                    'dataType': 'klines',
                                    'symbol':   'BTCUSDT',
                                    'interval': Config['ginterval']
                                },
                                'GStream.2.1.2.1':
                                {
                                    'Type': 'Binance',
                                    'Name': 'GSteram1 (2, 1, 2, 1)',
                                    'dataType': 'klines',
                                    'symbol':   'ETHUSDT',
                                    'interval': Config['ginterval']
                                },
                            }
                        },
                        'Indicator2':
                        {
                            'Type': 'GoodIndicator',
                            'Name': '(2, 2, 1 - GoodIndicator)',
                            'GStreams' :
                            {
                                'GStream.1.2.2.1':
                                {
                                    'Type': 'Binance',
                                    'Name': 'GSteram3 (1, 2, 2, 1)',
                                    'dataType': 'klines',
                                    'symbol':   'MATICUSDT',
                                    'interval': Config['ginterval']
                                },
                            }
                        },
                    },
                },
            },
        },
    },
}


