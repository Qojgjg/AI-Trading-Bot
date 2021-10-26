import sys
import threading
import datetime as dt
import time as tm

from abc import ABC, abstractmethod

from .TimeMachine import *
from .config import *

class ThreadOnTimeMachine(ABC):

    #debug = ""

    nInstances = 0
    instances = []

    def __init__(self, structuralParams, timingParams, steps = None):
        self.__resume_flag = threading.Event() # The flag used to pause the thread
        self.__run_flag = threading.Event() # Used to top the thread indeitification
        self.__contractorscanstart_flag = threading.Event()
        self.__contractorsfinished_flag = threading.Event()
        self.__icanstart_flag = threading.Event()
        self.thread = None

        self.timeMachine = TimeMachine(timingParams)
        self.currentInterval = None
        self.intervalsPerStep = timingParams['intervalsPerStep']

        self.__setInstance__(structuralParams, timingParams) # Calls __setInstance__() of the immediate subclass, not that of sub-sub class.

        self.steps = steps

        ThreadOnTimeMachine.nInstances += 1
        ThreadOnTimeMachine.instances.append(self)

        self.finished = False
        self.clients = []
        self.contractors = []

    def __del__(self):
        ThreadOnTimeMachine.nInstances -= 1

    def RegisterClient(self, client):
        if self.clients.index(client) < 0:
            self.clients.append(client)

    def UnregisterClient(self, client):
        if self.clients.index(client) >= 0:
            self.clients.remove(client)

    @abstractmethod
    def __setInstance__(self, structuralParams, timingParams):
        pass

    def Start(self): # Bottom-up start.

        TimeMachine.SetOriginSec(tm.time())

        if self.thread is not None: return

        if len(self.clients) <= 0: 
            print( "{}: Root starting a new round.\n".format( dt.datetime.timestamp(dt.datetime.now())) )
            self.__icanstart_flag.set()
        else:
            self.__icanstart_flag.clear()

        self.__contractorsfinished_flag.clear()
        for contractor in self.contractors: contractor.Start()

        self.__run_flag.set()
        self.__resume_flag.set()

        self.thread = threading.Thread(target=self.ThreadFunciton, args=(self.steps,)) #--------------------------
        self.thread.start()

    def Stop(self): # Bottom-up stop.
        for contractor in self.contractors: contractor.Stop()
        #for contractor in self.contractors: contractor.Join()

        self.__resume_flag.set() # Resume the thread from the suspended state, if it is alread suspended
        self.__run_flag.clear() # Set to False
        #self.thread.join(). Parent is Joining, instead.
        #self.thread = None

        #if len(self.clients) <= 0:
        #    self.Join() # Self-join.
        #    print('Root Timemachine joined()')

    def Join(self):
        for contractor in self.contractors: contractor.Join()
        self.thread.join()

    def Pause(self):
        self.__resume_flag.clear() # Set to False to block the thread

    def Resume(self):
        self.__resume_flag.set() # Set to True, let the thread stop blocking

    def OnContractorFinished(self, callingContractor):
        allfinished = True
        for contractor in self.contractors:
            if contractor.__icanstart_flag.is_set():
                allfinished = False
                break
        if allfinished:
            self.__contractorsfinished_flag.set()
            #print("{}: contractors finished.".format(self.name))

        last = 'All done' if allfinished else ''
        #if len(callingContractor.contractors) > 0:
        print( "{}: {} finished. {}\n".format( dt.datetime.timestamp(dt.datetime.now()) , callingContractor.name, last) )


    def ThreadFunciton(self, steps):
        stepId = -1
        while steps is None or stepId < steps:
            stepId += 1
            self.__resume_flag.wait()

            # self.__contractorsfinished_flag.is_set() : No
            # self.__icanstart_flat.is_set() : No for all but the root.

            if self.__run_flag.is_set():
                self.__icanstart_flag.wait() # All is locked here except Root.

            if len(self.contractors) > 0:
                for contractor in self.contractors: contractor.__icanstart_flag.set() # Free all the contractores, so they can finish.
                if self.__run_flag.is_set():
                    self.__contractorsfinished_flag.wait() # Wait until all contractores have finished
                    self.__contractorsfinished_flag.clear() # Consume the fact that all contractors have finished.

            if self.__run_flag.is_set():
                self.SingleStep(stepId) # As all contractores have finished, it's my turn to do.

            self.__icanstart_flag.clear()

            if len(self.clients) > 0:
                for client in self.clients: client.OnContractorFinished(self)
                if not self.__run_flag.is_set(): break
            else:
                print( "{}: --------- Root: Finished a round. Sleeping.\n".format( dt.datetime.timestamp(dt.datetime.now())) )
                self.__icanstart_flag.set() # Only root can free itself up.

                if not self.__run_flag.is_set(): break
                self.currentInterval, _ = self.timeMachine.SleepForIntervals(self.currentInterval, self.intervalsPerStep)
                if not self.__run_flag.is_set(): break
                print( "{}: Root: Starting a new step. -----------\n".format( dt.datetime.timestamp(dt.datetime.now())) )

        print('Time machine {} is quiting.'.format(self.name))
        #sys.exit(0) # Do NOT sys.exit(0), as join() is waiting.
        if len(self.contractors) > 0:
            for contractor in self.contractors: contractor.__icanstart_flag.set() # Free all the contractores, so they can finish.


    @abstractmethod
    def SingleStep(self, stepId):
        for n in range( 5 * pow(10, 6) ): a = pow(n, 0.5)
        pass

    def from_dt_local_to_dt_utc( dt_local ):
        now_timestamp = tm.time()
        offset = dt.datetime.fromtimestamp(now_timestamp) - dt.datetime.utcfromtimestamp(now_timestamp)
        return dt_local - offset

    def from_dt_utc_to_dt_local( dt_utc ):
        now_timestamp = tm.time()
        offset = dt.datetime.fromtimestamp(now_timestamp) - dt.datetime.utcfromtimestamp(now_timestamp)
        return dt_utc + offset