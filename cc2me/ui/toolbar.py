import tkinter
from .image_loader import load_icon


class Toolbar:

    def __init__(self, parent, **kwargs):
        self.frame = tkinter.Frame(parent, **kwargs)
        self.buttons = {}

    def add_button(self, name: str, icon: str, command: callable, state=tkinter.NORMAL,
                   group="default"):
        b = tkinter.Button(self.frame,
                           text=name, image=load_icon(icon),
                           state=state,
                           command=command)
        b.pack(fill=tkinter.X, side=tkinter.LEFT)
        if group not in self.buttons:
            self.buttons[group] = {}
        self.buttons[group][name] = b

    def enable_group(self, group):
        if group in self.buttons:
            for name in self.buttons[group]:
                self.buttons[group][name]["state"] = tkinter.NORMAL

    def enable(self, name: str):
        for group in self.buttons:
            for btn_name in self.buttons[group]:
                if btn_name == name:
                    self.buttons[group][name]["state"] = tkinter.NORMAL

    def disable(self, name: str):
        for group in self.buttons:
            for btn_name in self.buttons[group]:
                if btn_name == name:
                    self.buttons[group][name]["state"] = tkinter.DISABLED

    def disable_group(self, group):
        if group in self.buttons:
            for name in self.buttons[group]:
                self.buttons[group][name]["state"] = tkinter.DISABLED
