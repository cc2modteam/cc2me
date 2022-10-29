import tkinter
from typing import Optional, Any, List
from tkinter import ttk
from ..savedata.types.objects import CC2MapItem
from .mapmarkers import CC2DataMarker


class PropertyItem:
    def __init__(self, props: "Properties", name: str, value: Any, choices=None):
        self.owner = props
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
                for obj in self.owner.objects:
                    obj: CC2MapItem
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

            for marker in owner.map_widget.canvas_marker_list:
                if isinstance(marker, CC2DataMarker):
                    marker: CC2DataMarker
                    if marker.selected:
                        marker.update_shape_outline()
                        marker.redraw()


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
        self._objects = None
        self.map_widget = None

    @property
    def objects(self) -> List[CC2MapItem]:
        return self._objects

    @objects.setter
    def objects(self, new_value: List[CC2MapItem]):
        self.clear()
        self._objects = list(new_value)
        if new_value is not None:
            if len(self.objects) == 1:
                obj: CC2MapItem = self.objects[0]
                self.title.set(obj.display_ident)
                # show normal props

                for prop in obj.viewable_properties:
                    value = obj.__getattribute__(prop)
                    choices = None
                    try:
                        choices = ["None"] + obj.__getattribute__(f"{prop}_choices")
                    except AttributeError:
                        pass
                    self.add_option_property(prop, value, choices)
            elif len(self._objects) > 1:
                self.title.set(f"Multiple ({len(self.objects)}) objects selected")
                obj: CC2MapItem = self.objects[0]
                # multiple objects,
                # allow only change of team
                self.add_option_property("team_owner", "None",
                                         obj.team_owner_choices)

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

