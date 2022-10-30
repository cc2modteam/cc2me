import random
from abc import ABC
from enum import Enum
from typing import cast, List, Optional, Union

MAX_INTEGER = 4294967295

MIN_TILE_SEED = 6000
MAX_TILE_SEED = 20000

POS_Y_SEABOTTOM = -1

BIOME_GREEN_PINES = 0
BIOME_SNOW_PINES = 1
BIOME_SANDY_PINES = 3
BIOME_DARK_MESAS = 7

VEHICLE_DEF_CARRIER = 0


def generate_island_seed() -> int:
    return random.randint(MIN_TILE_SEED, MAX_TILE_SEED)


class XEnum(Enum):
    @classmethod
    def lookup(cls, value):
        for item in cls:
            if item.value == value:
                return item
        raise KeyError(value)

    @classmethod
    def reverse_lookup(cls, name):
        for item in cls:
            if item.name == name:
                return item
        return KeyError(name)


class IntEnum(XEnum):
    @property
    def int(self) -> int:
        return cast(int, self.value)

    def __str__(self):
        return str(self.name)

    @classmethod
    def get_name(cls, num: int):
        for item in cls:
            if item.value == num:
                return str(item.name)
        return f"Unknown {num}"


class VehicleType(IntEnum):
    Albatross = 8
    Barge = 16
    Bear = 6
    Carrier = 0
    Droid = 97
    Jetty = 64
    Lifeboat = 57
    Manta = 10
    Mule = 88
    Needlefish = 77
    Petrel = 14
    Razorbill = 12
    Seal = 2
    Swordfish = 79
    Turret = 59
    VirusBot = 58
    Walrus = 4


class VehicleAttachmentDefinitionIndex(IntEnum):
    AWACS = 41
    AirObsCam = 39
    BattleDroids = 100
    Bomb0 = 31
    Bomb1 = 32
    Bomb2 = 33
    CIWS = 24
    CruiseMissile = 29
    ShipCIWS = 26
    ShipCam = 30
    DriverSeat = 38
    Flares = 43
    FuelTank = 42
    Gun100mm = 18
    Gun100mmHeavy = 86
    Gun120mm = 19
    ShipGun160mm = 20
    Gun15mm = 87
    Gun20mm = 21
    Gun30mm = 17
    Gun40mm = 85
    MissileAA = 36
    MissileAALauncher = 27
    MissileIR = 34
    MissileIRLauncher = 25
    MissileLaser = 35
    MissileTV = 72
    Noisemaker = 73
    ObsCam = 37
    Radar = 81
    Rearm100mm = 93
    Rearm120mm = 94
    Rearm20mm = 90
    Rearm30mm = 91
    Rearm40mm = 92
    RearmIR = 96
    Refuel = 95
    RocketPod = 22
    SmallCam = 40
    SmokeBomb = 83
    SmokeTrail = 84
    SonicPulse = 82
    Torpedo = 70
    TorpedoCountermesure = 74
    ShipTorpedo = 75
    VirusBot = 23


class IslandTypes(IntEnum):
    Warehouse = 0
    Small_Munitions = 1
    Large_Munitions = 2
    Turrets = 3
    Utility = 4
    Surface_Units = 5
    Air_Units = 6
    Fuel = 7
    Barges = 8


ISLAND_NAMES = ['VULCAN', 'ELWOOD', 'BYRNE', 'CEREBUS', 'CHARISSA', 'DUESSA', 'SOCRATES', 'GENETIX', 'EDGELEY',
                'TOKAMAK', 'AVERNUS', 'ACHERON', 'MAGMA', 'IGNEOUS', 'ODRACIR', 'NAIADES', 'BEACON', 'DIONYSIUS',
                'BACCHUS', 'BELTEMPEST', 'BARDLAND', 'BEDROCK', 'GRANITE', 'HYTAC', 'MNEMONIC', 'STORM', 'TERMINUS',
                'THERMOPYLAE', 'STAVROS', 'EVERGREEN', 'CHERENKOV', 'LINGARD', 'VATTLAND', 'JUDGEMENT', 'FULCRUM',
                'OUTCROP', 'ENDYMION', 'SOMNUS', 'SPLINTER', 'FORNAX', 'STEADFAST', 'TAKSAVEN', 'FRONTIER', 'DEADLOCK',
                'URSULA', 'SANCTUARY', 'OBSIDIAN', 'ARACHNID', 'TWILIGHT', 'MILESTONE', 'INFERNO', 'TREASURE',
                'FEARS', 'EDGE', 'TRAFFIC', 'STYX', 'HADES', 'KOUYATE', 'OUTPOST', 'BOUNTYBAR', 'MEDUSA', 'ISOLUS',
                'SERRANO', 'CHARIBDIS', 'NEMESIS']


def get_island_name(island_id: int) -> str:
    try:
        return ISLAND_NAMES[island_id - 1]
    except IndexError:
        return "Island {island_id}"


class Capacity(ABC):

    attribs: List[str] = []

    def __init__(self,
                 attachment: VehicleAttachmentDefinitionIndex,
                 count: int,
                 *v_types):
        self.attachment = attachment
        self.count = count
        self.vtypes = v_types


class AmmunitionCapacity(Capacity):
    attribs = ["ammo"]


class FuelTankCapacity(Capacity):
    attribs = ["fuel_capacity", "fuel_remaining"]


class InternalFuelCapacity(Capacity):
    attribs = ["internal_fuel_remaining"]

    def __init__(self, count: int, *vtype: VehicleType):
        super(InternalFuelCapacity, self).__init__(VehicleAttachmentDefinitionIndex.FuelTank, count, *vtype)


VEHICLE_CAPACITY = [
    InternalFuelCapacity(2000, VehicleType.Petrel, VehicleType.Manta, VehicleType.Albatross),
    InternalFuelCapacity(1200, VehicleType.Walrus, VehicleType.Bear, VehicleType.Mule),
    InternalFuelCapacity(800, VehicleType.Seal),
    InternalFuelCapacity(400, VehicleType.Razorbill),
    InternalFuelCapacity(1000, VehicleType.Swordfish),
    InternalFuelCapacity(800, VehicleType.Needlefish),
    InternalFuelCapacity(2000, VehicleType.Barge),
]


ATTACHMENT_CAPACITY = [
    AmmunitionCapacity(VehicleAttachmentDefinitionIndex.ShipTorpedo, 4,
                       VehicleType.Needlefish, VehicleType.Swordfish),
    AmmunitionCapacity(VehicleAttachmentDefinitionIndex.ShipCIWS, 100,
                       VehicleType.Needlefish, VehicleType.Swordfish),
    AmmunitionCapacity(VehicleAttachmentDefinitionIndex.CruiseMissile, 10,
                       VehicleType.Needlefish, VehicleType.Swordfish),
    AmmunitionCapacity(VehicleAttachmentDefinitionIndex.AWACS, 1,
                       VehicleType.Manta),
    AmmunitionCapacity(VehicleAttachmentDefinitionIndex.Gun20mm, 400,
                       VehicleType.Manta, VehicleType.Albatross, VehicleType.Razorbill, VehicleType.Petrel),
    AmmunitionCapacity(VehicleAttachmentDefinitionIndex.Gun30mm, 500,
                       VehicleType.Seal, VehicleType.Walrus),
    AmmunitionCapacity(VehicleAttachmentDefinitionIndex.Gun40mm, 400,
                       VehicleType.Seal, VehicleType.Walrus),
    AmmunitionCapacity(VehicleAttachmentDefinitionIndex.MissileIRLauncher, 4,
                       VehicleType.Seal, VehicleType.Walrus),
    AmmunitionCapacity(VehicleAttachmentDefinitionIndex.Gun100mm, 40,
                       VehicleType.Bear),
    AmmunitionCapacity(VehicleAttachmentDefinitionIndex.Gun100mmHeavy, 40,
                       VehicleType.Bear),
    AmmunitionCapacity(VehicleAttachmentDefinitionIndex.Gun120mm, 25,
                       VehicleType.Bear),
    FuelTankCapacity(VehicleAttachmentDefinitionIndex.FuelTank, 100,
                     VehicleType.Albatross, VehicleType.Manta, VehicleType.Razorbill, VehicleType.Petrel)
]

for a_type in [VehicleAttachmentDefinitionIndex.MissileIR,
               VehicleAttachmentDefinitionIndex.MissileAA,
               VehicleAttachmentDefinitionIndex.MissileLaser,
               VehicleAttachmentDefinitionIndex.Bomb0,
               VehicleAttachmentDefinitionIndex.Bomb1,
               VehicleAttachmentDefinitionIndex.Bomb2,
               VehicleAttachmentDefinitionIndex.MissileTV,
               VehicleAttachmentDefinitionIndex.AirObsCam,
               ]:
    ATTACHMENT_CAPACITY.append(
        AmmunitionCapacity(a_type, 1,
                           VehicleType.Manta, VehicleType.Petrel, VehicleType.Razorbill, VehicleType.Albatross))


def get_attachment_capacity(
        vehicle: Union[VehicleType, int],
        attachment: Union[VehicleAttachmentDefinitionIndex, int]) -> Optional[Capacity]:
    if isinstance(vehicle, int):
        vehicle = VehicleType.lookup(vehicle)
    if isinstance(attachment, int):
        attachment = VehicleAttachmentDefinitionIndex.lookup(attachment)

    for item in ATTACHMENT_CAPACITY:
        if item.attachment == attachment:
            if vehicle in item.vtypes:
                return item
    return None


def get_fuel_capacity(v_type: VehicleType) -> Optional[InternalFuelCapacity]:
    for item in VEHICLE_CAPACITY:
        if v_type in item.vtypes:
            return item
    return None
