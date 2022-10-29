from typing import cast, List

from xml.etree import ElementTree
from .embedded_xmlstates.vehicles import EmbeddedVehicleStateData
from ..utils import ElementProxy, e_property, StrAttribute, IntAttribute


class VehicleAttachmentState(ElementProxy):
    tag = "a"
    attachment_index = e_property(IntAttribute("attachment_index"))
    state = e_property(StrAttribute("state"))


class VehicleAttachmentStates(ElementProxy):
    tag = "attachments"

    def items(self) -> List[VehicleAttachmentState]:
        return [VehicleAttachmentState(x) for x in self.children()]


class VehicleStateContainer(ElementProxy):
    tag = "v"
    id = e_property(IntAttribute("id", default_value=0))
    state = e_property(StrAttribute("state", default_value=""))

    @property
    def attachments(self) -> VehicleAttachmentStates:
        return cast(VehicleAttachmentStates, self.get_default_child_by_tag(VehicleAttachmentStates))

    @property
    def data(self) -> EmbeddedVehicleStateData:
        root = ElementTree.fromstring(self.state)
        return EmbeddedVehicleStateData(element=root)

    @data.setter
    def data(self, value: EmbeddedVehicleStateData):
        self.state = value.to_string()

