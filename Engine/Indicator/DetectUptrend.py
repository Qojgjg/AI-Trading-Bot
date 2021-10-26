from .Indicator import *

from .. config import *

class GoodIndicator(Indicator):
    def __init__(self, structuralParams, timingParams):
        super().__init__(structuralParams, timingParams)

    def SingleStep(self, stepId):
        super().SingleStep(stepId)

        for gstream_name, gstream_key in self.gstreams.items():
            if gstream_key is not None:
                [dataType, symbol, interval] = gstream_key.split('.')
                start = dt.datetime.now() - dt.timedelta(days=int(dt.datetime.now().microsecond/600000), hours=int(dt.datetime.now().microsecond/50000), minutes=dt.datetime.now().second, seconds=dt.datetime.now().second) #vicious test.
                end = None #dt.datetime.now()
                #dataframe = Binance._singleton.Get_Filed_Data_By_Time( dataType, symbol, interval, start, end )

        return