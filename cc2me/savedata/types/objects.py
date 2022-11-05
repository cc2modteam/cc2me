import abc
from typing import Tuple, cast, Optional, List, Union, Dict

from .attachment_attributes import UnitAttachment
from .tiles import Tile
from .utils import ElementProxy, LocationMixin, MovableLocationMixin
from .vehicles.embedded_xmlstates.vehicles import EmbeddedAttachmentStateData
from .vehicles.vehicle import Vehicle
from ..constants import get_island_name, IslandTypes, VehicleType, VehicleAttachmentDefinitionIndex, \
    generate_island_seed
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
    def __init__(self, unit: Vehicle):
        super(Unit, self).__init__(unit)
        self.attachments: Dict[int, UnitAttachment] = {}
        self.setup_attachments()

    def setup_attachments(self):
        pass

    def find_attachment_choices(self, attrib: str) -> List[VehicleAttachmentDefinitionIndex]:
        if attrib.endswith("_choices"):
            name = attrib.rsplit("_", 1)[0]
            for item in self.attachments.values():
                if name == f"{item.name}{item.position}":
                    return item.choices
        return None

    def define_attachment_point(self, attachment: UnitAttachment):
        self.attachments[attachment.position] = attachment

    def __getattr__(self, name: str):
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

    @property
    def team_owner(self) -> int:
        return self.vehicle().team_id

    @team_owner.setter
    def team_owner(self, value):
        if value != "None":
            self.vehicle().team_id = int(value)
            team = self.object.cc2obj.team(self.vehicle().team_id)
            if team.human_controlled:
                # add a driver seat for human operation
                self.vehicle().set_attachment(0, VehicleAttachmentDefinitionIndex.DriverSeat)

    @property
    def display_ident(self) -> str:
        return f"{self.vehicle().type.name} ({self.vehicle().id}"

    @property
    def viewable_properties(self) -> List[str]:
        attachment_names = []
        for item in self.attachments.values():
            name = f"{item.name}{item.position}"
            attachment_names.append(name)
        return super(Unit, self).viewable_properties + ["vehicle_type", "alt", "hitpoints"] + attachment_names

    @property
    def hitpoints(self) -> float:
        return self.vehicle().state.data.hitpoints

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

    def setup_attachments(self):
        self.define_attachment_point(UnitAttachment(name="wing", position=1, choices=self.wing_choices))
        self.define_attachment_point(UnitAttachment(name="wing", position=2, choices=self.wing_choices))

    @property
    def wing_choices(self) -> List[VehicleAttachmentDefinitionIndex]:
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


class AirUnitAux(AirUnit):
    @property
    def aux_choices(self) -> List[VehicleAttachmentDefinitionIndex]:
        return [
            VehicleAttachmentDefinitionIndex.Flares,
            VehicleAttachmentDefinitionIndex.SmokeBomb,
            VehicleAttachmentDefinitionIndex.SmokeTrail,
            VehicleAttachmentDefinitionIndex.SonicPulse
        ]


class Razorbill(AirUnitAux):

    def setup_attachments(self):
        super(Razorbill, self).setup_attachments()
        self.define_attachment_point(UnitAttachment(name="aux", position=3, choices=self.aux_choices))
        self.define_attachment_point(UnitAttachment(name="aux", position=4, choices=self.aux_choices))


class Albatross(AirUnit):

    def setup_attachments(self):
        self.define_attachment_point(UnitAttachment(name="turret", position=1, choices=[
                                                        VehicleAttachmentDefinitionIndex.AirObsCam
                                                    ]))
        self.define_attachment_point(UnitAttachment(name="wing", position=2, choices=self.wing_choices))
        self.define_attachment_point(UnitAttachment(name="wing", position=3, choices=self.wing_choices))
        self.define_attachment_point(UnitAttachment(name="wing", position=4, choices=self.wing_choices))
        self.define_attachment_point(UnitAttachment(name="wing", position=5, choices=self.wing_choices))


class Petrel(Albatross):
    pass


class Manta(Albatross, AirUnitAux):

    @property
    def payload_choices(self) -> List[VehicleAttachmentDefinitionIndex]:
        return [
            VehicleAttachmentDefinitionIndex.AirObsCam
        ]

    def setup_attachments(self):
        super(Manta, self).setup_attachments()
        self.define_attachment_point(
            UnitAttachment(name="bay", position=6, choices=self.payload_choices)
        )
        self.define_attachment_point(
            UnitAttachment(name="aux", position=7, choices=self.aux_choices)
        )
        self.define_attachment_point(
            UnitAttachment(name="aux", position=8, choices=self.aux_choices)
        )


class GroundTurreted(Unit):

    def setup_attachments(self):
        self.define_attachment_point(UnitAttachment(name="turret", position=1, choices=self.turret_choices))
        self.define_attachment_point(UnitAttachment(name="aux", position=2, choices=self.aux_choices))
        self.define_attachment_point(UnitAttachment(name="aux", position=3, choices=self.aux_choices))

    @property
    def turret_choices(self) -> List[VehicleAttachmentDefinitionIndex]:
        return [
            VehicleAttachmentDefinitionIndex.CIWS,
            VehicleAttachmentDefinitionIndex.Gun30mm,
            VehicleAttachmentDefinitionIndex.Gun40mm,
            VehicleAttachmentDefinitionIndex.Radar,
            VehicleAttachmentDefinitionIndex.ObsCam,
            VehicleAttachmentDefinitionIndex.MissileIRLauncher,
        ]

    @property
    def aux_choices(self) -> List[VehicleAttachmentDefinitionIndex]:
        return [
            VehicleAttachmentDefinitionIndex.SmallCam,
            VehicleAttachmentDefinitionIndex.SmokeBomb,
            VehicleAttachmentDefinitionIndex.SonicPulse,
            VehicleAttachmentDefinitionIndex.SmokeTrail,
            VehicleAttachmentDefinitionIndex.Flares,
        ]


class Seal(GroundTurreted):
    pass


class Walrus(GroundTurreted):
    pass


class Bear(GroundTurreted):

    def setup_attachments(self):
        self.define_attachment_point(UnitAttachment(name="turret", position=2, choices=self.turret_choices))
        self.define_attachment_point(UnitAttachment(name="aux", position=1, choices=self.aux_choices))
        self.define_attachment_point(UnitAttachment(name="aux", position=3, choices=self.aux_choices))


class Ship(Unit):
    @staticmethod
    def ship_attachments() -> List[VehicleAttachmentDefinitionIndex]:
        return [
            VehicleAttachmentDefinitionIndex.ShipCam,
            VehicleAttachmentDefinitionIndex.ShipCIWS,
            VehicleAttachmentDefinitionIndex.ShipTorpedo,
            VehicleAttachmentDefinitionIndex.ShipGun160mm,
            VehicleAttachmentDefinitionIndex.CruiseMissile,
        ]


class Carrier(Ship):
    def setup_attachments(self):
        for i in range(14):
            self.define_attachment_point(UnitAttachment(name="carrier", position=i, choices=None))


class Needlefish(Ship):

    def setup_attachments(self):
        self.define_attachment_point(UnitAttachment(name="deck",
                                                    position=1,
                                                    choices=self.ship_attachments()))
        self.define_attachment_point(UnitAttachment(name="deck",
                                                    position=2,
                                                    choices=self.ship_attachments()))


class Swordfish(Needlefish):

    def setup_attachments(self):
        super(Swordfish, self).setup_attachments()
        self.define_attachment_point(UnitAttachment(name="deck",
                                                    position=3,
                                                    choices=self.ship_attachments()))
        self.define_attachment_point(UnitAttachment(name="deck",
                                                    position=4,
                                                    choices=self.ship_attachments()))


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

    return Unit(vehicle)
