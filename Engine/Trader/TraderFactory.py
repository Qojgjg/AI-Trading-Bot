

from ..ThreadOnTimeMachine import *
from .SimpleTrader import *

from ..config import *

class TraderFactory():

    def CreateTrader(structuralParams, timingParams):
        trader = None

        type = structuralParams['Type']

        if type == 'SimpleTrader':
            trader = SimpleTrader(structuralParams, timingParams)
        else:
            raise Exception('Invalid trader type')
        
        return trader
