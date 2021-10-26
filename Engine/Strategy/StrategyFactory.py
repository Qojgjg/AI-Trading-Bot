
from os import name
from ..ThreadOnTimeMachine import *
from ..Strategy.SimpleStrategy import *


from ..config import *

class StrategyFactory():

    def CreateStrategy(structuralParams, timingParams):
        strategy = None

        type = structuralParams['Type']

        if type == 'SimpleStrategy':
            strategy = SimpleStrategy(structuralParams, timingParams)
        else:
            raise Exception('Invalid strategy type')
        
        return strategy