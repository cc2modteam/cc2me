from tkinter import Event
from typing import Tuple, Callable, Optional, Any

from PIL.ImageTk import PhotoImage, Image
from tkintermapview import TkinterMapView
from tkintermapview.canvas_position_marker import CanvasPositionMarker

from .cc2constants import TILE_SIZE
from ..savedata.logging import logger


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
        self.selection_start = None
        self.canvas.configure(bg="#000050")
        self.on_select_box: Optional[Any, Callable[[Tuple[float, float], Tuple[float, float]], None]] = None
        self.selection_mode = False
        self.selection_box: Optional[Tuple[float, float, float, float]] = None
        self.selection_rect: Optional[int] = None

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

    def mouse_move(self, event):
        if not self.selection_mode:
            super(CC2MeMapView, self).mouse_move(event)
        else:
            # update the drag box
            self.canvas.coords(self.selection_rect,
                               *[self.selection_start.x, self.selection_start.y,
                                 event.x, event.y])

    def mouse_click(self, event):
        if self.selection_mode:
            self.selection_start = event
            self.selection_rect = self.canvas.create_rectangle(event.x, event.y, event.x + 1, event.y + 1,
                                                               fill="",
                                                               outline="#eeeeee",
                                                               )
        else:
            super(CC2MeMapView, self).mouse_click(event)

    def mouse_release(self, event):
        if self.selection_mode:
            if self.on_select_box:
                self.on_select_box(
                    self.selection_mode,
                    self.convert_canvas_coords_to_decimal_coords(self.selection_start.x, self.selection_start.y),
                    self.convert_canvas_coords_to_decimal_coords(event.x, event.y))
            self.selection_mode = None
            self.canvas.delete(self.selection_rect)
            self.selection_rect = None
        else:
            super(CC2MeMapView, self).mouse_release(event)
