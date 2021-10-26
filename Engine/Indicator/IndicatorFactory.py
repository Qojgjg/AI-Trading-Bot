from ..ThreadOnTimeMachine import *
from .SimpleIndicator import *
from .GoodIndicator import *
from .ProductsPrices import *
from .ProductsPrices_Stream import *


from ..config import *

class IndicatorFactory():

    def CreateIndicator(structuralParams, timingParams):
        indicator = None

        type = structuralParams['Type']

        if type == 'SimpleIndicator':
            indicator = SimpleIndicator(structuralParams, timingParams)
        elif type == 'GoodIndicator':
            indicator = GoodIndicator(structuralParams, timingParams)
        elif type == 'ProductsPrices':
            indicator = ProductsPrices(structuralParams, timingParams)
        elif type == 'ProductsPrices_Stream':
            indicator = ProductsPrices_Stream(structuralParams, timingParams)
        else:
            raise Exception('Invalid strategy type')
        
        return indicator