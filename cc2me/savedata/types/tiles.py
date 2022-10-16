import random
from typing import Optional, cast
from xml.etree.ElementTree import Element

from .utils import ElementProxy, Bounds, WorldPosition


class Tile(ElementProxy):
    tag = "t"

    def defaults(self):
        self.seed = random.randint(255, 15000)
        self.biome_type = random.randint(1, 7)

    @property
    def bounds(self) -> Bounds:
        return cast(Bounds, self.get_default_child_by_tag(Bounds))

    @property
    def world_position(self) -> WorldPosition:
        return cast(WorldPosition, self.get_default_child_by_tag(WorldPosition))

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
        self["team_control"] = value

