import tkinter
from typing import Optional

from cc2me.savedata.types.objects import CC2MapItem


class PropertyItem:
    def __init__(self, name, value, choices=None):
        self.name = name
        self.value = value
        self.choices = choices

        self.label = None
        self.value_widget = None


class Properties:
    def __init__(self, parent):
        self.parent = parent
        self.frame = tkinter.Frame(self.parent, relief=tkinter.SUNKEN)
        self.title = tkinter.Variable(self.frame, value="Current object:")
        self.title_label = tkinter.Label(self.frame,
                                         anchor=tkinter.NW,
                                         textvariable=self.title,
                                         width=40,
                                         height=1,
                                         bg="#cdcdcd")
        self.title_label.pack(side=tkinter.TOP, expand=True, fill=tkinter.Y)
        self.items = tkinter.Frame(self.frame)
        self.option_items = []
        self._object = None

    @property
    def object(self):
        return self._object

    @object.setter
    def object(self, new_value: CC2MapItem):
        self.clear()
        self._object = new_value
        if new_value is not None:
            self.title.set(self.object.display_ident)
            for prop in new_value.viewable_properties:
                value = new_value.__getattribute__(prop)
                self.add_option_property(prop, value, None)

    def clear(self):
        for item in self.option_items:
            item: PropertyItem
            item.label.pack_forget()
            item.label.destroy()
            if item.value_widget:
                item.value_widget.pack_forget()
                item.value_widget.destroy()
        self.option_items.clear()
        self.items.pack_forget()
        self.title.set("")

    def add_option_property(self, text: str, selected=None, values: Optional[list] = None):
        opt = PropertyItem(text, selected, values)
        opt.label = tkinter.Label(self.items, text=text, anchor=tkinter.W, width=40, justify=tkinter.LEFT)

        opt.value_widget = tkinter.Label(self.items, text=str(selected), anchor=tkinter.W)

        opt.label.pack(side=tkinter.TOP, expand=True, fill=tkinter.Y)
        opt.value_widget.pack(side=tkinter.TOP, expand=True, fill=tkinter.Y)
        self.option_items.append(opt)
        self.items.pack()

