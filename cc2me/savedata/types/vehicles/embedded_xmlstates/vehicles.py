from typing import List
from xml.etree import ElementTree
from ...utils import ElementProxy, IntAttribute, e_property, FloatAttribute, BoolAttribute


class EmbeddedData(ElementProxy):
    tag = "data"

    def to_string(self):
        buf = '<?xml version="1.0" encoding="UTF-8"?>'
        buf += ElementTree.tostring(self.element, short_empty_elements=False, encoding="unicode")
        return buf


class EmbeddedVehicleStateData(EmbeddedData):
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


class EmbeddedAttachmentStateData(EmbeddedData):
    ammo = e_property(IntAttribute("ammo"))
    fuel_capacity = e_property(FloatAttribute("fuel_capacity"))
    fuel_remaining = e_property(FloatAttribute("fuel_remaining"))
