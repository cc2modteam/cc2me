from typing import cast, List, Optional

from ..constants import VehicleAttachmentDefinitionIndex
from .utils import ElementProxy, e_property, IntAttribute, Bodies


class Attachment(ElementProxy):
    tag = "a"
    attachment_index = e_property(IntAttribute("attachment_index"))
    definition_index = e_property(IntAttribute("definition_index"))

    @property
    def bodies(self) -> Optional[Bodies]:
        return cast(Bodies, self.get_default_child_by_tag(Bodies))

    @property
    def attachment_type(self) -> Optional[VehicleAttachmentDefinitionIndex]:
        if self.definition_index > 0:
            return VehicleAttachmentDefinitionIndex(self.definition_index)
        return None

    def __str__(self):
        a_type = self.attachment_type
        if a_type is not None:
            return a_type.name
        return "[EMPTY]"


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
        for child in self.element:
            if child.attrib.get("attachment_index", "-1") == str(key.attachment_index):
                self.element.remove(child)

    def replace(self, attachment: Attachment):
        del self[attachment]
        self.element.append(attachment.element)


def make_attachment(atype: VehicleAttachmentDefinitionIndex) -> Attachment:
    obj = Attachment(element=None)
    obj.definition_index = atype.value
    return obj
