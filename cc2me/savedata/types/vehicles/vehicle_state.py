from typing import cast, List, Optional

from xml.etree import ElementTree
from xml.etree.ElementTree import Element

from .embedded_xmlstates.vehicles import EmbeddedVehicleStateData, EmbeddedAttachmentStateData
from ..utils import ElementProxy, e_property, StrAttribute, IntAttribute


class VehicleAttachmentState(ElementProxy):
    tag = "a"
    attachment_index = e_property(IntAttribute("attachment_index"))
    state = e_property(StrAttribute("state"))

    _cached_data = None

    def defaults(self):
        data = self.data
        self.data = data

    @property
    def data(self) -> EmbeddedAttachmentStateData:
        if self._cached_data is None:
            root = None
            try:
                root = ElementTree.fromstring(self.state)
            except ElementTree.ParseError:
                pass
            self._cached_data = EmbeddedAttachmentStateData(element=root)
        return self._cached_data

    @data.setter
    def data(self, value: EmbeddedAttachmentStateData):
        self._cached_data = value
        self.state = value.to_string()


class VehicleAttachmentStates(ElementProxy):
    tag = "attachments"

    def items(self) -> List[VehicleAttachmentState]:
        return [VehicleAttachmentState(x) for x in self.children()]

    def __getitem__(self, attachment_index) -> Optional[VehicleAttachmentState]:
        for item in self.items():
            if item.attachment_index == attachment_index:
                return item
        return None

    def __delitem__(self, attachment):
        if attachment:
            a_id = str(attachment.attachment_index)
            children = [x for x in self.element]
            for child in children:
                if child.attrib.get("attachment_index", "-1") == a_id:
                    self.element.remove(child)

    def replace(self, attachment: VehicleAttachmentState):
        del self[attachment]
        self.element.append(attachment.element)


class VehicleStateContainer(ElementProxy):
    tag = "v"
    id = e_property(IntAttribute("id", default_value=0))
    state = e_property(StrAttribute("state", default_value=""))

    _cached_state = None
    _cached_waypoints = []

    def defaults(self):
        data = self.data
        self.data = data  # uuuh..

    @property
    def attachments(self) -> VehicleAttachmentStates:
        return cast(VehicleAttachmentStates, self.get_default_child_by_tag(VehicleAttachmentStates))

    @property
    def data(self) -> EmbeddedVehicleStateData:
        return self.get_embdata()

    def get_embdata(self):
        if self._cached_state is None:
            root = None
            try:
                root = ElementTree.fromstring(self.state)
            except ElementTree.ParseError:
                pass
            state = EmbeddedVehicleStateData(element=root)
            self._cached_state = state
        else:
            assert True
        return self._cached_state

    @data.setter
    def data(self, value: EmbeddedVehicleStateData):
        self.set_embdata(value)
        self.state = value.to_string()

    def set_embdata(self, value: EmbeddedVehicleStateData):
        self.state = value

    @property
    def waypoints(self) -> List[Element]:
        ret = []
        for child in self.get_embdata().children():
            if child.tag == "waypoints":
                ret = child.findall("w")
                break
        return ret
