
font = "Arial"
font_weight = "bold"
font_size = 14

from enum import Enum
class TradingSide(Enum):
    Buy = 1
    Sell = 2

class OrderType(Enum):
    Limit = 1
    Market = 2
    StopLimit = 3


class Color(Enum):
    Bid = 'green4'
    Ask = 'brown1'
    BG1 = 'gray1'
    BG2 = 'gray7'
    BG3 = 'gray15'
    LowFG = 'gray60'
    HighFG = 'gray99'


class Direction(Enum):
    Up = 1
    Down = 2
    Keep = 3


