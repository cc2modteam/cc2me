import tkinter
from .image_loader import load_icon


class Toolbar:

    def __init__(self, parent, **kwargs):
        self.frame = tkinter.Frame(parent, **kwargs)
        self.buttons = {}

    def add_button(self, name: str, icon: str, command: callable, state=tkinter.NORMAL):
        b = tkinter.Button(self.frame,
                           text=name, image=load_icon(icon),
                           state=state,
                           command=command)
        b.pack(fill=tkinter.X, side=tkinter.LEFT)
        self.buttons[name] = b

    def enable(self, name: str):
        if name in self.buttons:
            self.buttons[name]["state"] = tkinter.NORMAL

    def disable(self, name: str):
        if name in self.buttons:
            self.buttons[name]["state"] = tkinter.DISABLED
