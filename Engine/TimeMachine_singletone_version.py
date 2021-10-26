

import os
import time
import win32api
from threading import Timer

from config import *

class TimeMachine():

    _singleton = None
    tense = None
    originSec = None
    intervalSec = None
    
    #currentInterval = None

    def __init__():
        raise RuntimeError('Call instance() instead')

    @classmethod
    def instance(cls, tense = Tense.Present, intervalSec = 1.0, originSec = None):
        if cls._singleton is None:
            cls._singleton = cls.__new__(cls)

            cls.tense = tense
            cls.intervalSec = intervalSec

        if cls.tense == Tense.Present:
            timeSec = time.time()
            originSec = timeSec

            cls.originSec = originSec

            #cls.currentInterval, _ = cls.TimeToInterval( timeSec ) # should be 0.

            # Regularly update currentInterval.
            #timer = Timer( interval = cls.intervalSec, function=cls.UpdateCurrentInterval )
            #timer.start()

            mili= round( (cls.originSec - int(cls.originSec)) * 1000 + 1 )
            gmtime = time.gmtime( originSec )
            win32api.SetSystemTime(gmtime[0], gmtime[1], 0, gmtime[2], gmtime[3], gmtime[4], gmtime[5], mili) # Needs Administrator Permission

        else:
            assert originSec is not None
            cls.originSec = originSec

            cls.currentIntervalForPastTense = 0

        return cls._singleton

    @classmethod
    def TimeToIntervals(cls, timeSec): # For any tense.
        intervalsFloat = (timeSec - cls.originSec) / cls.intervalSec
        intervalsInt= round( intervalsFloat )
        fractionSec = (intervalsFloat - intervalsInt) * cls.intervalSec
        return intervalsInt, fractionSec

    @classmethod
    def GetCurrentInterval(cls):
        if cls.tense == Tense.Present:
            intervalsInt, _ = cls.TimeToIntervals(time.time())
        else:
            intervalsInt = cls.currentIntervalForPastTense # Who maintains this value?

        return intervalsInt

    @classmethod
    def SleepForIntervals(cls, callerInterval, intervals = 1): #------------------------------------- Performs a time machine.
        assert type(callerInterval) == int
        assert type(intervals) == int

        if cls.tense == Tense.Present:
            currentInterval, fractionSec = cls.TimeToIntervals( time.time() )
            deltaInterval = callerInterval + intervals - currentInterval
            #assert deltaInterval >= 0
            sleepSec = deltaInterval * cls.intervalSec - fractionSec
            if sleepSec > 0: time.sleep( sleepSec )
            intervalsInt, _ = cls.TimeToIntervals( time.time() )
        else: # cls.tense is Tense.Past or cls.tense is Tense.Future
            intervalsInt = callerInterval + intervals

        discretTimeSec = intervalsInt * cls.intervalSec
        return intervalsInt, discretTimeSec

    #@classmethod
    #def UpdateCurrentInterval(cls):
    #    cls.currentInterval, _ = cls.TimeToInterval( time.time() )
    #    return
    
    #@classmethod
    #def GetCurrentInterval(cls):
    #    return cls.currentInterval
    
