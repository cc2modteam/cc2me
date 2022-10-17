import random
from typing import Optional, cast

from .utils import ElementProxy, Bounds, WorldPosition, IsSetMixin


class Tile(ElementProxy):
    tag = "t"

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
    def spawn_data(self) -> "SpawnData":
        return cast(SpawnData, self.get_default_child_by_tag(SpawnData))

    @property
    def world_position(self) -> WorldPosition:
        return cast(WorldPosition, self.get_default_child_by_tag(WorldPosition))

    @property
    def facility(self) -> "Facility":
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

    @property
    def team_capture(self) -> int:
        return int(self.get("team_capture", 0))

    @team_capture.setter
    def team_capture(self, value: int):
        self.set("team_capture", value)

    @property
    def difficulty_factor(self) -> float:
        return float(self.get("difficulty_factor", 0))

    @difficulty_factor.setter
    def difficulty_factor(self, value: float):
        self.set("difficulty_factor", value)

    @property
    def team_capture_progress(self) -> float:
        return float(self.get("team_capture_progress", 0))

    @team_capture_progress.setter
    def team_capture_progress(self, value: float):
        self.set("team_capture_progress", value)

    @property
    def id(self) -> int:
        return int(self["id"])

    @id.setter
    def id(self, value: int):
        self["id"] = value

    @property
    def index(self) -> int:
        return self["index"]

    @index.setter
    def index(self, value: int):
        self["index"] = value

    @property
    def seed(self) -> int:
        return int(self["seed"])

    @seed.setter
    def seed(self, value: int):
        self["seed"] = value

    @property
    def biome_type(self) -> int:
        return self["biome_type"]

    @biome_type.setter
    def biome_type(self, value: int):
        self["biome_type"] = value

    @property
    def team_control(self) -> int:
        return self["team_control"]

    @team_control.setter
    def team_control(self, value: int):
        self.spawn_data.team_id = value
        self["team_control"] = value


class Facility(ElementProxy):
    tag = "facility"

    def defaults(self):
        self.category = random.randint(1, 7)
        self.fitting = 60
        self.production_timer = 4294967295
        self.production_timer_defense = 4294967295

    @property
    def category(self) -> int:
        return self["category"]

    @category.setter
    def category(self, value: int):
        self["category"] = value

    @property
    def fitting(self) -> int:
        return self["fitting"]

    @fitting.setter
    def fitting(self, value: int):
        self["fitting"] = value

    @property
    def production_timer(self) -> int:
        return self["production_timer"]

    @production_timer.setter
    def production_timer(self, value: int):
        self["production_timer"] = value

    @property
    def production_timer_defense(self) -> int:
        return self["production_timer_defense"]

    @production_timer_defense.setter
    def production_timer_defense(self, value: int):
        self["production_timer_defense"] = value


class SpawnData(ElementProxy, IsSetMixin):
    tag = "spawn_data"

    def defaults(self):
        self.is_set = False
        self.team_id = 0

    @property
    def team_id(self) -> int:
        return self["team_id"]

    @team_id.setter
    def team_id(self, value: int):
        self["team_id"] = value
