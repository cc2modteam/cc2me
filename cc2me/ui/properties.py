import tkinter
from typing import Optional, Any, List
from tkinter import ttk
from ..savedata.types.objects import MapItem
from .mapmarkers import MapItemMarker


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
                    obj: MapItem
                    self.textvalue: tkinter.StringVar
                    value = self.textvalue.get()
                    # try setting
                    dynamic = obj.dynamic_attribs.get(self.name, None)
                    if dynamic:
                        dynamic.set(value)
                        continue
                    try:
                        setattr(obj, self.name, value)
                    except AttributeError:
                        pass
                    except LookupError:
                        pass
                    except ValueError:
                        pass

            for marker in owner.map_widget.canvas_marker_list:
                if isinstance(marker, MapItemMarker):
                    marker: MapItemMarker
                    if marker.selected:
                        marker.update_shape_outline()
                        marker.redraw()


class Properties:
    def __init__(self, parent):
        self.width = 400
        self.parent = parent
        self.frame = tkinter.Frame(self.parent, relief=tkinter.SUNKEN, width=self.width)
        self.title = tkinter.Variable(self.frame, value="Current object:")
        self.title_label = tkinter.Label(self.frame,
                                         anchor=tkinter.NW,
                                         textvariable=self.title,
                                         width=40,
                                         height=1,
                                         bg="#cdcdcd")
        self.title_label.pack(side=tkinter.TOP, expand=False, fill=tkinter.X)
        self.rows = tkinter.Frame(self.frame)
        self.row_frames = []
        self.option_items = []
        self._objects = None
        self.map_widget = None

    @property
    def objects(self) -> List[MapItem]:
        return self._objects

    @objects.setter
    def objects(self, new_value: List[MapItem]):
        self.clear()
        self._objects = list(new_value)
        if new_value is not None:
            if len(self.objects) == 1:
                obj: MapItem = self.objects[0]
                self.title.set(obj.display_ident)
                # show normal props

                for prop in obj.viewable_properties:
                    value = getattr(obj, prop)
                    # value = obj.__getattribute__(prop)
                    choices = None
                    try:
                        choices = ["None"] + getattr(obj, f"{prop}_choices")
                    except AttributeError:
                        pass
                    self.add_option_property(prop, value, choices)

                for attr_name in sorted(obj.dynamic_attribs.keys()):
                    value = obj.dynamic_attribs[attr_name].get()
                    choices = None
                    try:
                        choices = ["None"] + getattr(obj, f"{attr_name}_choices")
                    except AttributeError:
                        pass
                    self.add_option_property(attr_name, value, choices)

            elif len(self._objects) > 1:
                self.title.set(f"Multiple ({len(self.objects)}) objects selected")
                obj: MapItem = self.objects[0]
                # multiple objects,
                # allow only change of team
                self.add_option_property("team_owner", selected="None",
                                         values=obj.team_owner_choices)
                self.add_option_property("alt", selected="None",
                                         values=[0, 50, 100, 300, 800])

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
        for row in self.row_frames:
            row.pack_forget()
            row.destroy()
        self.row_frames.clear()
        self.rows.pack_forget()
        self.title.set("")

    def add_option_property(self, text: str, selected=None, values: Optional[list] = None):
        row = tkinter.Frame(self.rows, width=self.width)

        opt = PropertyItem(self, text, selected, values)
        opt.label = tkinter.Label(row,
                                  text=text, anchor=tkinter.W, width=20, justify=tkinter.LEFT)
        if opt.choices is not None:
            opt.textvalue = tkinter.StringVar(self.rows)
            opt.textvalue.set(selected)
            opt.value_widget = ttk.Combobox(row, textvariable=opt.textvalue,
                                            width=int(self.width * 0.7))
            opt.value_widget.bind("<<ComboboxSelected>>", opt.on_modified)
            opt.value_widget["values"] = opt.choices
        else:
            opt.value_widget = tkinter.Label(row, text=str(selected), anchor=tkinter.W,
                                             width=int(self.width * 0.7))

        opt.label.pack(side=tkinter.LEFT, expand=False, fill=tkinter.NONE)
        opt.value_widget.pack(side=tkinter.RIGHT, expand=False, fill=tkinter.NONE)

        self.option_items.append(opt)
        self.row_frames.append(row)
        row.pack(side=tkinter.TOP, fill=tkinter.NONE, expand=False)
        self.rows.pack(fill=tkinter.NONE, expand=False)

