
from ..ThreadOnTimeMachine import *
from ..Strategy.StrategyFactory import *

from ..config import *

class SimpleTrader(ThreadOnTimeMachine):
    def __init__(self, structuralParams, timingParams):
        super().__init__(structuralParams, timingParams)
        self.contractors = [ StrategyFactory.CreateStrategy(strategyParams, timingParams)  for _, strategyParams in structuralParams['Strategies'].items() ]
        for contractor in self.contractors: contractor.clients.append(self)
     
    def __setInstance__(self, structuralParams, timingParams):
        super().__setInstance__(structuralParams, timingParams)
        self.name = structuralParams['Name']
        self.intervalsPerStep = timingParams['intervalsPerStep']
        return

    def SingleStep(self, stepId):
        super().SingleStep(stepId)
        #print('Trader - {}: step {}, currInterval {}'.format(self.name, stepId, self.currentInterval)) 
        return