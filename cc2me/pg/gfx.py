"""Rendering and common graphics"""
import pygame
from abc import ABC, abstractmethod
from uuid import uuid4
from typing import List, Optional, Union, Tuple
from collections.abc import Callable

EventHandler = Optional[Callable[[], bool]]

class Point:

    @classmethod
    def new(cls, x: float, y: float) -> "Point":
        p = cls()
        p.x = x
        p.y = y
        return p

    def __init__(self, pt: Union[None, Tuple[float, float], List, "Point"] = None):
        if pt is None:
            pt = [0, 0]
        self.x = pt[0]
        self.y = pt[1]

    def __getitem__(self, item):
        if item == 0:
            return self.x
        elif item == 1:
            return self.y
        raise KeyError()

    def __setitem__(self, key, value):
        if key == 0:
            self.x = value
        elif key == 1:
            self.y = value
        raise KeyError()


class GfxContext:

    def __init__(self, surface: pygame.Surface, fonts: List[pygame.font.Font]):
        self.surface = surface
        self.fonts = fonts
        self.font_x_offset = 1
        self.font_y_offset = -1

    @property
    def aspect(self) -> float:
        return self.w / self.h

    @property
    def w(self) -> int:
        return self.surface.get_width()

    @property
    def h(self) -> int:
        return self.surface.get_height()

    def update_ui_rectangle(self, x: int, y: int, w: int, h: int, col):
        pygame.draw.rect(self.surface, col,
                         pygame.Rect(x, y, w, h))

    def update_ui_rectangle_outline(self, x, y, w, h, col):
        pygame.draw.rect(self.surface, col,
                         pygame.Rect(x, y, w, h), 1)

    def update_ui_text(self, x: float, y: float, text: str, w: int, j: int, col, rot=0):
        lpad = 0
        span = int(w / 8)
        length = len(text)
        if j == 1:
            # center
            lpad = int((span - length) / 2)
        if j == 2:
            # right
            lpad = int(span - length)
        lpad = lpad * 4
        text = f"{' '*lpad}{text}"
        surf = self.fonts[0].render(text, False, col)

        if rot > 0:
            rotated = pygame.transform.rotate(surf, -90 * rot)
            new_rect = rotated.get_rect(bottomleft=surf.get_rect(topleft=(x + self.font_x_offset - 2, y + self.font_y_offset)).topleft)
        else:
            rotated = surf
            new_rect = rotated.get_rect(topleft=(x + self.font_x_offset, y + self.font_y_offset))
        self.surface.blit(rotated, new_rect)


class Widget(ABC):
    def __init__(self,
                 ctx: Optional[GfxContext] = None,
                 parent: Optional["Widget"] = None,
                 pos: Optional[Point] = None,
                 size: Optional[Point] = None,
                 ):
        self._ident = uuid4()
        self.parent = parent
        self.hover = True
        self.ctx: Optional[GfxContext] = None
        self.children: List[Widget] = []
        if ctx is None:
            if parent is not None:
                ctx = parent.ctx
        if pos is None:
            pos = Point()
        if size is None:
            size = Point()
        self.ctx = ctx
        self.pos = pos
        self.size = size
        self.padding = Point()
        if parent:
            parent.children.append(self)

        self.on_mouseover: EventHandler = None
        self.on_mouseup: EventHandler = None

    def max_size(self) -> Point:
        if self.parent:
            return self.max_size()
        return Point(self.size)

    def add_child(self, child: "Widget") -> "Widget":
        self.children.append(child)
        return child

    @property
    def ident(self) -> uuid4:
        return self._ident

    def __hash__(self):
        return hash(self.ident)

    def get_hover(self, screen: Point) -> Optional["Widget"]:
        """Get the deepest widget under our mouse"""
        found = None
        for child in self.children:
            found = child.get_hover(screen)
            if found:
                break
        if not found and self.hover:
            if self.size.x > 0 and self.size.y > 0:
                if self.pos.x < screen.x < self.pos.x + self.size.x:
                    if self.pos.y < screen.y < self.pos.y + self.size.y:
                        found = self
        return found

    @abstractmethod
    def draw(self):
        pass

    def mouseup(self) -> bool:
        if self.on_mouseup:
            return self.on_mouseup()
        return False

    def mouseover(self) -> bool:
        if self.on_mouseover:
            return self.on_mouseover()
        return False

    def event(self, event: pygame.event) -> bool:
        for child in self.children:
            handled = child.event(event)
            if handled:
                return True
        if self.hover:
            if self == self.get_hover(Point(pygame.mouse.get_pos())):
                if event.type == pygame.MOUSEBUTTONUP:
                    return self.mouseup()
                if event.type == pygame.MOUSEMOTION:
                    return self.mouseover()
        return False


class Frame(Widget):
    def __init__(self, ctx: GfxContext, pos: Point, size: Point, border: Optional[pygame.Color] = None, background: Optional[pygame.Color] = None):
        super().__init__(ctx=ctx, pos=pos, size=size)
        self.border: Optional[pygame.Color] = border
        self.background_color: Optional[pygame.Color] = background

    def draw(self):
        if self.background_color:
            self.ctx.update_ui_rectangle(self.pos.x, self.pos.y, self.size.x, self.size.y, self.background_color)
        if self.border:
            self.ctx.update_ui_rectangle_outline(self.pos.x, self.pos.y, self.size.x, self.size.y, self.border)
        for child in self.children:
            child.draw()

class Label(Widget):
    def __init__(self, parent: Widget, pos: Point, text: str, color: pygame.Color):
        super().__init__(parent=parent, pos=pos, size=Point.new(6 * len(text), 7))
        self.text = text
        self.color = color

    def draw(self):
        self.ctx.update_ui_text(self.pos.x, self.pos.y, self.text, self.size.x, 0, self.color)
