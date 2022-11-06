from typing import cast, Iterable

from .utils import ElementProxy, IsSetMixin, e_property, IntAttribute, FloatAttribute, WorldPosition


class VehicleSpawnData(ElementProxy):
    tag = "data"

    respawn_id = e_property(IntAttribute("respawn_id", default_value=0))
    definition_index = e_property(IntAttribute("definition_index", default_value=0))
    hitpoints = e_property(IntAttribute("hitpoints", default_value=0))
    orientation = e_property(FloatAttribute("orientation", default_value=0))

    @property
    def world_position(self) -> WorldPosition:
        return cast(WorldPosition, self.get_default_child_by_tag(WorldPosition))


class VehicleSpawn(ElementProxy):
    tag = "v"
    spawn_type = e_property(IntAttribute("spawn_type", default_value=0))

    @property
    def data(self) -> VehicleSpawnData:
        return cast(VehicleSpawnData, self.get_default_child_by_tag(VehicleSpawnData))

    @data.setter
    def data(self, value: VehicleSpawnData):
        children = [x for x in self.element]
        for child in children:
            self.element.remove(child)
        self.element.append(value.element)


class VehicleSpawnContainer(ElementProxy):
    tag = "vehicles"

    def items(self) -> Iterable[VehicleSpawn]:
        ret = []
        for element in self.children():
            ret.append(VehicleSpawn(element))
        return ret

    def remove(self, child: VehicleSpawn):
        children = self.items()
        for item in children:
            item: VehicleSpawn
            if item.data.respawn_id == child.data.respawn_id:
                self.element.remove(item.element)

    def append(self, item: VehicleSpawn):
        self.element.append(item.element)


class SpawnData(ElementProxy, IsSetMixin):
    tag = "spawn_data"
    team_id = e_property(IntAttribute("team_id", default_value=0))

    def defaults(self):
        self.is_set = False

    @property
    def vehicles(self) -> VehicleSpawnContainer:
        return cast(VehicleSpawnContainer, self.get_default_child_by_tag(VehicleSpawnContainer))
