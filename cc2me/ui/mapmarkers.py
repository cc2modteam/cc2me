from abc import ABC, abstractmethod
from typing import Optional, Callable, List

from tkintermapview.canvas_position_marker import CanvasPositionMarker

from cc2me.savedata.types.objects import CC2MapItem, Island
from cc2me.ui.cc2memapview import get_team_color

from cc2me.ui.mapshapes import CanvasShape


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
        self._shapes: List[CanvasShape] = []
        self._zoom_scale_factor = zoom_scale

    def add_shape(self, shape: CanvasShape):
        self._shapes.append(shape)

    def render(self, event=None):
        if self.is_visible():
            x, y = self.get_canvas_pos(self.position)
            for shape in self._shapes:
                if shape.canvas_id == -1:
                    shape.render(x, y, self.map_widget.zoom * self._zoom_scale_factor)
                shape.update(self.map_widget.canvas, x, y, self.map_widget.zoom * self._zoom_scale_factor)
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


class IslandMarker(CC2DataMarker):
    def __init__(self, map_widget: "TkinterMapView", cc2obj: Island):
        super(IslandMarker, self).__init__(map_widget, cc2obj)
        self.marker_color_outside = get_team_color(cc2obj.tile().team_control)
        # add the shape
        self.add_shape(
            CanvasShape(map_widget.canvas.create_rectangle,
                        -2, -2,
                        2, 2,
                        fill=self.marker_color_outside,
                        width=1,
                        outline=self.marker_color_outside,
                        tag="island marker"
                        )
        )