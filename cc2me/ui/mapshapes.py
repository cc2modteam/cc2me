import tkinter
from typing import List, Optional

from tkintermapview.canvas_path import CanvasPath


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
        self.outline = kwargs.get("outline", None)
        self.fill = kwargs.get("fill", None)
        self._normal_outline_color = None

    def update_colors(self):
        if "fill" in self.kwargs:
            if self.fill:
                self.canvas.itemconfig(self.canvas_id, fill=self.fill)

        if "outline" in self.kwargs:
            if self.outline != "#000000":
                if self.outline:
                    self.canvas.itemconfig(self.canvas_id, outline=self.outline)
                else:
                    self.canvas.itemconfig(self.canvas_id, outline="")

                if self.selected:
                    self.canvas.itemconfig(self.canvas_id, outline=self.selected_outline_color)

    def select(self):
        if not self.selected:
            self.selected = True
            self.update_colors()

    def unselect(self):
        if self.selected:
            self.selected = False
            self.update_colors()

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
            args = dict(self.kwargs)
            if self.outline:
                args["outline"] = self.outline
            if self.fill:
                args["fill"] = self.fill
            self.canvas_id = self.func(*coords, **args)

    def update(self, canvas: tkinter.Canvas, x: float, y: float, zoom: float):
        if self.canvas_id != -1:
            coords = self.get_coords(x, y, zoom)
            canvas.coords(self.canvas_id, *coords)
            canvas.tag_bind(self.canvas_id, "<Button-1>", self.on_left_mouse)
            self.update_colors()

    def delete(self, canvas: tkinter.Canvas):
        if self.canvas_id != -1:
            canvas.delete(self.canvas_id)
            self.canvas_id = -1


class CustomCanvasPath(CanvasPath):

    def __init__(self, *args, width=1, **kwargs, ):
        super().__init__(*args, **kwargs)
        self.width = width

    def draw(self, move=False):
        super().draw(move=move)
        if self.canvas_line is not None:
            self.map_widget.canvas.delete(self.canvas_line)
            self.canvas_line = self.map_widget.canvas.create_line(self.canvas_line_positions,
                                                                  width=self.width, fill=self.path_color,
                                                                  capstyle=tkinter.ROUND, joinstyle=tkinter.ROUND,
                                                                  tag="path")