from abc import ABC
from typing import cast, List, Optional

from ...constants import VehicleAttachmentDefinitionIndex as Adi, VehicleAttachmentDefinitionIndex
from ..utils import ElementProxy, e_property, IntAttribute, Bodies


class Attachment(ElementProxy):
    tag = "a"
    attachment_index = e_property(IntAttribute("attachment_index"))
    definition_index = e_property(IntAttribute("definition_index"))

    @property
    def bodies(self) -> Bodies:
        return cast(Bodies, self.get_default_child_by_tag(Bodies))


class DriverSeat(Attachment):
    """Attachment where a human can remote control a unit"""


class GroundTurret(Attachment, ABC):
    """Eg, 30mm, 40mm, IR launcher"""


class Gun30mm(GroundTurret):
    pass


class Gun40mm(GroundTurret):
    pass


class MissileIRLauncher(GroundTurret):
    pass


class GroundHeavyTurret(Attachment, ABC):
    """Eg, 100mm, 120mm"""


class Gun100mm(GroundHeavyTurret):
    pass


class Gun100mmHeavy(Gun100mm):
    pass


class Gun120mm(GroundHeavyTurret):
    pass


class UtilityAttachment(Attachment, ABC):
    """Eg, flare, smoke, small cam"""


class FlareLauncher(UtilityAttachment):
    pass


ATTACHMENT_TYPES = {
    Adi.DriverSeat: DriverSeat,
    Adi.Flares: FlareLauncher,
}


class Attachments(ElementProxy):
    tag = "attachments"

    def items(self) -> List[Attachment]:
        return [Attachment(x) for x in self.children()]

    def __getitem__(self, item_index: int) -> Optional[Attachment]:
        for item in self.items():
            if item.attachment_index == item_index:
                return item
        return None

    def __delitem__(self, key):
        for item in self.items():
            if item.attachment_index == key:
                self.children().remove(item.element)

    def replace(self, attachment: Attachment):
        del self[attachment]
        self.children().append(attachment.element)


def make_attachment(atype: VehicleAttachmentDefinitionIndex):
    ctor: Optional[callable] = ATTACHMENT_TYPES.get(atype, None)
    if ctor:
        return ctor(element=None, definition_index=atype.value)
    raise KeyError(atype)
