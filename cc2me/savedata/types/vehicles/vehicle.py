from typing import cast, List, Optional
from ... import constants
from ..utils import (ElementProxy, e_property, IntAttribute, Transform, Bodies,
                     LocationMixin, Location, MovableLocationMixin)


def vehicle_definition_name(defid: int) -> str:
    if constants.VEHICLE_DEF_CARRIER == defid:
        return "Carrier"
    return f"Unknown ({defid})"


class Attachment(ElementProxy):
    tag = "a"
    attachment_index = e_property(IntAttribute("attachment_index"))
    definition_index = e_property(IntAttribute("definition_index"))

    @property
    def bodies(self) -> Bodies:
        return cast(Bodies, self.get_default_child_by_tag(Bodies))


class Attachments(ElementProxy):
    tag = "attachments"

    def items(self) -> List[Attachment]:
        return [Attachment(x) for x in self.children()]


class Vehicle(ElementProxy, LocationMixin, MovableLocationMixin):
    tag = "v"

    id = e_property(IntAttribute("id"))
    definition_index = e_property(IntAttribute("definition_index"))
    team_id = e_property(IntAttribute("team_id"))

    @property
    def chassis(self) -> str:
        return vehicle_definition_name(self.definition_index)

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

    @property
    def loc(self) -> Location:
        return Location(self.transform.tx, self.transform.ty, self.transform.tz)