"""
Render the CC2 map as a pan/zoom surface similar to the game
"""

import pygame
from typing import Optional, Tuple, List, Union, cast
from pygame.math import clamp
from pygame_gui.core import UIElement
from pygame_gui.ui_manager import UIManager
from pygame_gui.elements import UIWindow, UILabel

from .gfx import GfxContext
from ..savedata.types.save import CC2XMLSave, Tile, Vehicle, VehicleSpawn
from ..savedata.types.objects import MapItem, MapTile, MapVehicle, Spawn, Carrier, Barge, InventoryMixin
from ..savedata.constants import get_biome_name, InventoryIndex, VehicleType
from ..ui.cc2constants import get_team_color


class UnitWindow(UIWindow):
    def __init__(self, position, ui_manager):
        super().__init__(pygame.Rect(position, (220, 450)), ui_manager,
                         window_display_title="",
                         object_id="#unit_window",
                         draggable=False,
                         resizable=False,
                         )
        self._unit: Optional[MapItem] = None
        self.props: List[UIElement] = []

    def get_last_prop_y(self) -> int:
        h = 0
        for prop in self.props:
            h += prop.get_relative_rect().height
        return h

    def add_property_string(self, label_text: str, value_text: str):
        start_y = self.get_last_prop_y()
        label = UILabel(relative_rect=pygame.Rect((5, start_y), (-1, 24)),
                             text=f"{label_text}:",
                             container=self,
                             anchors={
                                 "left": "left",
                                 "top": "top",
                                 "bottom": "bottom",
                                 "right": "right",
                             },
                             manager=self.ui_manager)
        text = UILabel(relative_rect=pygame.Rect((15, start_y + label.get_relative_rect().height + 2), (-1, 24)),
                             text=f"{value_text}",
                             container=self,
                             anchors={
                                 "left": "left",
                                 "top": "top",
                                 "bottom": "bottom",
                                 "right": "right",
                             },
                             manager=self.ui_manager)
        self.props.extend([label, text])

    def show(self):
        super().show()
        self.close_window_button.hide()

    def on_close_window_button_pressed(self):
        self.hide()

    @property
    def unit(self) -> Optional[MapItem]:
        return self._unit

    @unit.setter
    def unit(self, unit: Optional[MapItem]):
        self._unit = unit
        for p in self.props:
            p.kill()
        self.props.clear()
        if unit is not None:
            if isinstance(unit, MapVehicle):
                self.add_property_string("id", str(unit.vehicle().id))
                self.add_property_string("type", unit.vehicle_type.name)
                team = unit.team_owner
                self.add_property_string("team", str(team))
                hp = unit.hitpoints
                self.add_property_string("hitpoints", str(hp))

            elif isinstance(unit, MapTile):
                tile = cast(MapTile, unit)
                self.add_property_string("id", str(tile.tile().id))
                self.add_property_string("type", tile.island_type.name)
                self.add_property_string("team", str(tile.team_owner))
                self.add_property_string("name", f"{tile.name} ({tile.shields})")
                self.add_property_string("size", f"{tile.size/1000:2.1f}km")
                self.add_property_string("biome", get_biome_name(tile.biome))

            if unit.has_inventory() and isinstance(unit, InventoryMixin):
                container = cast(InventoryMixin, unit)
                content = container.get_inventory_content()
                inventory_weight = unit.get_inventory().total_weight
                self.add_property_string("cargo", f"{inventory_weight:6d} kg")



class MapRenderer:

    def __init__(self, gfx: GfxContext):
        self.gfx = gfx
        self.savedata: Optional[CC2XMLSave] = None
        # east-west, south-north
        self.origin = (0, 0)
        self.camera_size = 0
        self.reset_view()
        self.grid_major = 4000
        self.grid_minor = 1000
        self.grid_color = (0, 0, 128, 48)
        self.pan = False
        self.hover_items = []
        self.selected_item: Union[Tile, Vehicle, VehicleSpawn, None] = None
        self._tiles = []
        self._vehicles = []
        self._spawns = []
        self.ui_manager = UIManager((self.gfx.w, self.gfx.h))
        self.unit_window = UnitWindow((24, 40), self.ui_manager)
        self.unit_window.hide()


    @property
    def camera_w(self) -> int:
        return round(self.camera_size)

    @property
    def camera_h(self) -> int:
        return abs(round(self.camera_size / self.gfx.aspect))

    @property
    def surface(self) -> pygame.Surface:
        return self.gfx.surface

    @property
    def tiles(self) -> List[MapTile]:
        return list(self._tiles)

    @property
    def vehicles(self) -> List[MapVehicle]:
        return list(self._vehicles)

    @property
    def spawns(self) -> List[Spawn]:
        return list(self._spawns)

    @property
    def screen_middle(self) -> Tuple[float, float]:
        return self.origin[0] + self.camera_w / 2, self.origin[1] - self.camera_h / 2

    def reset_view(self):
        _, y = self.screen_to_world_scale((0, self.surface.get_height() - 48))
        self.origin = (0, -y)
        self.camera_size = 50000 # 50km wide


    def load(self, save: CC2XMLSave):
        del self.savedata
        self.savedata = save
        self.reset_view()
        self._tiles.clear()
        for tile in self.savedata.tiles:
            self._tiles.append(MapTile(tile))
            for spawn in tile.spawn_data.vehicles.items():
                spawn.parent_object = tile
                self._spawns.append(Spawn(spawn, tile))
        for vehicle in self.savedata.vehicles:
            if vehicle.vehicle_type == VehicleType.Carrier:
                obj = Carrier(vehicle)
            elif vehicle.vehicle_type == VehicleType.Barge:
                obj = Barge(vehicle)
            else:
                obj = MapVehicle(vehicle)
            self._vehicles.append(obj)

        first_island = self.tiles[0]
        self.pan_to(first_island.tile().loc.x, first_island.tile().loc.z)

    def _world_to_screen_vha(self, world: Tuple[float, float]) -> Tuple[float, float, float]:
        aspect = self.gfx.aspect
        return self.camera_w, self.camera_h, aspect

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
        screen_w = self.gfx.w
        screen_h = self.gfx.h

        view_x = screen[0] / screen_w
        view_y = screen[1] / screen_h

        return view_x * self.camera_w, -view_y * self.camera_h

    def screen_to_world(self, screen: Tuple[float, float]) -> Tuple[float, float]:
        world_x, world_y = self.screen_to_world_scale(screen)

        return int(world_x + self.origin[0]), int(world_y + self.origin[1])


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
                             (width, screen_y), width=self.gfx.scale_strokes)
            h_y += self.grid_major

    def event(self, event: pygame.event.Event):
        if event:

            if event.type == pygame.VIDEORESIZE:
                self.ui_manager.set_window_resolution((self.gfx.w, self.gfx.h))

            if self.ui_manager.process_events(event):
                return

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
        under = self.hover_items
        if under:
            self.selected_item = under[0]
            if self.selected_item:
                self.unit_window.unit = self.selected_item
                self.unit_window.show()
            print(under[0])
        else:
            self.selected_item = None
            self.unit_window.hide()
            self.pan = True

    def mouse_up(self):
        self.pan = False

    def mouse_move(self):
        self.hover_items = self.under_mouse()
        if self.pan:
            dx, dy = pygame.mouse.get_rel()
            self.pan_camera(-dx * 1.6, -dy * 1.3)


    def draw(self, time_delta: float):
        """Render the portion of the map in view"""

        self.render_grid()
        self.render_tiles()
        self.render_units()
        if self.selected_item is not None:
            self.unit_window.show()
        self.ui_manager.update(time_delta)
        self.ui_manager.draw_ui(self.gfx.surface)

        self.render_mouse()
        # render the systray
        self.render_systray()

    def render_mouse(self):
        screen = pygame.mouse.get_pos()
        world = self.screen_to_world(screen)
        self.gfx.update_ui_text(4, self.gfx.h - self.gfx.font.get_height() * 2, f"X={world[0]:d}, Y={world[1]:d}", 256, 0, "#ababab")

    def render_systray(self):
        x = 0
        h = self.gfx.font.get_height()
        y = self.gfx.h - h

        self.gfx.update_ui_rectangle(x, y, self.gfx.w, h, "#cdcdcd")
        x += 3
        for hover in self.hover_items:
            text = f"{hover}"
            text_w = int(self.gfx.font.get_height() * 0.5) * len(text) + 1
            self.gfx.update_ui_text(x, y + self.gfx.scale_strokes, text, text_w, 0, "#000000")
            x += text_w + 6

    def render_tile(self, tile: MapTile):
        pos = tile.tile().world_position
        bounds = tile.tile().bounds

        color = pygame.Color(get_team_color(tile.team_owner))
        if tile in self.hover_items:
            color = (255, 255, 255, 255)
        sw = self.world_to_screen((pos.x + bounds.min.x, pos.z + bounds.min.z))
        se = self.world_to_screen((pos.x + bounds.max.x, pos.z + bounds.min.z))
        ne = self.world_to_screen((pos.x + bounds.max.x, pos.z + bounds.max.z))
        nw = self.world_to_screen((pos.x + bounds.min.x, pos.z + bounds.max.z))
        poly = [
            sw,
            nw,
            ne,
            se,
        ]
        top = pos.z + bounds.max.z
        pygame.draw.polygon(self.surface, color, poly, width=self.gfx.scale_strokes)

        # draw a mover box
        pygame.draw.rect(self.surface, color, (nw[0], nw[1], 16, 16))
        name = tile.name
        screen = self.world_to_screen((pos.x - tile.tile().island_radius, top))
        self.gfx.update_ui_text(screen[0], screen[1] - self.gfx.font.get_height() - 2, name, 6 * len(name), 1, color )

    def render_tiles(self):
        if self.savedata:
            for tile in self.tiles:
                self.render_tile(tile)


    def render_units(self):
        if self.savedata:
            seen_vehicles = set()

            for vehicle in self.vehicles:
                seen_vehicles.add(vehicle.v_id)
                color = pygame.Color(get_team_color(vehicle.team_owner))
                if vehicle in self.hover_items:
                    color = (255, 255, 255, 255)
                pos = vehicle.vehicle().loc
                screen = self.world_to_screen((pos.x, pos.z))
                pygame.draw.circle(self.surface, color, screen, 6, width=0)
                pygame.draw.circle(self.surface, (0, 0, 0, 48), screen, 7, width=1)

            for spawn in self.spawns:
                data = spawn.spawn().data
                if data.respawn_id not in seen_vehicles:
                    if isinstance(spawn.parent_object, Tile):
                        tile = spawn.parent_object
                        color = pygame.Color(get_team_color(tile.team_control))
                        if spawn in self.hover_items:
                            color = (255, 255, 255, 255)
                        pos = spawn.spawn().loc
                        screen = self.world_to_screen((pos.x, pos.z))
                        pygame.draw.circle(self.surface, color, screen, 6, width=self.gfx.scale_strokes)


    def under_mouse(self) -> List:
        found = []
        if self.savedata:
            mouse = pygame.mouse.get_pos()

            for unit in self.vehicles:
                # get units within 10 screen pixels of this mouse point
                screen = self.world_to_screen((unit.location.x, unit.location.z))
                if screen[0] - 5 < mouse[0] < screen[0] + 5:
                    if screen[1] - 5 < mouse[1] < screen[1] + 5:
                        found.append(unit)

            world_x, world_y = self.screen_to_world(mouse)
            for tile in self.tiles:
                # get tile under the mouse using the NW corner box
                nw = (tile.tile().loc.x + tile.tile().bounds.min.x, tile.tile().loc.z + tile.tile().bounds.max.z)
                box_size = self.screen_to_world_scale((16, 16))
                box_se = (nw[0] + box_size[0], nw[1] + box_size[1])
                if nw[0] < world_x < nw[0] + box_size[0]:
                    print(f"in x bounds  {nw[1]} {world_y} {box_se[1]}")
                    if box_se[1] < world_y < nw[1]:
                        found.append(tile)
                        break

        return found

    def zoom(self, amount: int):
        if amount:
            middle = self.screen_middle
            amount = int(clamp(amount, -4, 4))
            frac = self.camera_size / 10
            self.camera_size += frac * -amount
            self.camera_size = clamp(self.camera_size, 1000, 150000)
            self.pan_to(*middle)

    def set_origin(self, new_x, new_y) -> None:
        self.origin = (new_x, new_y)

    def pan_to(self, world_x, world_y) -> None:
        self.origin = (
            world_x - self.camera_w / 2,
            world_y + self.camera_h / 2
        )

    def pan_camera(self, screen_dx, screen_dy):
        screen_dx = clamp(screen_dx, -60, 60)
        screen_dy = clamp(screen_dy, -40, 40)
        world = self.screen_to_world_scale((screen_dx, screen_dy))

        x = int(round(self.origin[0] + world[0]))
        y = int(round(self.origin[1] + world[1]))
        self.origin = (x, y)
