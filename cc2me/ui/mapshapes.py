import tkinter
from typing import List


class CanvasShape:
    def __init__(self, func: callable, *coords, **kwargs):
        self.func = func
        self.coords = coords
        self.kwargs = kwargs
        self.canvas_id = -1
        self.bindable = True
        self.min_zoom = 1

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

    def delete(self, canvas: tkinter.Canvas):
        if self.canvas_id != -1:
            canvas.delete(self.canvas_id)
            self.canvas_id = -1

