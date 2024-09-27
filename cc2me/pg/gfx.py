"""Rendering and common graphics"""
import pygame
from typing import List


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