import tkinter
from tkinter import simpledialog
from typing import Dict

import customtkinter

from cc2me.savedata.constants import InventoryIndex
from cc2me.savedata.types.objects import MapItem, InventoryMixin


class InventoryEditor(simpledialog.Dialog):
    def __init__(self, app, item: MapItem, title="Edit Inventory"):
        self.mapitem: MapItem = item
        self.inventory: Dict[InventoryIndex, int] = {}
        self.string_vars: Dict[InventoryIndex, tkinter.StringVar] = {}
        super(InventoryEditor, self).__init__(parent=app, title=title)
        self.rows = None


    def body(self, master) -> None:
        super().body(master)
        self.rows = customtkinter.CTkScrollableFrame(master, width=300)

        if isinstance(self.mapitem, InventoryMixin) and self.mapitem.has_inventory():
            for item in list(InventoryIndex):
                name = item.name
                value = self.mapitem.get_inventory_item(item)
                self.inventory[item] = value
                row = tkinter.Frame(self.rows, width=40)
                label = tkinter.Label(row,
                              text=name, anchor=tkinter.W, width=20, justify=tkinter.LEFT)
                self.string_vars[item] = tkinter.StringVar(row)
                self.string_vars[item].set(str(value))
                entry = tkinter.Entry(row, textvariable=self.string_vars[item])
                label.pack(side=tkinter.LEFT, expand=True, fill=tkinter.BOTH)
                entry.pack(side=tkinter.RIGHT, expand=True, fill=tkinter.BOTH)

                row.pack(side=tkinter.TOP, fill=tkinter.BOTH, expand=True)

                self.rows.pack(fill=tkinter.BOTH, expand=True)