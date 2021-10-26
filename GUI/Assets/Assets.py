from tkinter import StringVar, messagebox
import tkinter.font as tkFont
import tkinter as tk

from ..config import *
from ..TopLevelObject import *


class Assets(TopLevelObject):
    def __init__(self, master):
        super().__init__(master)

    def Grid(self, **options):
        super().Grid(options)

        tk.Label(self.frame, text='Assets').grid(row=1, column=1)
        for label in range(5):
            tk.Label(self.frame, text='Assets label, Assets lable ' + str(label).zfill(2)).grid(row=label+2, column=1)
        

    def Pack(self, **options):
        super().Pack(options)
        
        self.button1 = tk.Button(self.frame, text='Assets button top')
        self.button1.pack(side='top')

        self.button2 = tk.Button(self.frame, text='Assets button bottom')
        self.button2.pack(side='bottom')
