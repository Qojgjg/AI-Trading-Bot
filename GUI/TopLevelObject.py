from tkinter import StringVar, messagebox
import tkinter.font as tkFont
import tkinter as tk

from .config import *

class TopLevelObject():
    engine = None

    def __init__(self, root, **options):
        self.root = root
        options['bg'] = Color.BG2.value
        self.frame = tk.Frame(root, options)
        self.frame.grid(sticky='NEWS')
    
    def Grid(self, options):
        self.frame.grid(options)
        pass

    def Pack(self, options):
        self.frame.pack(options)
        pass

    def Set_Engine(self, engien):
        self.engine = engien
        return
