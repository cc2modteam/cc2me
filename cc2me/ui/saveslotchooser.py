"""Dialog to select a CC2 save slot"""
import tkinter
from functools import partial
from xml.etree import ElementTree
from xml.etree.ElementTree import Element
from tkinter import simpledialog


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

    def __init__(self, app, persistent_file: str, choice: dict, title="Load a save slot",  ):
        self.persistent_file = persistent_file
        self.slots = []
        self.choice = choice
        with open(self.persistent_file, "r") as xmlfile:
            xml = xmlfile.read()
        self.etree = ElementTree.fromstring(xml)
        for item in self.etree:
            if isinstance(item, Element):
                filename = item.attrib.get("save_name")
                text = item.attrib.get("display_name")
                if filename:
                    self.slots.append({
                        "filename": filename,
                        "display": text
                    })

        super(SlotChooser, self).__init__(parent=app, title=title)


