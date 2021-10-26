import os, sys
import threading
import time as tm

def thread_fun():
    print('starting and quiting thread fun')
    sys.exit(0)

thread = threading.Thread(target=thread_fun, args=())
thread.start()

tm.sleep(1)
pass
thread.start()

pass
