
import os
from enum import Enum


Config = {}

Root = os. getcwd()
Config['Root'] = Root
Config['Data'] = os.path.join( Root, 'Engine\\Data' )
Config['History'] = os.path.join( Root, 'History' )
Config['Models'] = os.path.join( Root, 'Models' )
Config['Reports'] = os.path.join( Root, 'Reports' )
Config['Summary'] = os.path.join( Root, 'Summary' )
Config['CheckPoints'] = os.path.join( Root, 'CheckPoints' )

os.environ["STORE_DIRECTORY"] = Config['Data']

Config['.NCheck'] = 30

Config['api_key'] = os.getenv('Binance_API_Key')
Config['api_secret'] = os.getenv('Binance_API_Secret')

Config['dateformat'] = "%b %d, %Y"
Config['datefimeformat'] = "%b %d, %Y %H:%M:%S"


class Tense(Enum):
    Past = 1
    Present = 2
    Future = 3

Config['timing'] = \
{
    'tense': Tense.Present,
    'intervalSec': 1.0,
    'originSec': 999,
    'intervalsPerStep': 20,
}


Config['Exchanges'] = {
    'Exchange1': {
        'Type' : 'Binance',
        'Name' : 'Binance',
        'DataTypes' : ['klines'],
        'Symbols': ['ETHUSDT'],
        'Intervals': ['1m'],
    }
}

Config['structure'] = \
{
    'Name': 'SimpleEngine',
    'Traders':
    {
        'Trader1': 
        {
            'Type': 'SimpleTrader',
            'Name': '(1)',
            'Cared': True,
            'Strategies':
            {
                'Strategy1':
                {
                    'Type': 'SimpleStrategy',
                    'Name': '(1, 1)',
                    'Indicators':
                    {
                        'Indicator1':
                        {
                            'Type': 'SimpleIndicator',
                            'Name': '(1, 1, 1)',
                            'Period': 9,
                            'Channels' : [ 
                                { 'Exchange': 'Binance', 'Channel': 'klines.ETHUSDT.1m' } 
                            ],
                        },
                        'Indicator2':
                        {
                            'Type': 'SimpleIndicator',
                            'Name': '(2, 1, 1)',
                            'Period': 25,
                            'Channels' : [ 
                                { 'Exchange': 'Binance', 'Channel': 'klines.ETHUSDT.1m' } 
                            ],
                        }
                    }
                },
                'Strategy2':
                {
                    'Type': 'SimpleStrategy',
                    'Name': '(2, 1)',
                    'Indicators':
                    {
                        'Indicator1':
                        {
                            'Type': 'SimpleIndicator',
                            'Name': '(1, 2, 1)',
                            'Period': 15,
                            'Channels' : [ 
                                { 'Exchange': 'Binance', 'Channel': 'klines.ETHUSDT.1m' } 
                            ],
                        },
                        'Indicator2':
                        {
                            'Type': 'SimpleIndicator',
                            'Name': '(2, 2, 1)',
                            'Period': 30,
                            'Channels' : [ 
                                { 'Exchange': 'Binance', 'Channel': 'klines.ETHUSDT.1m' } 
                            ],
                        },
                    },
                },
            },
        },
    },
}


