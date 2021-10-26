import asyncio
import threading

import Engine.config

import Engine.___Engine
from Engine.___Engine import Engine
from Engine.config import *

from GUI.__GUI import GUI

import tkinter as tk

# Create tkinter window/app
root = tk.Tk()
root.title('SORTINO - AI Trading Platform')
#root.attributes('-topmost', True)
#root.geometry("1920x1080")
root.state('zoomed')
app = GUI(root)
#app['bg'] = "#1E1E1E"
#app.configure()
app.mainloop()