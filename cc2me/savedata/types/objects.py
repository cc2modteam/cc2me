import abc
from typing import Tuple, cast, Optional, List, Union, Dict, Iterable

from .attachment_attributes import UnitAttachment
from .spawndata import VehicleSpawn
from .tiles import Tile
from .utils import ElementProxy, LocationMixin, MovableLocationMixin
from .vehicles.embedded_xmlstates.vehicles import EmbeddedAttachmentStateData
from .vehicles.vehicle import Vehicle
from ..constants import get_island_name, IslandTypes, VehicleType, VehicleAttachmentDefinitionIndex, \
    generate_island_seed, get_default_hitpoints
from ..rules import get_unit_attachment_choices, get_unit_attachment_slots
from ..loader import CC2XMLSave

LOC_SCALE_FACTOR = 1000


class CC2MapItem:
    def __init__(self, obj: ElementProxy):
        self.object = obj

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


class Island(CC2MapItem):
    def __init__(self, tile: Tile):
        super(Island, self).__init__(tile)

    def tile(self) -> Tile:
        return cast(Tile, self.object)

    @property
    def display_ident(self) -> str:
        return self.name

    @property
    def alt(self) -> float:
        return self.tile().loc.y

    @property
    def biome(self) -> int:
        return self.tile().biome_type

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
        return super(Island, self).viewable_properties + ["name", "island_type", "alt", "seed", "biome", "size"]

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
        return IslandTypes.lookup(self.tile().facility.category)

    @island_type.setter
    def island_type(self, value: Union[IslandTypes, str]):
        if value != "None":
            if isinstance(value, str):
                value = IslandTypes.reverse_lookup(value)
            self.tile().facility.category = value.value

    @property
    def island_type_choices(self) -> List[IslandTypes]:
        return [
            IslandTypes.Warehouse,
            IslandTypes.Air_Units,
            IslandTypes.Barges,
            IslandTypes.Surface_Units,
            IslandTypes.Large_Munitions,
            IslandTypes.Small_Munitions,
            IslandTypes.Turrets,
            IslandTypes.Fuel
        ]


class Unit(CC2MapItem):
    def __init__(self, unit: Union[Vehicle, VehicleSpawn]):
        super(Unit, self).__init__(unit)
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

        raise AttributeError(name)

    def __setattr__(self, key: str, value):
        if "attachments" in self.__dict__:
            attachment = self.find_attachment(key)
            if attachment is not None:
                self.set_attachment(attachment.position, value)
                return

        super(Unit, self).__setattr__(key, value)

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
        return f"{self.vehicle().type.name} ({self.vehicle().id}"

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
        return super(Unit, self).viewable_properties + ["vehicle_type", "alt", "hitpoints"] + list(attachment_names)

    @property
    def hitpoints(self) -> float:
        return self.vehicle().state.data.hitpoints

    @hitpoints.setter
    def hitpoints(self, value: Union[float, str]):
        if isinstance(value, str):
            if value.isdecimal():
                value = float(value)
        if value:
            data = self.vehicle().state.data
            data.hitpoints = value
            self.vehicle().state.data = data

    @property
    def hitpoints_choices(self) -> List[float]:
        values = [
            self.hitpoints,
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
        self.vehicle().state.attachments[attachment_index].data = data


class AirUnit(Unit):
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


class GroundTurreted(Unit):
    pass

class Seal(GroundTurreted):
    pass


class Walrus(GroundTurreted):
    pass


class Bear(GroundTurreted):
    pass


class Ship(Unit):
    pass


class Carrier(Ship):
    def setup_attachments(self):
        for i in range(14):
            self.define_attachment_point(UnitAttachment(name="carrier", position=i, choices=None))


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


class Spawn(Unit):

    def __init__(self, vspawn: VehicleSpawn, island: Tile):
        super(Spawn, self).__init__(vspawn)
        self.tile = island

    def __str__(self):
        return f"{self.display_ident}"

    def xsetup_attachments(self):
        data_attachments = self.spawn().data.attachments.items()
        for item in data_attachments:
            self.define_attachment_point(UnitAttachment(name="",
                                                        position=len(self.attachments),
                                                        choices=[VehicleAttachmentDefinitionIndex.lookup(
                                                            item.definition_index)]))

    def get_attachment(self, attachment_index: int) -> Optional[VehicleAttachmentDefinitionIndex]:
        items = self.spawn().data.attachments.items()
        if len(items) > attachment_index:
            return VehicleAttachmentDefinitionIndex.lookup(items[attachment_index].definition_index)
        return None

    def get_attachment_state(self, attachment_index: int) -> Optional[EmbeddedAttachmentStateData]:
        return None

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


def get_unit(vehicle: Vehicle) -> Unit:
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

    return Unit(vehicle)
