from ..ThreadOnTimeMachine import *
from ..Exchange.ExchangeFactory import *
from ..Exchange.GStreamFactory import *

from ..config import *

class Indicator(ThreadOnTimeMachine):
    def __init__(self, structuralParams, timingParams):
        ThreadOnTimeMachine.__init__(self, structuralParams, timingParams)

        self.exchanges = set()
        self.gstreams = {}
        for gstream_name, gstream_params in structuralParams['GStreams'].items():
            if self.gstreams.get(gstream_name, None) is None:
                exchnage, gstream = GStreamFactory.CreateGStream(gstream_params, granular=True)
                self.exchanges.add(exchnage)
                self.gstreams[gstream_name] = gstream
            else:
                raise Exception('Duplicate GStream Name.')
        
        #self.contractors = [ exchange for exchange in self.exchanges ]
        #for contractor in self.contractors: contractor.clients.append(self)

    def __setInstance__(self, structuralParams, timingParams):
        super().__setInstance__(structuralParams, timingParams)
        self.name = structuralParams['Name']
        self.intervalsPerStep = timingParams['intervalsPerStep']

        return

    def SingleStep(self, stepId):
        super().SingleStep(stepId)
        #print('Indicator - {}: step {}, currInterval {}'.format(self.name, stepId, self.currentInterval))

        return
  