import tkinter
from abc import ABC, abstractmethod
from typing import Optional, Callable, List, cast

from tkintermapview.canvas_position_marker import CanvasPositionMarker
from tkintermapview import TkinterMapView

from .cc2constants import get_team_color
from .mapshapes import CanvasShape
from ..savedata.constants import VehicleTypes
from ..savedata.types.objects import CC2MapItem, Island, Unit
from ..savedata.types.tiles import Tile


class Marker(CanvasPositionMarker, ABC):
    """An extensible marker"""
    def is_visible(self) -> bool:
        canvas_pos_x, canvas_pos_y = self.get_canvas_pos(self.position)
        return -50 < canvas_pos_x < self.map_widget.width + 50 and -50 < canvas_pos_y < self.map_widget.height + 70

    def draw(self, event=None):
        if not self.deleted:
            self.render(event)
            if not self.is_visible():
                self.map_widget.manage_z_order()

    @abstractmethod
    def render(self, event=None):
        pass


class ShapeMarker(Marker, ABC):

    def __init__(self,
                 map_widget: "TkinterMapView",
                 position: tuple,
                 text: Optional[str] = None,
                 text_color: Optional[str] = "#652A22",
                 command: Optional[Callable] = None,
                 data: any = None,
                 zoom_scale: Optional[int] = 1,
                 ):
        super(ShapeMarker, self).__init__(
            map_widget,
            position,
            text=text,
            text_color=text_color,
            command=command,
            data=data)
        self.label: Optional[CanvasShape] = None
        self._shapes: List[CanvasShape] = []
        self._zoom_scale_factor = zoom_scale

    def show_label(self) -> bool:
        return self.label is not None and self.map_widget.zoom > 4

    def add_shapes(self, *shapes: CanvasShape):
        for shape in shapes:
            self._shapes.append(shape)

    def render(self, event=None):
        if self.is_visible():
            x, y = self.get_canvas_pos(self.position)
            for shape in self._shapes:
                if shape.canvas_id == -1:
                    shape.render(x, y, self.map_widget.zoom * self._zoom_scale_factor)
                shape.update(self.map_widget.canvas, x, y, self.map_widget.zoom * self._zoom_scale_factor)
            if self.show_label():
                if self.label and self.label.canvas_id != -1:
                    self.map_widget.canvas.itemconfig(self.label.canvas_id, text=self.text)
            self.bind_commands()
        else:
            for shape in self._shapes:
                if shape.canvas_id != -1:
                    shape.delete(self.map_widget.canvas)

    def bind_commands(self):
        for shape in self._shapes:
            if shape.bindable and shape.canvas_id != -1:
                self.map_widget.canvas.tag_bind(shape.canvas_id, "<Enter>", self.mouse_enter)
                self.map_widget.canvas.tag_bind(shape.canvas_id, "<Leave>", self.mouse_leave)
                self.map_widget.canvas.tag_bind(shape.canvas_id, "<Button-1>", self.click)


class CC2DataMarker(ShapeMarker):
    def __init__(self, map_widget: "TkinterMapView", cc2obj: CC2MapItem):
        super(CC2DataMarker, self).__init__(map_widget,
                                            position=cc2obj.loc,
                                            text=cc2obj.text)
        self.object = cc2obj
        self.selected = False
        self._color = "#ff0000"
        self.on_hover_start: callable = None
        self.on_hover_end: callable = None

    def mouse_enter(self, event=None):
        super(Marker, self).mouse_enter(event)
        if self.on_hover_start:
            self.on_hover_start(self)

    def mouse_leave(self, event=None):
        super(Marker, self).mouse_leave(event)
        if self.on_hover_end:
            self.on_hover_end(self)

    @property
    def color(self) -> str:
        return self._color

    @color.setter
    def color(self, value: str):
        self._color = value

    def select(self):
        self.selected = True
        for shape in self._shapes:
            shape.select()

    def unselect(self):
        self.selected = False
        for shape in self._shapes:
            shape.unselect()

    def click(self, event=None):
        print(self.position)


class IslandMarker(CC2DataMarker):
    def __init__(self, map_widget: "TkinterMapView", cc2obj: Island, on_click: Optional[callable] = None):
        super(IslandMarker, self).__init__(map_widget, cc2obj)
        self.color = get_team_color(cc2obj.tile().team_control)
        self.command = on_click
        self.polygon = None
        tile = cast(Tile, self.object.object)
        # add the island polygon
        self.polygon = map_widget.set_polygon(
            [
                (self.object.loc[0] + tile.bounds.min.z / 1000, self.object.loc[1] + tile.bounds.min.x / 1000),
                (self.object.loc[0] + tile.bounds.min.z / 1000, self.object.loc[1] + tile.bounds.max.x / 1000),
                (self.object.loc[0] + tile.bounds.max.z / 1000, self.object.loc[1] + tile.bounds.max.x / 1000),
                (self.object.loc[0] + tile.bounds.max.z / 1000, self.object.loc[1] + tile.bounds.min.x / 1000),
            ],
            outline_color=self.color,
            border_width=1,
            fill_color=None,
        )

        # add the shape/icon
        production = CanvasShape(map_widget.canvas,
                                 map_widget.canvas.create_rectangle,
                                 -2, -2,
                                 2, 2,
                                 fill=self.color,
                                 width=1,
                                 outline=self.color,
                                 tag="island marker",
                                 )
        production.on_left_mouse = self.click
        self.label = CanvasShape(map_widget.canvas,
                                 map_widget.canvas.create_text,
                                 0, -3,
                                 text=self.text,
                                 fill="#990000",
                                 font=self.font,
                                 anchor=tkinter.S,
                                 tag="marker text"
                                 )
        self.add_shapes(production, self.label)

    def click(self, event=None):
        self.command(self)


class UnitMarker(CC2DataMarker):

    @property
    def unit(self) -> Unit:
        return cast(Unit, self.object)

    @property
    def size(self) -> float:
        v = self.unit.vehicle()
        if v.definition_index == VehicleTypes.Carrier.int:  # carrier
            return 1.5

        return 0.5

    def __init__(self, map_widget: TkinterMapView, cc2obj: Unit, on_click: Optional[callable] = None):
        super(UnitMarker, self).__init__(map_widget, cc2obj)
        self.color = get_team_color(cc2obj.vehicle().team_id)
        back = CanvasShape(map_widget.canvas,
                           map_widget.canvas.create_polygon,
                           -1 * self.size, 0,
                           0, -1 * self.size,
                           self.size, 0,
                           0, self.size,
                           fill="",
                           width=3,
                           outline="#000000",
                           tag="vehicle marker",
                           )
        unit = CanvasShape(map_widget.canvas,
                           map_widget.canvas.create_polygon,
                           -1 * self.size, 0,
                           0, -1 * self.size,
                           self.size, 0,
                           0, self.size,
                           fill="",
                           width=1,
                           outline=self.color,
                           tag="vehicle marker",
                           )

        self.add_shapes(back, unit)
