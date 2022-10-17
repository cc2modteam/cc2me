import random
from typing import Optional, cast

from .utils import (ElementProxy,
                    IntAttribute,
                    FloatAttribute,
                    BoolAttribute,
                    Bounds,
                    WorldPosition,
                    IsSetMixin,
                    MAX_INTEGER, e_property)


class Facility(ElementProxy):
    tag = "facility"

    category = IntAttribute("category", default_value=1)
    fitting = IntAttribute("fitting", default_value=60)
    production_timer = IntAttribute("production_timer", default_value=MAX_INTEGER)
    production_timer_defense = IntAttribute("production_timer_defense", default_value=MAX_INTEGER)

    def defaults(self):
        self.category = random.randint(1, 7)
        self.fitting = 60


class SpawnData(ElementProxy, IsSetMixin):
    tag = "spawn_data"
    team_id = e_property(IntAttribute("team_id", default_value=0))

    def defaults(self):
        self.is_set = False


class Tile(ElementProxy):
    tag = "t"

    id = e_property(IntAttribute("id", default_value=0))
    index = e_property(IntAttribute("index", default_value=1))
    seed = e_property(IntAttribute("seed", default_value=12000))
    biome_type = e_property(IntAttribute("biome_type"))
    team_capture = e_property(IntAttribute("team_capture", default_value=MAX_INTEGER))
    team_capture_progress = e_property(FloatAttribute("team_capture_progress"))
    difficulty_factor = e_property(FloatAttribute("difficulty_factor"))

    def defaults(self):
        self.seed = random.randint(10000, 22000)
        self.biome_type = random.randint(1, 7)
        self.team_capture_progress = 0.0
        self.team_capture = 4294967295
        self.difficulty_factor = 0.0
        assert self.bounds
        assert self.facility
        assert self.world_position
        assert self.spawn_data

    @property
    def bounds(self) -> Bounds:
        return cast(Bounds, self.get_default_child_by_tag(Bounds))

    @property
    def spawn_data(self) -> SpawnData:
        return cast(SpawnData, self.get_default_child_by_tag(SpawnData))

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
        if x is not None:
            self.world_position.x = x
        if y is not None:
            self.world_position.y = y
        if z is not None:
            self.world_position.z = z

