from xml.etree import ElementTree
from ...utils import ElementProxy, IntAttribute, e_property, FloatAttribute, BoolAttribute


class EmbeddedVehicleStateData(ElementProxy):
    # see cc2me/tests/canned_saves/manta-state.xml
    tag = "data"

    # e.g. glued to another unit, eg, this is a docked unit
    attached_to_vehicle_id = e_property(IntAttribute("attached_to_vehicle_id"))

    internal_fuel_remaining = e_property(FloatAttribute("internal_fuel_remaining"))
    is_destroyed = e_property(BoolAttribute("is_destroyed"))
    hitpoints = e_property(IntAttribute("hitpoints"))

    def defaults(self):
        self.is_destroyed = False
        self.hitpoints = 80
        self.internal_fuel_remaining = 400

    def to_string(self):
        return ElementTree.tostring(self.element)


class EmbeddedAttachmentStateData(ElementProxy):
    tag = "data"

    ammo = e_property(IntAttribute("ammo"))

    def defaults(self):
        self.ammo = 1

    def to_string(self):
        return ElementTree.tostring(self.element)