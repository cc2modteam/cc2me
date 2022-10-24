import tkinter
from typing import List, Optional


class CanvasShape:
    def __init__(self, canvas: tkinter.Canvas, func: callable, *coords, **kwargs):
        self.canvas = canvas
        self.func = func
        self.coords = coords
        self.kwargs = kwargs
        self.canvas_id = -1
        self.bindable = True
        self.min_zoom = 1
        self.on_left_mouse: Optional[callable] = None
        self.selected = False
        self.selected_outline_color = "#ffffff"
        self._normal_outline_color = None

    def select(self):
        if not self.selected:
            self.selected = True
            self._normal_outline_color = self.kwargs.get("outline", None)
            if self._normal_outline_color is not None:
                self.kwargs["outline"] = self.selected_outline_color
                self.canvas.itemconfig(self.canvas_id, outline=self.kwargs["outline"])

    def unselect(self):
        if self.selected:
            self.selected = False
            if self._normal_outline_color is not None:
                self.kwargs["outline"] = self._normal_outline_color
                self._normal_outline_color = None
                self.canvas.itemconfig(self.canvas_id, outline=self.kwargs["outline"])

    def get_coords(self, x: float, y: float, zoom: float) -> List[float]:
        coords = []
        for i in range(0, len(self.coords), 2):
            coords.append(x + self.coords[i] * zoom)
            coords.append(y + self.coords[i + 1] * zoom)
        return coords

    def render(self, x: float, y: float, zoom: float) -> None:
        if zoom < self.min_zoom:
            return
        coords = self.get_coords(x, y, zoom)
        if self.canvas_id == -1:
            self.canvas_id = self.func(*coords, **self.kwargs)

    def update(self, canvas: tkinter.Canvas, x: float, y: float, zoom: float):
        if self.canvas_id != -1:
            coords = self.get_coords(x, y, zoom)
            canvas.coords(self.canvas_id, *coords)
            canvas.tag_bind(self.canvas_id, "<Button-1>", self.on_left_mouse)

    def delete(self, canvas: tkinter.Canvas):
        if self.canvas_id != -1:
            canvas.delete(self.canvas_id)
            self.canvas_id = -1

