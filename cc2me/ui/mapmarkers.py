import tkinter
from abc import ABC, abstractmethod
from typing import Optional, Callable, List, cast, Union

from tkintermapview.canvas_path import CanvasPath
from tkintermapview.canvas_position_marker import CanvasPositionMarker
from tkintermapview import TkinterMapView
from .cc2constants import get_team_color
from .image_loader import load_icon
from .mapshapes import CanvasShape
from ..savedata.constants import VehicleType, TileTypes
from ..savedata.types.objects import MapItem, MapTile, MapVehicle, Spawn, LOC_SCALE_FACTOR, MapWaypoint
from .cc2memapview import CC2MeMapView


class Marker(CanvasPositionMarker, ABC):
    """An extensible marker"""

    def is_visible(self) -> bool:
        canvas_pos_x, canvas_pos_y = self.get_canvas_pos(self.position)
        return -50 < canvas_pos_x < self.map_widget.width + 50 and -50 < canvas_pos_y < self.map_widget.height + 70

    def draw(self, event=None):
        if not self.deleted:
            self.render(event)
            self.map_widget.manage_z_order()

    @abstractmethod
    def render(self, event=None):
        pass


class ShapeMarker(Marker, ABC):

    def __init__(self,
                 map_widget: "CC2MeMapView",
                 text: Optional[str] = None,
                 text_color: Optional[str] = "#652A22",
                 command: Optional[Callable] = None,
                 data: any = None,
                 zoom_scale: Optional[int] = 1,
                 ):
        super(ShapeMarker, self).__init__(
            map_widget,
            (0, 0),
            text=text,
            text_color=text_color,
            command=command,
            data=data)
        self.label: Optional[CanvasShape] = None
        self._shapes: List[CanvasShape] = []
        self._zoom_scale_factor = zoom_scale

    @property
    def shapes(self) -> List[CanvasShape]:
        return self._shapes

    def delete(self):
        super(ShapeMarker, self).delete()
        self.clear()

    def clear(self):
        for item in self.shapes:
            item.delete(self.map_widget.canvas)
        if self.label:
            self.label.delete(self.map_widget.canvas)

    def redraw(self):
        self.clear()
        self.render()
        self.map_widget.manage_z_order()

    def show_label(self) -> bool:
        return self.label is not None and self.map_widget.zoom > 4

    def add_shapes(self, *shapes: CanvasShape):
        for shape in shapes:
            self._shapes.append(shape)

    @property
    def zoom_scale(self) -> float:
        return self.map_widget.zoom * self._zoom_scale_factor

    def render(self, event=None):
        if self.is_visible():
            x, y = self.get_canvas_pos(self.position)
            for shape in self._shapes:
                if shape.canvas_id == -1:
                    shape.render(x, y, self.zoom_scale)
                shape.update(self.map_widget.canvas, x, y, self.zoom_scale)
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
                # anything bindable
                self.map_widget.canvas.tag_bind(shape.canvas_id, "<Enter>", self.mouse_enter)
                self.map_widget.canvas.tag_bind(shape.canvas_id, "<Leave>", self.mouse_leave)
                self.map_widget.canvas.tag_bind(shape.canvas_id, "<Button-1>", self.click)


class MapItemMarker(ShapeMarker):
    def __init__(self, map_widget: "TkinterMapView", mapitem: MapItem):
        super(MapItemMarker, self).__init__(map_widget,
                                            text=mapitem.text)
        self.mapitem = mapitem
        self.selected = False
        self._color = "#ff0000"
        self.on_hover_start: callable = None
        self.on_hover_end: callable = None
        self.hovering = False
        if mapitem:
            self.color = get_team_color(mapitem.team_owner)

    def render(self, event=None):
        self.update_shape_outline()
        super(MapItemMarker, self).render(event)

    @property
    def position(self) -> tuple:
        if self.mapitem:
            return self.mapitem.loc
        return 0, 0

    @position.setter
    def position(self, value):
        pass

    def move(self, lat: float, lon: float):
        self.mapitem.move(lat, lon)

    def click(self, event=None):
        super(MapItemMarker, self).click(event)

    def mouse_enter(self, event=None):
        self.hovering = True
        super(Marker, self).mouse_enter(event)
        if self.on_hover_start:
            self.on_hover_start(self)

    def mouse_leave(self, event=None):
        self.hovering = False
        super(Marker, self).mouse_leave(event)
        if self.on_hover_end:
            self.on_hover_end(self)

    @property
    def color(self) -> str:
        return self._color

    def set_color(self, value):
        self._color = value

    @color.setter
    def color(self, value: str):
        self.set_color(value)

    def select(self):
        self.selected = True
        for shape in self._shapes:
            shape.select()

    def unselect(self):
        self.selected = False
        for shape in self._shapes:
            shape.unselect()

    def update_shape_outline(self):
        # resync the shape outline if it has changed
        self.color = get_team_color(self.mapitem.team_owner)

        for shape in self.shapes:
            if shape.outline:
                if shape.outline != "#000000":
                    shape.outline = self.color
            if shape.fill:
                if isinstance(self.mapitem, Spawn):
                    pass
                else:
                    shape.fill = self.color


class TileMarker(MapItemMarker):
    ICONS = {
        TileTypes.Warehouse: "warehouse-island",
        TileTypes.Turrets: "turret-island",
        TileTypes.Surface_Units: "land-island",
        TileTypes.Air_Units: "air-island",
        TileTypes.Utility: "utility-island",
        TileTypes.Fuel: "fuel-island",
        TileTypes.Small_Munitions: "ammo-island",
        TileTypes.Large_Munitions: "large-ammo-island",
        TileTypes.Barges: "barge-island",
    }

    def get_icon(self):
        return load_icon(self.ICONS[self.island.island_type])

    def __init__(self, map_widget: "TkinterMapView", mapitem: MapTile, on_click: Optional[callable] = None):
        super(TileMarker, self).__init__(map_widget, mapitem)
        self.command = on_click

        self.icon = CanvasShape(map_widget.canvas,
                                map_widget.canvas.create_image,
                                0, 0,
                                image=self.get_icon(),
                                tags="icon"
                                )
        self.icon.on_left_mouse = self.click
        self.icon.bindable = True
        box = CanvasShape(map_widget.canvas,
                          map_widget.canvas.create_rectangle,
                          -2, -2,
                          2, 2,
                          fill=self.color,
                          width=1,
                          outline=self.color,
                          tag="island",
                          )
        box.bindable = True
        box.on_left_mouse = self.click
        self.label = CanvasShape(map_widget.canvas,
                                 map_widget.canvas.create_text,
                                 0, -3,
                                 text=self.text,
                                 fill="#990000",
                                 font=self.font,
                                 anchor=tkinter.S,
                                 tag="text"
                                 )
        self.add_shapes(self.icon, box, self.label)

        self.polygon = map_widget.canvas.create_polygon(
            *self.border_polygon_coords(),
            outline=self.color,
            width=1,
            fill="",
        )

    def border_polygon_coords(self):
        tile = self.island.tile()
        try:
            nw_x, nw_y = self.get_canvas_pos(
                (self.mapitem.loc[0] + tile.bounds.min.z / LOC_SCALE_FACTOR, self.mapitem.loc[1] + tile.bounds.min.x / LOC_SCALE_FACTOR))
            ne_x, ne_y = self.get_canvas_pos(
                (self.mapitem.loc[0] + tile.bounds.min.z / LOC_SCALE_FACTOR, self.mapitem.loc[1] + tile.bounds.max.x / LOC_SCALE_FACTOR))
            se_x, se_y = self.get_canvas_pos(
                (self.mapitem.loc[0] + tile.bounds.max.z / LOC_SCALE_FACTOR, self.mapitem.loc[1] + tile.bounds.max.x / LOC_SCALE_FACTOR))
            sw_x, sw_y = self.get_canvas_pos(
                (self.mapitem.loc[0] + tile.bounds.max.z / LOC_SCALE_FACTOR, self.mapitem.loc[1] + tile.bounds.min.x / LOC_SCALE_FACTOR))
            return [nw_x, nw_y, ne_x, ne_y, se_x, se_y, sw_x, sw_y]
        except ValueError as err:
            assert True
            raise

    def draw(self, event=None):
        super(TileMarker, self).draw(event)
        if self.polygon != -1:
            self.map_widget.canvas.coords(self.polygon, *self.border_polygon_coords())
            # ensure everything is on top of the polygon
            self.map_widget.canvas.tag_lower(self.polygon)

    def update_shape_outline(self):
        super().update_shape_outline()
        # update the icon if needed
        self.icon.kwargs["image"] = self.get_icon()

    @property
    def island(self) -> MapTile:
        return cast(MapTile, self.mapitem)


class WaypointMarker(MapItemMarker):
    def __init__(self, map_widget: TkinterMapView,
                 mapitem: MapWaypoint,
                 owner: MapVehicle,
                 vehicle_marker: "VehicleMarker",
                 on_click: Optional[callable] = None):
        super(WaypointMarker, self).__init__(map_widget, mapitem)
        self.size = 0.7
        self.owner = owner
        self.vehicle_marker = vehicle_marker
        self._color = "#cdcdcd"

        a = CanvasShape(map_widget.canvas,
                        map_widget.canvas.create_polygon,
                        -1 * self.size, -1 * self.size,
                        self.size, self.size,
                        fill="",
                        width=5,
                        outline=self.color,
                        tag="\\",
                        )
        b = CanvasShape(map_widget.canvas,
                        map_widget.canvas.create_polygon,
                        -1 * self.size, self.size,
                        self.size, -1 * self.size,
                        fill="",
                        width=5,
                        outline=self.color,
                        tag="//",
                        )

        self.add_shapes(a, b)

    def set_color(self, value):
        pass

    def get_vehicle(self) -> MapVehicle:
        return self.owner

    @property
    def zoom_scale(self) -> float:
        return 5.2

    def render(self, event=None):
        super().render(event=event)


class VehicleMarker(MapItemMarker):

    @property
    def unit(self) -> MapVehicle:
        return cast(MapVehicle, self.mapitem)

    @property
    def size(self) -> float:
        v = self.unit.vehicle()
        if v is not None:
            if v.definition_index == VehicleType.Carrier.int:  # carrier
                return 1.5

        return 0.5

    def __init__(self, map_widget: TkinterMapView, mapitem: MapVehicle, on_click: Optional[callable] = None):
        super(VehicleMarker, self).__init__(map_widget, mapitem)
        self.waypoint_path = None
        self.waypoints = []
        # fill the middle for spawns
        fill = ""
        if isinstance(mapitem, Spawn):
            fill = "white"

        back = CanvasShape(map_widget.canvas,
                           map_widget.canvas.create_polygon,
                           -1 * self.size, 0,
                           0, -1 * self.size,
                           self.size, 0,
                           0, self.size,
                           fill=fill,
                           width=3,
                           outline="#000000",
                           tag="unit",
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
                           tag="unit",
                           )

        self.add_shapes(back, unit)

    def update_waypoints(self, start_hover=None, end_hover=None, command=None) -> None:
        path_points = [self.position]
        unit = self.unit

        for wpt in self.waypoints:
            self.map_widget.delete(wpt)
        self.waypoints.clear()

        if self.waypoint_path is not None:
            self.map_widget.delete(self.waypoint_path)
            self.waypoint_path = None

        for wpt in unit.vehicle().waypoints:
            wpm = WaypointMarker(self.map_widget, MapWaypoint(unit, wpt), unit, self)
            wpm.command = command
            wpm.on_hover_start = start_hover
            wpm.on_hover_end = end_hover
            self.waypoints.append(wpm)
            path_points.append(wpm.position)
            self.map_widget.add_marker(wpm)

        if len(path_points) > 1:
            map_path: CanvasPath = self.map_widget.set_path(path_points)
            self.waypoint_path = map_path
