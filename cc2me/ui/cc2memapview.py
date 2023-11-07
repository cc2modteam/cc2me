import tkinter
from tkinter import Event
from typing import Tuple, Callable, Optional, Any, List

from PIL.ImageTk import PhotoImage, Image
from tkintermapview import TkinterMapView
from tkintermapview.canvas_path import CanvasPath
from tkintermapview.canvas_position_marker import CanvasPositionMarker

from .cc2constants import TILE_SIZE
from .mapshapes import CustomCanvasPath
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
                                           max_zoom=16,
                                           )
        self.selection_start = None
        self.canvas.configure(bg="#000050")
        self.on_select_box: Optional[Any, Callable[[Tuple[float, float], Tuple[float, float]], None]] = None
        self.selection_mode = False
        self.selection_box: Optional[Tuple[float, float, float, float]] = None
        self.selection_rect: Optional[int] = None
        self.selected_markers: List[CanvasPositionMarker] = []
        self.mouse_left_is_down = False
        self.on_mouse_drag: Optional[Callable[[Event], bool]] = None
        self.mouse_delta = [0, 0]
        self.last_mouse_move_position: Optional[Tuple] = None
        self.on_mouse_release: Optional[Callable] = None

    def set_path(self, position_list: list, **kwargs) -> CanvasPath:
        path = CustomCanvasPath(self, position_list, width=1, **kwargs)
        path.draw()
        self.canvas_path_list.append(path)
        return path

    def manage_z_order(self):
        super(CC2MeMapView, self).manage_z_order()
        try:
            self.canvas.tag_lower("island", "unit")
            self.canvas.tag_lower("path")
            self.canvas.tag_raise("text")
            self.canvas.tag_raise("icon")
        except tkinter.TclError:
            pass

    def set_zoom(self, zoom, relative_pointer_x: float = 0.5, relative_pointer_y: float = 0.5):
        logger.info(f"zoom {zoom}")
        super().set_zoom(zoom, relative_pointer_x, relative_pointer_y)

    def set_mouse_arrow(self):
        self.canvas.config(cursor="arrow")

    def set_mouse_move(self):
        self.canvas.config(cursor="fleur")

    def set_mouse_choose(self):
        self.canvas.config(cursor="hand2")

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
        if self.last_mouse_move_position is not None:
            self.mouse_delta[0] = event.x - self.last_mouse_move_position[0]
            self.mouse_delta[1] = event.y - self.last_mouse_move_position[1]
        self.last_mouse_move_position = (event.x, event.y)

        if self.on_mouse_drag is not None:
            if self.on_mouse_drag(event):
                return

        if not self.selection_mode:
            if self.last_mouse_down_position is not None:
                super(CC2MeMapView, self).mouse_move(event)
        else:
            # update the drag box
            self.canvas.coords(self.selection_rect,
                               *[self.selection_start.x, self.selection_start.y,
                                 event.x, event.y])

    def mouse_click(self, event):
        self.mouse_left_is_down = True
        if self.selection_mode:
            self.selection_start = event
            self.selection_rect = self.canvas.create_rectangle(event.x, event.y, event.x + 1, event.y + 1,
                                                               fill="",
                                                               outline="#eeeeee",
                                                               )
        else:
            super(CC2MeMapView, self).mouse_click(event)

    def mouse_release(self, event):
        self.mouse_left_is_down = False
        if self.on_mouse_release:
            self.on_mouse_release()
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
