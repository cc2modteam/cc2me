import tkinter
from typing import Optional
from tkinter import ttk
from cc2me.savedata.types.objects import CC2MapItem


class PropertyItem:
    def __init__(self, owner, name, value, choices=None):
        self.owner = owner
        self.name = name
        self.value = value
        self.choices = choices
        self.textvalue = None
        self.label = None
        self.value_widget = None

    def on_modified(self, event):
        owner: Optional[Properties] = self.owner
        if owner is not None:
            if self.textvalue is not None:
                obj: CC2MapItem = self.owner.object
                self.textvalue: tkinter.StringVar
                value = self.textvalue.get()
                # try setting
                try:
                    setattr(obj, self.name, value)
                except AttributeError:
                    pass
                except LookupError:
                    pass
                except ValueError:
                    pass


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
    def object(self) -> CC2MapItem:
        return self._object

    @object.setter
    def object(self, new_value: CC2MapItem):
        self.clear()
        self._object = new_value
        if new_value is not None:
            self.title.set(self.object.display_ident)
            for prop in new_value.viewable_properties:
                value = new_value.__getattribute__(prop)
                choices = None
                try:
                    choices = ["None"] + new_value.__getattribute__(f"{prop}_choices")
                except AttributeError:
                    pass
                self.add_option_property(prop, value, choices)

    def clear(self):
        for item in self.option_items:
            item: PropertyItem
            item.label.pack_forget()
            item.label.destroy()
            if item.value_widget:
                item.value_widget.pack_forget()
                item.value_widget.destroy()
            item.textvalue = None
        self.option_items.clear()
        self.items.pack_forget()
        self.title.set("")

    def add_option_property(self, text: str, selected=None, values: Optional[list] = None):
        opt = PropertyItem(self, text, selected, values)
        opt.label = tkinter.Label(self.items, text=text, anchor=tkinter.W, width=40, justify=tkinter.LEFT)
        if opt.choices is not None:
            opt.textvalue = tkinter.StringVar(self.items)
            opt.textvalue.set(selected)
            opt.value_widget = ttk.Combobox(self.items, textvariable=opt.textvalue)
            opt.value_widget.bind("<<ComboboxSelected>>", opt.on_modified)
            opt.value_widget["values"] = opt.choices
        else:
            opt.value_widget = tkinter.Label(self.items, text=str(selected), anchor=tkinter.W)

        opt.label.pack(side=tkinter.TOP, expand=True, fill=tkinter.Y)
        opt.value_widget.pack(side=tkinter.TOP, expand=True, fill=tkinter.Y)
        self.option_items.append(opt)
        self.items.pack()

