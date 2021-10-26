from copy import deepcopy
from .Indicator import *

from ..config import *

class SimpleIndicator(Indicator):
    def __init__(self, structuralParams, timingParams):
        super().__init__(structuralParams, timingParams)

    def SingleStep(self, stepId):
        super().SingleStep(stepId)

        if Binance.granualar_gstreams_ready:
            for n in range( pow(10, 6) ): a = pow(n, 0.5)

            trials = 10
            keys = copy.copy(list(Binance.gstreams.keys()))
            for key in keys:
                [dataType, symbol, interval] = key.split('.')
                with Binance.lock_gstream:
                    if Binance.gstreams.get(key, None) is not None:
                        start = dt.datetime.now() - dt.timedelta(days=int(dt.datetime.now().microsecond/600000), hours=int(dt.datetime.now().microsecond/50000), minutes=dt.datetime.now().second, seconds=dt.datetime.now().second) #vicious test.
                        end = Binance.gstream_datetime + dt.timedelta(seconds=1) # end is exclusive.
                        dataframe = Binance._singleton.Get_Filed_Data_By_Time( dataType, symbol, interval, start, end )
                        trials -= 1
                        if trials <= 0: break

        return
  