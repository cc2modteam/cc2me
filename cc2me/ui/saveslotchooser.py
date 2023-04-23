"""Dialog to select a CC2 save slot"""
import tkinter
from functools import partial
from xml.etree import ElementTree
from xml.etree.ElementTree import Element
from tkinter import simpledialog

from cc2me.savedata.constants import read_save_slots


class SlotChooser(simpledialog.Dialog):

    def select(self, slot):
        print(f"selected {slot}")
        self.choice[1] = slot
        self.destroy()

    def body(self, master) -> None:
        super().body(master)
        for slot in self.slots:
            callback = partial(self.select, dict(slot))
            btn = tkinter.Button(master,
                                 text=slot["display"],
                                 command=callback)
            btn.pack(fill=tkinter.X)

    def __init__(self, app, persistent_file: str, choice: dict, title="Load a save slot"):
        self.persistent_file = persistent_file
        self.slots = read_save_slots(persistent_file)
        self.choice = choice

        super(SlotChooser, self).__init__(parent=app, title=title)


