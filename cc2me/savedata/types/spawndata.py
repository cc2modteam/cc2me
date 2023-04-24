from typing import cast, Iterable, Optional, List, Any
from xml.etree.ElementTree import Element

from .utils import ElementProxy, IsSetMixin, e_property, IntAttribute, FloatAttribute, WorldPosition, \
    MovableLocationMixin, Location, Bodies
from .vehicles.attachments import Attachment
from ..constants import get_spawn_attachment_type, VehicleAttachmentDefinitionIndex


class VehicleSpawnAttachment(ElementProxy):
    tag = "a"
    ammo = e_property(IntAttribute("ammo"))

    attachment_type = e_property(IntAttribute("attachment_type"))

    @property
    def definition_index(self) -> int:
        return int(self.element.attrib.get("definition_index", "0"))

    @definition_index.setter
    def definition_index(self, value: int):
        self.element.attrib["definition_index"] = str(value)
        att_type = get_spawn_attachment_type(VehicleAttachmentDefinitionIndex.lookup(value))
        self.attachment_type = att_type


class VehicleSpawnAttachments(ElementProxy):
    tag = "attachments"

    def items(self) -> List[VehicleSpawnAttachment]:
        return [VehicleSpawnAttachment(x) for x in self.children()]

    def __getitem__(self, item_index: int) -> Optional[VehicleSpawnAttachment]:
        for item in self.items():
            if item.attachment_index == item_index:
                return item
        return None

    def __delitem__(self, key):
        for child in self.element:
            if child.attrib.get("attachment_index", "-1") == str(key.attachment_index):
                self.element.remove(child)

    def replace(self, attachment: VehicleSpawnAttachment):
        del self[attachment]
        self.element.append(attachment.element)


class VehicleSpawnData(ElementProxy):
    tag = "data"

    respawn_id = e_property(IntAttribute("respawn_id", default_value=0))
    definition_index = e_property(IntAttribute("definition_index", default_value=0))
    hitpoints = e_property(IntAttribute("hitpoints", default_value=0))
    orientation = e_property(FloatAttribute("orientation", default_value=0))

    @property
    def attachments(self) -> VehicleSpawnAttachments:
        return cast(VehicleSpawnAttachments, self.get_default_child_by_tag(VehicleSpawnAttachments))

    @property
    def world_position(self) -> WorldPosition:
        return cast(WorldPosition, self.get_default_child_by_tag(WorldPosition))


class VehicleSpawn(ElementProxy, MovableLocationMixin):

    def move(self, x: float, y: float, z: float) -> None:
        self.data.world_position.x = x
        self.data.world_position.y = y
        self.data.world_position.z = z

    def translate(self, dx: float, dy: float, dz: float) -> None:
        self.move(self.data.world_position.x + dx,
                  self.data.world_position.y + dy,
                  self.data.world_position.z + dz)

    @property
    def loc(self) -> Location:
        pos = self.data.world_position
        return Location(pos.x, pos.y, pos.z)

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
            ret.append(VehicleSpawn(element, self.cc2obj))
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
        self.is_set = True

    @property
    def vehicles(self) -> VehicleSpawnContainer:
        return cast(VehicleSpawnContainer, self.get_default_child_by_tag(VehicleSpawnContainer))
