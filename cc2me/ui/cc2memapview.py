import tkinter
from random import randrange
from typing import Tuple, Dict, Callable

from PIL.ImageTk import PhotoImage, Image
from tkintermapview import TkinterMapView
from tkintermapview.canvas_position_marker import CanvasPositionMarker
from ..savedata.logging import logger
from ..savedata.types.objects import CC2MapItem, Island

TILE_SIZE = 256

TEAM_COLORS = {
    0: "#990000",
    1: "#0066FF",
    2: "#FFCC00",
    3: "#66FF33",
    4: "#FF00FF",
}


def get_team_color(team: int) -> str:
    if team not in TEAM_COLORS:
        r, g, b = randrange(0, 255), randrange(0, 255), randrange(0, 255)
        TEAM_COLORS[team] = "#{:02X}{:02X}{:02X}".format(r, g, b)
    return TEAM_COLORS[team]


def generate_sea_tile() -> PhotoImage:
    img = Image.new("RGB", (TILE_SIZE, TILE_SIZE), (0, 0, 50))
    return PhotoImage(img)


class CC2MeMapView(TkinterMapView):

    sea_tile_image: PhotoImage = None

    def __init__(self, width: int = 300,
                 height: int = 200,
                 corner_radius: int = 0):
        super(CC2MeMapView, self).__init__(width=width,
                                           height=height,
                                           corner_radius=corner_radius,
                                           max_zoom=10,
                                           )

    def set_zoom(self, zoom: int, relative_pointer_x: float = 0.5, relative_pointer_y: float = 0.5):
        logger.info(f"zoom {zoom}")
        super().set_zoom(zoom, relative_pointer_x, relative_pointer_y)

    def request_image(self, zoom: int, x: int, y: int, db_cursor=None) -> PhotoImage:
        return self.empty_tile_image
        #if self.sea_tile_image is None:
        #    self.sea_tile_image = generate_sea_tile()
        #return self.sea_tile_image

    def add_marker(self, marker: CanvasPositionMarker):
        marker.draw()
        self.canvas_marker_list.append(marker)
        return marker


class Marker(CanvasPositionMarker):
    """A square marker that scales with zoom"""
    def __init__(self,
                 map_widget: "TkinterMapView",
                 position: tuple,
                 text: str = None,
                 text_color: str = "#652A22",
                 command: Callable = None,
                 data: any = None,
                 box_width: int = 64,
                 ):
        super(Marker, self).__init__(map_widget, position,
                                     text=text,
                                     text_color=text_color,
                                     command=command,
                                     data=data)
        self.shape_coords: Dict[str, Tuple] = {}
        self.shapes: Dict[str, int] = {}
        self.box_width = box_width

    def scale(self) -> float:
        return self.map_widget.zoom * self.box_width / 10

    def is_visible(self) -> bool:
        canvas_pos_x, canvas_pos_y = self.get_canvas_pos(self.position)
        return -50 < canvas_pos_x < self.map_widget.width + 50 and -50 < canvas_pos_y < self.map_widget.height + 70

    def update_coords(self):

        canvas_pos_x, canvas_pos_y = self.get_canvas_pos(self.position)
        self.shape_coords["box"] = (
            canvas_pos_x - self.scale()/2, canvas_pos_y - self.scale()/2,
            canvas_pos_x + self.scale()/2, canvas_pos_y + self.scale()/2
        )
        self.shape_coords["text"] = (
            canvas_pos_x, canvas_pos_y - 26
        )

        if "box" in self.shapes:
            self.map_widget.canvas.coords(self.shapes["box"], *self.shape_coords["box"])
        if "text" in self.shapes:
            self.map_widget.canvas.coords(self.shapes["text"], *self.shape_coords["text"])

    def create_shapes(self):
        if len(self.shapes):
            return
        coords = self.shape_coords["box"]
        shape = self.map_widget.canvas.create_rectangle(*coords,
                                                        fill=self.marker_color_outside,
                                                        width=2,
                                                        outline=self.marker_color_outside,
                                                        tag="marker")
        self.shapes["box"] = shape

        if self.command is not None:
            self.map_widget.canvas.tag_bind(self.shapes["box"], "<Enter>", self.mouse_enter)
            self.map_widget.canvas.tag_bind(self.shapes["box"], "<Leave>", self.mouse_leave)
            self.map_widget.canvas.tag_bind(self.shapes["box"], "<Button-1>", self.click)

    def draw(self, event=None):
        if not self.deleted:
            if self.is_visible():
                self.update_coords()
                self.create_shapes()

                if self.map_widget.zoom > 5:
                    if self.text is not None:
                        if "text" not in self.shapes:
                            self.shapes["text"] = self.map_widget.canvas.create_text(
                                *self.shape_coords["text"],
                                anchor=tkinter.S,
                                text=self.text,
                                fill=self.text_color,
                                font=self.font,
                                tag=("marker", "marker_text"))

                            if self.command is not None:
                                self.map_widget.canvas.tag_bind(self.shapes["text"], "<Enter>", self.mouse_enter)
                                self.map_widget.canvas.tag_bind(self.shapes["text"], "<Leave>", self.mouse_leave)
                                self.map_widget.canvas.tag_bind(self.shapes["text"], "<Button-1>", self.click)
                        else:
                            self.map_widget.canvas.itemconfig(self.shapes["text"], text=self.text)
                    else:
                        if "text" in self.shapes:
                            self.map_widget.canvas.delete(self.shapes["text"])

            else:
                for item in self.shapes:
                    self.map_widget.canvas.delete(self.shapes[item])
                self.shapes.clear()
                self.map_widget.manage_z_order()


class CC2DataMarker(Marker):
    def __init__(self, map_widget: "TkinterMapView", cc2obj: CC2MapItem):
        super(CC2DataMarker, self).__init__(map_widget,
                                            position=cc2obj.loc,
                                            text=cc2obj.text)
        self.object = cc2obj


class IslandMarker(CC2DataMarker):
    def __init__(self, map_widget: "TkinterMapView", cc2obj: Island):
        super(IslandMarker, self).__init__(map_widget, cc2obj)
        self.marker_color_outside = get_team_color(cc2obj.tile().team_control)

