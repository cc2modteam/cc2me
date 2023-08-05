import abc
from typing import Tuple, cast, Optional, List, Union, Dict, Any, Protocol

from .attachment_attributes import UnitAttachment
from .save import (
    VehicleSpawn, VehicleSpawnAttachment, Tile, Vehicle, Waypoint,
    EmbeddedAttachmentStateData, Inventory)
from .utils import ElementProxy, LocationMixin, MovableLocationMixin
from ..constants import (
    get_island_name, TileTypes, VehicleType, VehicleAttachmentDefinitionIndex,
    generate_island_seed, get_default_hitpoints, InventoryIndex,
    BIOMES, get_waypoint_type_kind)
from ..rules import (
    get_unit_attachment_choices, get_unit_attachment_slots)

from .save import CC2XMLSave

LOC_SCALE_FACTOR = 2000


class DynamicGetter(Protocol):
    def __call__(self, name: str) -> Any:
        pass


class DynamicSetter(Protocol):
    def __call__(self, name: str, value: Any) -> None:
        pass


class DynamicNamedAttribute:
    def __init__(self, name: str, getter: DynamicGetter, setter: DynamicSetter, argname: Optional[str] = None):
        self.name = name
        self.argname = name
        if argname:
            self.argname = argname
        self.getter = getter
        self.setter = setter

    def get(self) -> Any:
        return self.getter(self.argname)

    def set(self, value: Any):
        self.setter(self.argname, value)


class MapItem:
    def __init__(self, obj: ElementProxy):
        self.object = obj
        self.dynamic_attribs: Dict[str, DynamicNamedAttribute] = {}

    @property
    def display_ident(self) -> str:
        return "unknown"

    @property
    def viewable_properties(self) -> List[str]:
        return ["team_owner", "loc"]

    @property
    @abc.abstractmethod
    def team_owner(self) -> int:
        pass

    @property
    def team_owner_choices(self) -> List[int]:
        teams = []
        cc2obj: CC2XMLSave = self.object.cc2obj
        if cc2obj:
            for team in cc2obj.teams:
                teams.append(team.id)
        return teams

    @property
    def text(self) -> Optional[str]:
        return None

    @property
    def loc(self) -> Optional[Tuple[float, float]]:
        if isinstance(self.object, LocationMixin):
            temp = cast(LocationMixin, self.object)
            # map uses lat+long (y, then x) remember to swap!
            # in CC2 saves, Z is lattitude, X is longditude, Y is altitude
            return temp.loc.z / LOC_SCALE_FACTOR, temp.loc.x / LOC_SCALE_FACTOR
        return None

    def move(self, world_lat, world_lon):
        if isinstance(self.object, MovableLocationMixin):
            temp = cast(MovableLocationMixin, self.object)
            temp.move(world_lon * LOC_SCALE_FACTOR,
                      temp.loc.y,
                      world_lat * LOC_SCALE_FACTOR)

    def __str__(self):
        out = f"{self.display_ident}:\n"
        for prop in self.viewable_properties:
            out += f" {prop} {getattr(self, prop)}\n"
        return out


class MapWaypoint(MapItem):

    def __init__(self, unit: "MapVehicle", obj: ElementProxy):
        self.unit = unit
        super().__init__(obj)

    @property
    def display_ident(self) -> str:
        return f"waypoint of {self.unit.display_ident}"

    @property
    def waypoint_order(self) -> str:
        return get_waypoint_type_kind(self.type)

    @property
    def target_tile_id(self) -> str:
        return self.object.element.attrib.get("target_tile_id", "")

    @property
    def target_vehicle_id(self) -> str:
        return self.object.element.attrib.get("target_vehicle_id", "")

    @property
    def wait_group(self) -> str:
        return self.object.element.attrib.get("wait_group", "")

    @property
    def type(self) -> str:
        return self.object.element.attrib.get("type", "")

    @property
    def viewable_properties(self) -> List[str]:
        return ["team_owner", "waypoint_order", "loc", "alt", "target_tile_id", "target_vehicle_id", "wait_group", "type"]

    @property
    def alt(self) -> int:
        return int(self.waypoint().loc.y)

    @property
    def text(self) -> Optional[str]:
        return f"({self.unit.vehicle().id})"

    def waypoint(self) -> Waypoint:
        return cast(Waypoint, self.object)

    @property
    def team_owner(self) -> int:
        return self.unit.team_owner

    @property
    def loc(self) -> Optional[Tuple[float, float]]:
        offset = self.waypoint().loc
        lat = offset.x
        lon = offset.z

        return lon / LOC_SCALE_FACTOR, lat / LOC_SCALE_FACTOR

    def move(self, world_lat, world_lon):
        wpt = self.waypoint()

        wpt.set_location(x=world_lat * LOC_SCALE_FACTOR,
                         z=world_lon * LOC_SCALE_FACTOR)
        self.object.sync()


class MapTile(MapItem):
    def __init__(self, tile: Tile):
        super(MapTile, self).__init__(tile)

    def tile(self) -> Tile:
        return cast(Tile, self.object)

    @property
    def display_ident(self) -> str:
        return self.name

    @property
    def difficulty(self) -> float:
        return self.tile().difficulty_factor

    @difficulty.setter
    def difficulty(self, value):
        if isinstance(value, str):
            value = float(value)
        if isinstance(value, float):
            self.tile().difficulty_factor = value

    @property
    def difficulty_choices(self) -> List[str]:
        return [
            "0.0",
            "0.5",
            "0.7",
            "1.0"
        ]

    @property
    def alt(self) -> float:
        return self.tile().loc.y

    @property
    def biome(self) -> int:
        return self.tile().biome_type

    @biome.setter
    def biome(self, type: int):
        self.tile().biome_type = type

    @property
    def biome_choices(self) -> List[str]:
        return [str(x) for x in BIOMES]

    @property
    def size(self) -> float:
        return self.tile().island_radius

    @size.setter
    def size(self, value):
        self.tile().island_radius = value

    @property
    def size_choices(self) -> List[str]:
        return [
            "500",
            "1000",
            "2000",
            "3500",
            "5000",
            "6000",
            "7500",
        ]

    @property
    def seed(self) -> int:
        return self.tile().seed

    @seed.setter
    def seed(self, value):
        self.tile().seed = value

    @property
    def seed_choices(self) -> List[str]:
        return [
            str(self.seed),
            str(generate_island_seed()),
            str(generate_island_seed()),
            str(generate_island_seed()),
        ]

    @property
    def viewable_properties(self) -> List[str]:
        return super(MapTile, self).viewable_properties + ["name", "island_type", "alt", "seed", "biome", "size", "difficulty"]

    @property
    def team_owner(self) -> int:
        return self.tile().team_control

    @team_owner.setter
    def team_owner(self, value):
        if value != "None":
            self.tile().team_control = int(value)
            self.tile().spawn_data.team_id = int(value)

    @property
    def name(self):
        return get_island_name(self.tile().id)

    @property
    def island_type(self):
        return TileTypes.lookup(self.tile().facility.category)

    @island_type.setter
    def island_type(self, value: Union[TileTypes, str]):
        if value != "None":
            if isinstance(value, str):
                value = TileTypes.reverse_lookup(value)
            self.tile().facility.category = value.value

    @property
    def island_type_choices(self) -> List[TileTypes]:
        return [
            TileTypes.Warehouse,
            TileTypes.Air_Units,
            TileTypes.Barges,
            TileTypes.Surface_Units,
            TileTypes.Large_Munitions,
            TileTypes.Small_Munitions,
            TileTypes.Turrets,
            TileTypes.Utility,
            TileTypes.Fuel
        ]


class MapVehicle(MapItem):

    show_waypoints = True

    @property
    def v_id(self) -> int:
        return int(self.object.element.attrib.get("id", -1))

    def __init__(self, unit: Union[Vehicle, VehicleSpawn]):
        super(MapVehicle, self).__init__(unit)
        self.attachments: Dict[int, UnitAttachment] = {}
        self.setup_attachments()

    def setup_attachments(self):
        slots = get_unit_attachment_slots(self.vehicle_type)
        for slot in slots:
            self.define_attachment_point(
                UnitAttachment(name="attach", position=slot,
                               choices=get_unit_attachment_choices(self.vehicle_type, slot))
            )

    def find_attachment(self, name: str) -> Optional[UnitAttachment]:
        for item in self.attachments.values():
            if f"{name}" == f"{item.name}{item.position}":
                return item
        return None

    def find_attachment_choices(self, attrib: str) -> Optional[List[VehicleAttachmentDefinitionIndex]]:
        if attrib.endswith("_choices"):
            name = attrib.rsplit("_", 1)[0]
            for item in self.attachments.values():
                if name == f"{item.name}{item.position}":
                    return item.choices
        return None

    def define_attachment_point(self, attachment: UnitAttachment):
        self.attachments[attachment.position] = attachment

    def __getattr__(self, name: str):
        if "attachments" in self.__dict__:
            if name.endswith("_choices"):
                choices = self.find_attachment_choices(name)
                if choices is not None:
                    return choices

            else:
                for item in self.attachments.values():
                    item: UnitAttachment
                    if name == f"{item.name}{item.position}":
                        return self.get_attachment(item.position)

        if name in dir(self):
            return getattr(type(self), name).fget(self)
        raise AttributeError(name)

    def __setattr__(self, key: str, value):
        if "attachments" in self.__dict__:
            attachment = self.find_attachment(key)
            if attachment is not None:
                self.set_attachment(attachment.position, value)
                return

        super(MapVehicle, self).__setattr__(key, value)

    @property
    def team_owner(self) -> int:
        return self.vehicle().team_id

    @team_owner.setter
    def team_owner(self, value):
        if value != "None":
            self.vehicle().team_id = int(value)
            team = self.object.cc2obj.team(self.vehicle().team_id)
            if team.human_controlled or not team.is_ai_controlled:
                # add a driver seat for human operation
                self.vehicle().set_attachment(0, VehicleAttachmentDefinitionIndex.DriverSeat)

    @property
    def display_ident(self) -> str:
        return f"{self.vehicle().type.name} (ID {self.vehicle().id})"

    @property
    def dynamic_attachment_names(self) -> List[str]:
        attachment_names = []
        for item in self.attachments.values():
            name = f"{item.name}{item.position}"
            attachment_names.append(name)
        return attachment_names

    @property
    def viewable_properties(self) -> List[str]:
        attachment_names = self.dynamic_attachment_names
        return super(MapVehicle, self).viewable_properties + ["vehicle_type", "alt", "hitpoints"] + list(attachment_names)

    @property
    def hitpoints(self) -> float:
        return self.vehicle().state.data.hitpoints

    @hitpoints.setter
    def hitpoints(self, value: Union[float, str]):
        if isinstance(value, str):
            if value.isdecimal():
                value = float(value)
        self.vehicle().state.data.hitpoints = value
        self.vehicle().sync()

    @property
    def hitpoints_choices(self) -> List[float]:
        values = [
            self.hitpoints,
            int(self.hitpoints / 5),
        ]

        default_max = get_default_hitpoints(self.vehicle_type)
        if default_max:
            values.append(int(default_max / 2))
            values.append(default_max)

        return values

    def vehicle(self) -> Vehicle:
        return cast(Vehicle, self.object)

    @property
    def vehicle_type(self) -> VehicleType:
        return self.vehicle().type

    @property
    def alt(self) -> float:
        return self.vehicle().transform.ty

    @alt.setter
    def alt(self, value: float):
        if value != "None":
            self.vehicle().move(self.vehicle().transform.tx,
                                float(value),
                                self.vehicle().transform.tz
                                )

    @property
    def alt_choices(self) -> List[float]:
        return [
            self.alt,
            -10,
            -1,
            5,
            15,
            50,
            200,
            800,
            1200,
            10000,  # just for fun
        ]

    def altitude(self, alt: float):
        if isinstance(self.object, MovableLocationMixin):
            temp = cast(MovableLocationMixin, self.object)
            temp.move(temp.loc.z,
                      alt,
                      temp.loc.x)

    def get_attachment(self, attachment_index: int) -> Optional[VehicleAttachmentDefinitionIndex]:
        return self.vehicle().get_attachment(attachment_index)

    def set_attachment(self, attachment_index: int, value: Optional[VehicleAttachmentDefinitionIndex]):
        self.vehicle().set_attachment(attachment_index, value)

    def get_attachment_state(self, attachment_index: int) -> Optional[EmbeddedAttachmentStateData]:
        a_state_container = self.vehicle().get_attachment_state(attachment_index)
        if a_state_container:
            return a_state_container.data
        return EmbeddedAttachmentStateData(element=None)

    def set_attachment_state(self, attachment_index: int, data: EmbeddedAttachmentStateData):
        if self.vehicle().state.attachments[attachment_index] is not None:
            # not all attachments have state
            self.vehicle().state.attachments[attachment_index].data = data


class AirUnit(MapVehicle):
    pass


class AirUnitAux(AirUnit):
    pass


class Razorbill(AirUnitAux):
    pass


class Albatross(AirUnit):
    pass


class Petrel(Albatross):
    pass


class Manta(Albatross, AirUnitAux):
    pass


class GroundTurreted(MapVehicle):
    pass


class Turret(GroundTurreted):
    pass


class Seal(GroundTurreted):
    pass


class Walrus(GroundTurreted):
    pass


class Bear(GroundTurreted):
    pass


class Ship(MapVehicle):
    pass


class Carrier(Ship):

    def __init__(self, unit: Union[Vehicle, VehicleSpawn]):
        super(Carrier, self).__init__(unit)
        self.dynamic_attribs["stored_fuel"] = DynamicNamedAttribute(
            InventoryIndex.Fuel.name,
            self.get_inventory_item,
            self.set_inventory_item
        )

    def setup_attachments(self):
        for i in range(14):
            self.define_attachment_point(UnitAttachment(name="carrier", position=i, choices=None))

    def get_inventory(self) -> Inventory:
        embedded_data = self.vehicle().state.data
        values = cast(Inventory, embedded_data.get_default_child_by_tag(Inventory))
        return values

    def get_inventory_item(self, name: str) -> int:
        offset: int = InventoryIndex.reverse_lookup(name).value
        return self.get_inventory().item_quantities.items()[offset]

    def set_inventory_item(self, name: str, count: int):
        pass
        #offset: int = InventoryIndex.reverse_lookup(name).value
        #current = self.get_inventory()
        #current.children()


class Barge(Ship):

    def setup_attachments(self):
        self.define_attachment_point(
            UnitAttachment(name="seat",
                           position=0,
                           choices=[
                               VehicleAttachmentDefinitionIndex.DriverSeat,
                           ]))


class Needlefish(Ship):
    pass


class Swordfish(Needlefish):
    pass


class Spawn(MapVehicle):

    def __init__(self, vspawn: VehicleSpawn, island: Tile):
        super(Spawn, self).__init__(vspawn)
        self.tile = island

    def __str__(self):
        return f"{self.display_ident}"

    def _get_attachment_item(self, attachment_index: int) -> Optional[VehicleSpawnAttachment]:
        items = self.spawn().data.attachments.items()
        if len(items) > attachment_index:
            return items[attachment_index]
        return None

    def get_attachment(self, attachment_index: int) -> Optional[VehicleAttachmentDefinitionIndex]:
        item = self._get_attachment_item(attachment_index)
        if item is not None:
            return VehicleAttachmentDefinitionIndex.lookup(item.definition_index)
        return None

    def set_attachment(self, attachment_index: int, value: Optional[VehicleAttachmentDefinitionIndex]):
        item = self._get_attachment_item(attachment_index)
        if item is not None:
            item.definition_index = VehicleAttachmentDefinitionIndex.reverse_lookup(value).value

    def get_attachment_state(self, attachment_index: int) -> Optional[EmbeddedAttachmentStateData]:
        item = self._get_attachment_item(attachment_index)
        data = EmbeddedAttachmentStateData()
        if item is not None:
            data.ammo = item.ammo
        return data

    def set_attachment_state(self, attachment_index: int, data: EmbeddedAttachmentStateData):
        item = self._get_attachment_item(attachment_index)
        if item is not None:
            if data:
                item.ammo = data.ammo

    def vehicle(self) -> Optional[Vehicle]:
        return None

    @property
    def vehicle_type(self) -> VehicleType:
        return VehicleType(self.spawn().data.definition_index)

    @property
    def viewable_properties(self) -> List[str]:
        return ["vehicle_type", "team_owner", "loc", "alt"] + list(self.dynamic_attachment_names)

    @property
    def alt(self) -> float:
        return self.spawn().data.world_position.y

    @alt.setter
    def alt(self, value: float):
        data = self.spawn().data
        data.world_position.y = value
        self.spawn().data = data

    @property
    def display_ident(self) -> str:
        return f"spawn {VehicleType.lookup(self.spawn().data.definition_index)} {self.spawn().data.respawn_id}"

    @property
    def team_owner(self) -> int:
        return self.tile.team_control

    def spawn(self) -> VehicleSpawn:
        return VehicleSpawn(self.object.element)


class Jetty(MapVehicle):

    show_waypoints = False

    @property
    def viewable_properties(self) -> List[str]:
        return ["team_owner", "loc", "alt"]


def get_unit(vehicle: Vehicle) -> MapVehicle:
    if vehicle.type == VehicleType.Turret:
        return Turret(vehicle)
    if vehicle.type == VehicleType.Seal:
        return Seal(vehicle)
    elif vehicle.type == VehicleType.Walrus:
        return Walrus(vehicle)
    elif vehicle.type == VehicleType.Bear:
        return Bear(vehicle)
    elif vehicle.type == VehicleType.Razorbill:
        return Razorbill(vehicle)
    elif vehicle.type == VehicleType.Albatross:
        return Albatross(vehicle)
    elif vehicle.type == VehicleType.Petrel:
        return Petrel(vehicle)
    elif vehicle.type == VehicleType.Manta:
        return Manta(vehicle)
    elif vehicle.type == VehicleType.Swordfish:
        return Swordfish(vehicle)
    elif vehicle.type == VehicleType.Needlefish:
        return Needlefish(vehicle)
    elif vehicle.type == VehicleType.Carrier:
        return Carrier(vehicle)
    elif vehicle.type == VehicleType.Barge:
        return Barge(vehicle)
    elif vehicle.type == VehicleType.Jetty:
        return Jetty(vehicle)

    return MapVehicle(vehicle)
