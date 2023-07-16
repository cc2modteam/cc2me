from typing import cast, Optional, Union, List, Any
from xml.etree.ElementTree import Element

from .attachments import Attachments, Attachment
from .embedded_xmlstates.vehicles import EmbeddedVehicleStateData
from .vehicle_state import VehicleStateContainer, VehicleAttachmentState
from ..teams import Team
from ..utils import (ElementProxy, e_property, IntAttribute, Transform, Bodies,
                     Location, MovableLocationMixin)
from ...constants import VehicleType, VehicleAttachmentDefinitionIndex, get_attachment_capacity

REMOTE_DRIVEABLE_VEHICLES = [
    VehicleType.Bear,
    VehicleType.Barge,
    VehicleType.Seal,
    VehicleType.Walrus,
    VehicleType.Razorbill,
    VehicleType.Albatross,
    VehicleType.Petrel,
    VehicleType.Mule,
    VehicleType.Needlefish,
    VehicleType.Swordfish
]


class Vehicle(ElementProxy, MovableLocationMixin):
    tag = "v"

    @property
    def state(self) -> Optional[VehicleStateContainer]:
        if self.cc2obj:
            return self.cc2obj.vehicle_state(self.id)
        return None

    @property
    def human_controlled(self) -> bool:
        if self.cc2obj:
            team: Team = self.cc2obj.team(self.team_id)
            return team.human_controlled
        return False

    @property
    def type(self) -> VehicleType:
        return VehicleType.lookup(self.definition_index)

    @property
    def human_remote_pilot(self) -> bool:
        if self.human_controlled:
            return self.type in REMOTE_DRIVEABLE_VEHICLES
        return False

    def on_set_team_id(self):
        # if we are set to a human team, ensure there is a pilot seat for some unit types
        if self.human_remote_pilot:
            a0 = self.attachments[0]
            if a0 is None:
                pass
                # make a driver seat

    id = e_property(IntAttribute("id"))
    definition_index = e_property(IntAttribute("definition_index"))
    team_id = e_property(IntAttribute("team_id"), side_effect=on_set_team_id)

    @property
    def transform(self) -> Transform:
        return cast(Transform, self.get_default_child_by_tag(Transform))

    @property
    def bodies(self) -> Bodies:
        return cast(Bodies, self.get_default_child_by_tag(Bodies))

    @property
    def attachments(self) -> Attachments:
        return cast(Attachments, self.get_default_child_by_tag(Attachments))

    def set_location(self,
                     x: Optional[float] = None,
                     y: Optional[float] = None,
                     z: Optional[float] = None
                     ):
        """change the location of this vehicle and update all bodies and attachments with the delta"""
        current_position = self.transform
        if x is None:
            x = current_position.tx
        if y is None:
            y = current_position.ty
        if z is None:
            z = current_position.tz

        dx = x - current_position.tx
        dy = y - current_position.ty
        dz = z - current_position.tz

        # update positions
        self.transform.tx += dx
        self.transform.ty += dy
        self.transform.tz += dz

        for att in self.attachments.items():
            if att.bodies:
                for body in att.bodies.items():
                    body.transform.tx += dx
                    body.transform.ty += dy
                    body.transform.tz += dz

        for body in self.bodies.items():
            body.transform.tx += dx
            body.transform.ty += dy
            body.transform.tz += dz

    def move(self, x: float, y: float, z: float) -> None:
        self.set_location(x, y, z)

    def translate(self, dx: float, dy: float, dz: float) -> None:
        self.set_location(self.loc.x + dx,
                          self.loc.y + dy,
                          self.loc.z + dz)

    @property
    def waypoints(self) -> List["Waypoint"]:
        ret = []
        wlist = self.state.waypoints
        for w in wlist:
            ret.append(Waypoint(w, cc2obj=self.cc2obj, vehicle=self))
        return ret

    @property
    def loc(self) -> Location:
        return Location(self.transform.tx, self.transform.ty, self.transform.tz)

    def get_attachment(self, attachment_index: int) -> Optional[VehicleAttachmentDefinitionIndex]:
        item = self.attachments[attachment_index]
        if item is not None:
            item = VehicleAttachmentDefinitionIndex.lookup(item.definition_index)
        return item

    def get_attachment_state(self, attachment_index: int) -> Optional[VehicleAttachmentState]:
        return self.state.attachments[attachment_index]

    def set_attachment(self, attachment_index: int, value: Optional[Union[str, VehicleAttachmentDefinitionIndex]]):
        if value == "None":
            value = None

        if isinstance(value, str):
            try:
                value = VehicleAttachmentDefinitionIndex.reverse_lookup(value)
            except KeyError:
                return

        if value is not None:
            value: VehicleAttachmentDefinitionIndex
            value_idx = value.value
            new_attachment = Attachment()
            new_attachment.attachment_index = attachment_index
            new_attachment.definition_index = value_idx
            self.attachments.replace(new_attachment)

            new_attachment_state = VehicleAttachmentState(element=None, cc2obj=self.cc2obj)
            new_attachment_state.attachment_index = attachment_index

            capacity = get_attachment_capacity(self.definition_index, value)
            if capacity is not None:
                data = new_attachment_state.data
                for attrib_name in capacity.attribs:
                    setattr(data, attrib_name, capacity.count)

                new_attachment_state.data = data
                self.state.attachments.replace(new_attachment_state)
        else:
            del self.attachments[attachment_index]
            del self.state.attachments[attachment_index]


class Waypoint(ElementProxy, MovableLocationMixin):

    def __init__(self, element: Optional[Element] = None, cc2obj: Optional[Any] = None, vehicle: Optional[Vehicle] = None):
        super().__init__(element, cc2obj)
        self.vehicle = vehicle

    def set_location(self,
                     x: Optional[float] = None,
                     y: Optional[float] = None,
                     z: Optional[float] = None
                     ):
        if z is not None:
            self.element.set("altitude", str(z))
        position = self.element.find("position")
        if position is not None:
            if x is not None:
                position.set("x", str(x))
            if y is not None:
                position.set("y", str(x))

    def move(self, x: float, y: float, z: float) -> None:
        self.set_location(x, y, z)

    @property
    def loc(self) -> Location:
        position = self.element.find("position")
        location = Location(float(position.get("x")),
                            float(position.get("y")),
                            float(self.element.get("altitude")))
        return location

    def translate(self, dx: float, dy: float, dz: float) -> None:
        self.set_location(self.loc.x + dx,
                          self.loc.y + dy,
                          self.loc.z + dz)

    tag = "v"
