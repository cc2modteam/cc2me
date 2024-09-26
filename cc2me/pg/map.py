"""
Render the CC2 map as a pan/zoom surface similar to the game
"""
import pygame
from typing import Optional, Tuple, List

from pandas.io.formats.format import return_docstring
from pygame.math import clamp

from ..savedata.types.save import CC2XMLSave, Tile, Vehicle
from ..ui.cc2constants import get_team_color


class MapRenderer:

    def __init__(self, surface: pygame.Surface):
        self.surface = surface
        self.savedata: Optional[CC2XMLSave] = None
        # east-west, south-north
        self.origin = (0, 0)
        self.camera_size = 0
        self.reset_view()
        self.grid_major = 4000
        self.grid_minor = 1000
        self.grid_color = (0, 0, 128, 64)
        self.pan = False
        self.hover_items = []
        self._tiles = []
        self._vehicles = []

    @property
    def tiles(self) -> List[Tile]:
        return list(self._tiles)

    @property
    def vehicles(self) -> List[Vehicle]:
        return list(self._vehicles)


    def reset_view(self):
        self.origin = (0, 0)
        self.camera_size = 50000 # 50km wide


    def load(self, save: CC2XMLSave):
        del self.savedata
        self.savedata = save
        self.reset_view()
        self._tiles.clear()
        for tile in self.savedata.tiles:
            self._tiles.append(tile)
        for vehicle in self.savedata.vehicles:
            self._vehicles.append(vehicle)

    def _world_to_screen_vha(self, world: Tuple[float, float]) -> Tuple[float, float, float]:
        screen_w = self.surface.get_width()
        screen_h = self.surface.get_height()
        aspect = screen_w / screen_h

        view_w = self.camera_size
        view_h = self.camera_size
        if aspect > 1:
            view_w = view_w * aspect
        else:
            view_h = view_h / aspect
        return view_w, view_h, aspect

    def world_to_screen_scale(self, world: Tuple[float, float]) -> Tuple[float, float]:
        cam_x = self.surface.get_width() / self.camera_size
        return world[0] * cam_x, -world[1] * cam_x

    def world_to_screen(self, world: Tuple[float, float]) -> Tuple[float, float]:
        screen_w = self.surface.get_width()
        screen_h = self.surface.get_height()
        view_w, view_h, aspect = self._world_to_screen_vha(world)
        view_x = (world[0] - self.origin[0]) / view_w
        view_y = (self.origin[1] - world[1]) / view_h

        return round(view_x * screen_w), round(view_y * screen_h)

    def screen_to_world_scale(self, screen: Tuple[float, float]) -> Tuple[float, float]:
        screen_w = self.surface.get_width()
        screen_h = self.surface.get_height()
        aspect = screen_w / screen_h

        view_x = screen[0] / screen_w
        view_y = screen[1] / screen_h

        return view_x * self.camera_size * aspect, -view_y * self.camera_size

    def screen_to_world(self, screen: Tuple[float, float]) -> Tuple[float, float]:
        world_x, world_y = self.screen_to_world_scale(screen)

        return world_x + self.origin[0], world_y + self.origin[1]


    def render_grid(self):
        """Draw the background grid lines"""
        height = self.surface.get_height()
        width = self.surface.get_width()
        _, world_y = self.screen_to_world((0, height))
        grid_start = (self.origin[0] - 3, world_y + 3)

        # calc map position of the first north and west grid we will draw
        x = int(grid_start[0] / self.grid_major) * self.grid_major
        y = int(grid_start[1] / self.grid_major) * self.grid_major

        # scale for the camera size
        screen_x = 0
        screen_y = 0
        h_x = x
        h_y = y

        while screen_x < width:
            screen_x, screen_y = self.world_to_screen((h_x, y))
            pygame.draw.line(self.surface, self.grid_color,
                             (screen_x, 0),
                             (screen_x, height))
            h_x += self.grid_major

        while screen_y > 0:
            screen_x, screen_y = self.world_to_screen((x, h_y))
            pygame.draw.line(self.surface, self.grid_color,
                             (0, screen_y),
                             (width, screen_y))
            h_y += self.grid_major

    def event(self, event: pygame.event.Event):
        if event:
            if event.type == pygame.MOUSEWHEEL:
                if event.y != 0:
                    self.zoom(event.y)
            if event.type == pygame.MOUSEBUTTONDOWN:
                b1, _, _ = pygame.mouse.get_pressed()
                if b1:
                    self.mouse_down()
            if event.type == pygame.MOUSEBUTTONUP:
                b1, _, _ = pygame.mouse.get_pressed()
                if not b1:
                    self.mouse_up()
            if event.type == pygame.MOUSEMOTION:
                self.mouse_move()

    def mouse_down(self):
        self.pan = True

    def mouse_up(self):
        self.pan = False

    def mouse_move(self):
        if self.pan:
            dx, dy = pygame.mouse.get_rel()
            self.pan_camera(-dx, -dy)


    def draw(self):
        """Render the portion of the map in view"""
        self.hover_items = self.under_mouse()
        self.render_grid()
        self.render_tiles()
        self.render_units()

    def render_tiles(self):
        if self.savedata:
            for tile in self.tiles:
                pos = tile.world_position
                bounds = tile.bounds

                color = pygame.Color(get_team_color(tile.team_control))
                if tile in self.hover_items:
                    color = (255, 255, 255, 255)
                poly = [
                    self.world_to_screen((pos.x + bounds.min.x, pos.z + bounds.min.z)),
                    self.world_to_screen((pos.x + bounds.max.x, pos.z + bounds.min.z)),
                    self.world_to_screen((pos.x + bounds.max.x, pos.z + bounds.max.z)),
                    self.world_to_screen((pos.x + bounds.min.x, pos.z + bounds.max.z)),
                ]
                pygame.draw.polygon(self.surface, color, poly, width=1)


    def render_units(self):
        if self.savedata:
            for vehicle in self.vehicles:
                color = pygame.Color(get_team_color(vehicle.team_id))
                if vehicle in self.hover_items:
                    color = (255, 255, 255, 255)
                pos = vehicle.loc
                screen = self.world_to_screen((pos.x, pos.z))
                pygame.draw.circle(self.surface, color, screen, 6, width=1)


    def under_mouse(self) -> List:
        found = []
        if self.savedata:
            mouse = pygame.mouse.get_pos()

            for unit in self.vehicles:
                # get units within 10 screen pixels of this mouse point
                screen = self.world_to_screen((unit.loc.x, unit.loc.z))
                if screen[0] - 5 < mouse[0] < screen[0] + 5:
                    if screen[1] - 5 < mouse[1] < screen[1] + 5:
                        found.append(unit)

            world_x, world_y = self.screen_to_world(mouse)
            for tile in self.tiles:
                # get tile under the mouse
                if tile.loc.x + tile.bounds.min.x < world_x < tile.loc.x + tile.bounds.max.x:
                    if tile.loc.z + tile.bounds.min.z < world_y < tile.loc.z + tile.bounds.max.z:
                        found.append(tile)
                        break

        return found




    def zoom(self, amount: int):
        if amount:
            amount = int(clamp(amount, -4, 4))
            self.camera_size += 2000 * -amount
            self.camera_size = max(self.camera_size, 1000)
            self.camera_size = min(self.camera_size, 200000)

    def pan_camera(self, screen_dx, screen_dy):
        screen_dx = clamp(screen_dx, -30, 30)
        screen_dy = clamp(screen_dy, -30, 30)
        world = self.screen_to_world_scale((screen_dx, screen_dy))
        x = int(self.origin[0] + world[0])
        y = int(self.origin[1] + world[1])
        self.origin = (x, y)
