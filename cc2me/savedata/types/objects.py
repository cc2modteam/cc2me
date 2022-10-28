"""

"""
import abc
from typing import Tuple, cast, Optional, List, Union

from .tiles import Tile
from .utils import ElementProxy, LocationMixin, MovableLocationMixin
from .vehicles.vehicle import Vehicle
from ..constants import get_island_name, IslandTypes, VehicleType, VehicleAttachmentDefinitionIndex
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


class Island(CC2MapItem):
    def __init__(self, tile: Tile):
        super(Island, self).__init__(tile)

    def tile(self) -> Tile:
        return cast(Tile, self.object)

    @property
    def display_ident(self) -> str:
        return self.name

    @property
    def viewable_properties(self) -> List[str]:
        return super(Island, self).viewable_properties + ["name", "island_type"]

    @property
    def team_owner(self) -> int:
        return self.tile().team_control

    @team_owner.setter
    def team_owner(self, value):
        self.tile().team_control = int(value)

    @property
    def team_owner_choices(self) -> List[int]:
        teams = []
        cc2obj: CC2XMLSave = self.object.cc2obj
        for team in cc2obj.teams:
            teams.append(team.id)
        return teams

    @property
    def name(self):
        return get_island_name(self.tile().id)

    @property
    def island_type(self):
        return IslandTypes.lookup(self.tile().facility.category)

    @island_type.setter
    def island_type(self, value: Union[IslandTypes, str]):
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
    def __init__(self, unit: Vehicle):
        super(Unit, self).__init__(unit)

    @property
    def team_owner(self) -> int:
        return self.vehicle().team_id

    @property
    def team_owner_choices(self) -> List[int]:
        teams = []
        cc2obj: CC2XMLSave = self.object.cc2obj
        for team in cc2obj.teams:
            teams.append(team.id)
        return teams

    @property
    def display_ident(self) -> str:
        return f"{self.vehicle().type.name} ({self.vehicle().id}"

    @property
    def viewable_properties(self) -> List[str]:
        return super(Unit, self).viewable_properties + ["vehicle_type", "alt"]

    def vehicle(self) -> Vehicle:
        return cast(Vehicle, self.object)

    @property
    def vehicle_type(self) -> VehicleType:
        return self.vehicle().type

    @property
    def alt(self) -> float:
        return self.vehicle().loc.y

    def altitude(self, alt: float):
        if isinstance(self.object, MovableLocationMixin):
            temp = cast(MovableLocationMixin, self.object)
            temp.move(temp.loc.z,
                      alt,
                      temp.loc.x)

    def get_attachment(self, attachment_index: int) -> Optional[VehicleAttachmentDefinitionIndex]:
        item = self.vehicle().attachments[attachment_index]
        if item is not None:
            item = VehicleAttachmentDefinitionIndex.lookup(item.definition_index)

        return item


class AirUnit(Unit):
    @property
    def wing0(self) -> Optional[VehicleAttachmentDefinitionIndex]:
        return self.get_attachment(1)

    @property
    def wing0_choices(self) -> List[VehicleAttachmentDefinitionIndex]:
        return [
            VehicleAttachmentDefinitionIndex.Gun20mm,
            VehicleAttachmentDefinitionIndex.MissileIR,
            VehicleAttachmentDefinitionIndex.MissileAA,
            VehicleAttachmentDefinitionIndex.MissileTV,
            VehicleAttachmentDefinitionIndex.MissileLaser,
            VehicleAttachmentDefinitionIndex.Torpedo,
            VehicleAttachmentDefinitionIndex.TorpedoCountermesure,
            VehicleAttachmentDefinitionIndex.Noisemaker,
            VehicleAttachmentDefinitionIndex.Bomb0,
            VehicleAttachmentDefinitionIndex.Bomb1,
            VehicleAttachmentDefinitionIndex.Bomb2,
            VehicleAttachmentDefinitionIndex.FuelTank
        ]

    @property
    def wing1_choices(self) -> List[VehicleAttachmentDefinitionIndex]:
        return self.wing0_choices

    @property
    def wing1(self) -> Optional[VehicleAttachmentDefinitionIndex]:
        return self.get_attachment(2)


class AirUnitAux(AirUnit):
    @property
    def aux0_choices(self) -> List[VehicleAttachmentDefinitionIndex]:
        return [
            VehicleAttachmentDefinitionIndex.Flares,
            VehicleAttachmentDefinitionIndex.SmokeBomb,
            VehicleAttachmentDefinitionIndex.SmokeTrail,
            VehicleAttachmentDefinitionIndex.SonicPulse
        ]

    @property
    def aux1_choices(self) -> List[VehicleAttachmentDefinitionIndex]:
        return self.aux0_choices


class Razorbill(AirUnitAux):
    @property
    def aux0(self) -> Optional[VehicleAttachmentDefinitionIndex]:
        return self.get_attachment(3)

    @property
    def aux1(self) -> Optional[VehicleAttachmentDefinitionIndex]:
        return self.get_attachment(4)

    @property
    def viewable_properties(self) -> List[str]:
        return super(Razorbill, self).viewable_properties + ["wing0", "wing1", "aux0", "aux1"]


class Albatross(AirUnit):

    @property
    def turret(self) -> Optional[VehicleAttachmentDefinitionIndex]:
        return self.get_attachment(1)

    @property
    def turret_choices(self) -> List[VehicleAttachmentDefinitionIndex]:
        return [
            VehicleAttachmentDefinitionIndex.AirCam
        ]

    @property
    def wing0(self) -> Optional[VehicleAttachmentDefinitionIndex]:
        return self.get_attachment(2)

    @property
    def wing1(self) -> Optional[VehicleAttachmentDefinitionIndex]:
        return self.get_attachment(4)

    @property
    def wing2_choices(self) -> List[VehicleAttachmentDefinitionIndex]:
        return self.wing0_choices

    @property
    def wing2(self) -> Optional[VehicleAttachmentDefinitionIndex]:
        return self.get_attachment(5)

    @property
    def wing3_choices(self) -> List[VehicleAttachmentDefinitionIndex]:
        return self.wing0_choices

    @property
    def wing3(self) -> Optional[VehicleAttachmentDefinitionIndex]:
        return self.get_attachment(3)

    @property
    def viewable_properties(self) -> List[str]:
        return super(Albatross, self).viewable_properties + ["turret", "wing0", "wing1", "wing2", "wing3"]


class Petrel(Albatross):
    pass


class Manta(Albatross):

    @property
    def payload(self) -> Optional[VehicleAttachmentDefinitionIndex]:
        return self.get_attachment(6)

    @property
    def payload_choices(self) -> List[VehicleAttachmentDefinitionIndex]:
        return [
            VehicleAttachmentDefinitionIndex.AWACS
        ]

    @property
    def aux0(self) -> Optional[VehicleAttachmentDefinitionIndex]:
        return self.get_attachment(7)

    @property
    def aux1(self) -> Optional[VehicleAttachmentDefinitionIndex]:
        return self.get_attachment(8)

    @property
    def viewable_properties(self) -> List[str]:
        return super(Manta, self).viewable_properties + ["payload", "aux0", "aux1"]


class GroundTurreted(Unit):
    @property
    def turret(self) -> Optional[VehicleAttachmentDefinitionIndex]:
        return self.get_attachment(1)

    @property
    def aux0(self) -> Optional[VehicleAttachmentDefinitionIndex]:
        return self.get_attachment(2)

    @property
    def aux1(self) -> Optional[VehicleAttachmentDefinitionIndex]:
        return self.get_attachment(3)

    @property
    def turret_choices(self) -> List[VehicleAttachmentDefinitionIndex]:
        return [
            VehicleAttachmentDefinitionIndex.Gun30mm,
            VehicleAttachmentDefinitionIndex.Gun40mm,
            VehicleAttachmentDefinitionIndex.Radar,
            VehicleAttachmentDefinitionIndex.ObsCam,
            VehicleAttachmentDefinitionIndex.MissileIRLauncher
        ]

    @property
    def aux0_choices(self) -> List[VehicleAttachmentDefinitionIndex]:
        return [
            VehicleAttachmentDefinitionIndex.Flares,
            VehicleAttachmentDefinitionIndex.SmallCam,
            VehicleAttachmentDefinitionIndex.SmokeBomb,
            VehicleAttachmentDefinitionIndex.SmokeTrail,
            VehicleAttachmentDefinitionIndex.SonicPulse
        ]

    @property
    def aux1_choices(self) -> List[VehicleAttachmentDefinitionIndex]:
        return self.aux0_choices

    @property
    def viewable_properties(self) -> List[str]:
        return super(GroundTurreted, self).viewable_properties + ["turret", "aux0", "aux1"]


class Seal(GroundTurreted):
    pass


class Walrus(GroundTurreted):
    pass


class Bear(GroundTurreted):

    @property
    def turret(self) -> Optional[VehicleAttachmentDefinitionIndex]:
        return self.get_attachment(2)

    @property
    def turret_choices(self) -> List[VehicleAttachmentDefinitionIndex]:
        return [
            VehicleAttachmentDefinitionIndex.Gun100mm,
            VehicleAttachmentDefinitionIndex.Gun100mmHeavy,
            VehicleAttachmentDefinitionIndex.Gun120mm,
        ]

    @property
    def aux0(self) -> Optional[VehicleAttachmentDefinitionIndex]:
        return self.get_attachment(3)

    @property
    def aux1(self) -> Optional[VehicleAttachmentDefinitionIndex]:
        return self.get_attachment(1)


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

    return Unit(vehicle)
