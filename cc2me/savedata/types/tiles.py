import random
from typing import Optional, cast, Tuple

from .spawndata import SpawnData
from .teams import Team
from .utils import (ElementProxy,
                    IntAttribute,
                    FloatAttribute,
                    Bounds,
                    WorldPosition,
                    e_property, Location, MovableLocationMixin)
from ..constants import MAX_INTEGER, generate_island_seed


class Facility(ElementProxy):
    tag = "facility"

    category = e_property(IntAttribute("category", default_value=1))
    fitting = e_property(IntAttribute("fitting", default_value=60))
    production_timer = e_property(IntAttribute("production_timer", default_value=MAX_INTEGER))
    production_timer_defense = e_property(IntAttribute("production_timer_defense", default_value=MAX_INTEGER))

    def defaults(self):
        self.category = random.randint(1, 7)
        self.fitting = 60


class Tile(ElementProxy, MovableLocationMixin):
    tag = "t"

    id = e_property(IntAttribute("id", default_value=0))
    index = e_property(IntAttribute("index", default_value=1))
    seed = e_property(IntAttribute("seed", default_value=12000))
    biome_type = e_property(IntAttribute("biome_type"))
    team_capture = e_property(IntAttribute("team_capture", default_value=MAX_INTEGER))
    team_capture_progress = e_property(FloatAttribute("team_capture_progress"))
    difficulty_factor = e_property(FloatAttribute("difficulty_factor"))

    @property
    def human_controlled(self) -> bool:
        if self.cc2obj:
            team: Team = self.cc2obj.team(self.team_control)
            return team.human_controlled
        return False

    def on_set_team_control(self):
        self.spawn_data.team_id = self.team_control

    team_control = e_property(IntAttribute("team_control"), side_effect=on_set_team_control)

    def defaults(self):
        self.seed = generate_island_seed()
        self.biome_type = random.randint(1, 7)
        self.team_capture_progress = 0.0
        self.team_control = 0
        self.difficulty_factor = 0.0
        assert self.bounds
        assert self.facility
        assert self.world_position
        assert self.spawn_data

    @property
    def bounds(self) -> Bounds:
        return cast(Bounds, self.get_default_child_by_tag(Bounds))

    @property
    def island_radius(self) -> float:
        return self.bounds.max.x

    @island_radius.setter
    def island_radius(self, radius: int):
        radius = int(radius)
        if radius > 2000:
            if radius > 7000:
                radius = 7000
            self.bounds.min.x = -1 * radius
            self.bounds.min.z = -1 * radius
            self.bounds.max.x = radius
            self.bounds.max.z = radius

    @property
    def spawn_data(self) -> SpawnData:
        sd = cast(SpawnData, self.get_default_child_by_tag(SpawnData))
        sd.cc2obj = self.cc2obj
        return sd

    @property
    def world_position(self) -> WorldPosition:
        return cast(WorldPosition, self.get_default_child_by_tag(WorldPosition))

    @property
    def facility(self) -> Facility:
        return cast(Facility, self.get_default_child_by_tag(Facility))

    def set_position(self, *,
                     x: Optional[float] = None,
                     y: Optional[float] = None,
                     z: Optional[float] = None):
        dx = 0.0
        if x is not None:
            dx = x - self.world_position.x
            self.world_position.x = x
        dy = 0.0
        if y is not None:
            dy = y - self.world_position.y
            self.world_position.y = y
        dz = 0.0
        if z is not None:
            dz = z - self.world_position.z
            self.world_position.z = z

        # update the spawn locations
        for item in self.spawn_data.vehicles.items():
            item.data.world_position.x += dx
            item.data.world_position.y += dy
            item.data.world_position.z += dz

    def move(self, x: float, y: float, z: float) -> None:
        self.set_position(x=x, y=y, z=z)

    @property
    def loc(self) -> Location:
        return Location(self.world_position.x, self.world_position.y, self.world_position.z)
