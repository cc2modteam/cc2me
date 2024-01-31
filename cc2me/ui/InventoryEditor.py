import tkinter
from functools import partial
from tkinter import simpledialog
from tkinter.scrolledtext import ScrolledText
from typing import Dict

import customtkinter

from cc2me.savedata.constants import InventoryIndex
from cc2me.savedata.types.objects import MapItem, Carrier


class InventoryEditor(simpledialog.Dialog):
    def __init__(self, app, item: MapItem, title="Edit Inventory"):
        self.mapitem: MapItem = item
        self.inventory: Dict[InventoryIndex, int] = {}
        self.rows = None
        self.scroll = None
        self.string_vars: Dict[InventoryIndex, tkinter.StringVar] = {}
        super(InventoryEditor, self).__init__(parent=app, title=title)

    def body(self, master) -> None:
        super().body(master)

        self.scroll = customtkinter.CTkScrollableFrame(master)
        self.scroll.pack(pady=5)

        if isinstance(self.mapitem, MapItem) and self.mapitem.has_inventory():
            for item in list(InventoryIndex):
                name = item.name
                value = self.mapitem.get_inventory_item(item)
                self.inventory[item] = value
                row = tkinter.Frame(self.scroll, width=40)
                label = tkinter.Label(row,
                              text=name, anchor=tkinter.W, width=20, justify=tkinter.LEFT)
                self.string_vars[item] = tkinter.StringVar(row)
                self.string_vars[item].set(str(value))
                entry = tkinter.Entry(row, textvariable=self.string_vars[item])
                label.pack(side=tkinter.LEFT, expand=False, fill=tkinter.NONE)
                entry.pack(side=tkinter.RIGHT, expand=False, fill=tkinter.NONE)

                row.pack(side=tkinter.TOP, fill=tkinter.NONE, expand=False)
        #self.rows.pack(fill=tkinter.NONE, expand=False)
        #self.scroll.pack(fill="both", expand=True)