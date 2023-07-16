import os
import random
from abc import ABC
from enum import Enum
from typing import cast, List, Optional, Union, Dict
from xml.etree import ElementTree
from xml.etree.ElementTree import Element

MAX_INTEGER = 4294967295

MIN_TILE_SEED = 2000
MAX_TILE_SEED = 30000

POS_Y_SEABOTTOM = -1

BIOME_GREEN_PINES = 0
BIOME_SNOW_PINES = 1
BIOME_SANDY_PINES = 3
BIOME_DARK_MESAS = 7

BIOMES = [BIOME_DARK_MESAS, BIOME_GREEN_PINES, BIOME_SNOW_PINES, BIOME_SANDY_PINES]

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


class SpawnType(IntEnum):
    Ground = 0
    Airfield = 1
    NeedlefishNavalPatrol = 2
    SwordfishNavalPatrol = 3


class SpawnAttachmentType(IntEnum):
    Seat = 0
    Turret = 1
    AirCam = 2
    Hardpoint = 3


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
    ShipCruiseMissile = 28
    ShipCounterMeasure = 76
    ShipFlare = 29
    ShipCIWS = 26
    ShipCam = 30
    DriverSeat = 38
    Flares = 43
    FuelTank = 42
    GimbalGun = 101
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
    Autocannon = 99


class InventoryIndex(IntEnum):
    Ammo30mm = 0
    Seal = 1
    Walrus = 2
    Bear = 3
    Albatross = 4
    Manta = 5
    Razorbill = 6
    Petrel = 7
    Reserved1 = 8
    Turret30mm = 9
    AircraftChaingun = 10
    RocketPod = 11
    TurretCIWS = 12
    TurretIRMissile = 13
    BombLight = 14
    BombMedium = 15
    BombHeavy = 16
    MissilesIR = 17
    MissilesLaser = 18
    MissilesAir = 19
    ActuatedCamera = 20
    Reserved2 = 21
    GimbalCamera = 22
    ObservationCamera = 23
    AWACS = 24
    FuelTankAircraft = 25
    FlareLauncher = 26
    BattleCannon = 27
    ArtilleryGun = 28
    CruiseMissile= 29
    Rocket = 30
    Flares = 31
    Ammo20mm = 32
    Ammo100mm = 33
    Ammo120mm = 34
    Ammo160mm = 35
    Fuel = 36
    Torpedo = 37
    TVMissile = 38
    TorpedoNoise = 39
    TorpedoCountermeasure = 40
    Radar = 41
    SonicPulseGenerator = 42
    SmokeLauncherStream = 43
    SmokeLauncherExplosive = 44
    AmmoSonicPulse = 45
    AmmoSmoke = 46
    Turret40mm = 47
    Ammo40mm = 48
    HeavyCannon = 49
    VirusModules = 50
    Reserved3 = 51
    Reserved4 = 52
    Reserved5 = 53
    Reserved6 = 54
    Reserved7 = 55
    Reserved8 = 56
    Reserved9 = 57
    Reserved10 = 58
    Mule = 59
    DeployableDroid = 60


class WaypointTypes(IntEnum):
    Move = 0


HARDPOINT_ATTACHMENTS = [
    VehicleAttachmentDefinitionIndex.Bomb0,
    VehicleAttachmentDefinitionIndex.Bomb1,
    VehicleAttachmentDefinitionIndex.Bomb2,
    VehicleAttachmentDefinitionIndex.RocketPod,
    VehicleAttachmentDefinitionIndex.MissileAA,
    VehicleAttachmentDefinitionIndex.MissileIR,
    VehicleAttachmentDefinitionIndex.MissileTV,
    VehicleAttachmentDefinitionIndex.Gun20mm,
    VehicleAttachmentDefinitionIndex.Torpedo,
    VehicleAttachmentDefinitionIndex.Noisemaker,
    VehicleAttachmentDefinitionIndex.TorpedoCountermesure,
]

TURRET_ATTACHMENTS = [
    VehicleAttachmentDefinitionIndex.Gun100mm,
    VehicleAttachmentDefinitionIndex.Gun100mmHeavy,
    VehicleAttachmentDefinitionIndex.Gun120mm,
    VehicleAttachmentDefinitionIndex.Gun15mm,
    VehicleAttachmentDefinitionIndex.Gun30mm,
    VehicleAttachmentDefinitionIndex.Gun40mm,
    VehicleAttachmentDefinitionIndex.CIWS,
    VehicleAttachmentDefinitionIndex.MissileIRLauncher,
    VehicleAttachmentDefinitionIndex.VirusBot,
]


def get_spawn_attachment_type(definition: VehicleAttachmentDefinitionIndex) -> SpawnAttachmentType:
    if definition == VehicleAttachmentDefinitionIndex.DriverSeat:
        return SpawnAttachmentType.Seat

    if definition in HARDPOINT_ATTACHMENTS:
        return SpawnAttachmentType.Hardpoint

    return SpawnAttachmentType.Turret


class TileTypes(IntEnum):
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


class Hitpoints(Capacity):
    attribs = ["hitpoints"]

    def __init__(self, count: int, *vtype: VehicleType):
        super(Hitpoints, self).__init__(VehicleAttachmentDefinitionIndex.DriverSeat, count, *vtype)


VEHICLE_DEFAULT_STATE = [
    InternalFuelCapacity(2000, VehicleType.Petrel, VehicleType.Manta, VehicleType.Albatross),
    InternalFuelCapacity(1200, VehicleType.Walrus, VehicleType.Bear, VehicleType.Mule),
    InternalFuelCapacity(800, VehicleType.Seal),
    InternalFuelCapacity(400, VehicleType.Razorbill),
    InternalFuelCapacity(1000, VehicleType.Swordfish),
    InternalFuelCapacity(800, VehicleType.Needlefish),
    InternalFuelCapacity(2000, VehicleType.Barge),
    Hitpoints(40, VehicleType.Razorbill, VehicleType.Albatross),
    Hitpoints(300, VehicleType.Needlefish),
    Hitpoints(600, VehicleType.Swordfish),
    Hitpoints(80, VehicleType.Manta),
    Hitpoints(160, VehicleType.Petrel),
    Hitpoints(4000, VehicleType.Barge),
    Hitpoints(5000, VehicleType.Carrier),
    Hitpoints(400, VehicleType.Seal, VehicleType.Bear, VehicleType.Walrus, VehicleType.Mule),
    Hitpoints(1000000, VehicleType.Jetty),
    Hitpoints(800, VehicleType.Turret),
]


ATTACHMENT_CAPACITY = [
    AmmunitionCapacity(VehicleAttachmentDefinitionIndex.ShipTorpedo, 4,
                       VehicleType.Needlefish, VehicleType.Swordfish),
    AmmunitionCapacity(VehicleAttachmentDefinitionIndex.ShipCIWS, 100,
                       VehicleType.Needlefish, VehicleType.Swordfish),
    AmmunitionCapacity(VehicleAttachmentDefinitionIndex.ShipCruiseMissile, 10,
                       VehicleType.Needlefish, VehicleType.Swordfish),
    AmmunitionCapacity(VehicleAttachmentDefinitionIndex.AWACS, 1,
                       VehicleType.Manta),
    AmmunitionCapacity(VehicleAttachmentDefinitionIndex.Gun20mm, 400,
                       VehicleType.Manta, VehicleType.Albatross, VehicleType.Razorbill, VehicleType.Petrel),
    AmmunitionCapacity(VehicleAttachmentDefinitionIndex.Gun30mm, 500,
                       VehicleType.Seal, VehicleType.Walrus),
    AmmunitionCapacity(VehicleAttachmentDefinitionIndex.CIWS, 200,
                       VehicleType.Seal, VehicleType.Walrus, VehicleType.Bear),
    AmmunitionCapacity(VehicleAttachmentDefinitionIndex.Gun40mm, 400,
                       VehicleType.Seal, VehicleType.Walrus, VehicleType.Bear, VehicleType.Petrel),
    AmmunitionCapacity(VehicleAttachmentDefinitionIndex.MissileIRLauncher, 4,
                       VehicleType.Seal, VehicleType.Walrus),
    AmmunitionCapacity(VehicleAttachmentDefinitionIndex.Gun100mm, 40,
                       VehicleType.Bear, VehicleType.Petrel),
    AmmunitionCapacity(VehicleAttachmentDefinitionIndex.Gun100mmHeavy, 40,
                       VehicleType.Bear),
    AmmunitionCapacity(VehicleAttachmentDefinitionIndex.Gun120mm, 25,
                       VehicleType.Bear),
    AmmunitionCapacity(VehicleAttachmentDefinitionIndex.MissileAALauncher, 8,
                       VehicleType.Swordfish, VehicleType.Needlefish, VehicleType.Turret),
    AmmunitionCapacity(VehicleAttachmentDefinitionIndex.Flares, 16,
                       VehicleType.Bear, VehicleType.Walrus, VehicleType.Seal, VehicleType.Razorbill, VehicleType.Manta),
    AmmunitionCapacity(VehicleAttachmentDefinitionIndex.SmokeBomb, 10,
                       VehicleType.Bear, VehicleType.Walrus, VehicleType.Seal, VehicleType.Razorbill,
                       VehicleType.Manta),
    AmmunitionCapacity(VehicleAttachmentDefinitionIndex.SmokeTrail, 10,
                       VehicleType.Bear, VehicleType.Walrus, VehicleType.Seal, VehicleType.Razorbill,
                       VehicleType.Manta),
    AmmunitionCapacity(VehicleAttachmentDefinitionIndex.SmokeBomb, 10,
                       VehicleType.Bear, VehicleType.Walrus, VehicleType.Seal),
    AmmunitionCapacity(VehicleAttachmentDefinitionIndex.Flares, 60,
                       VehicleType.Swordfish, VehicleType.Needlefish),
    FuelTankCapacity(VehicleAttachmentDefinitionIndex.FuelTank, 100,
                     VehicleType.Albatross, VehicleType.Manta, VehicleType.Razorbill, VehicleType.Petrel),

    # silly warship weapons
    AmmunitionCapacity(VehicleAttachmentDefinitionIndex.MissileLaser, 30,
                       VehicleType.Swordfish, VehicleType.Needlefish),

    AmmunitionCapacity(VehicleAttachmentDefinitionIndex.ShipCounterMeasure, 3,
                       VehicleType.Carrier, VehicleType.Swordfish, VehicleType.Needlefish),
    AmmunitionCapacity(VehicleAttachmentDefinitionIndex.ShipFlare, 10,
                       VehicleType.Carrier, VehicleType.Swordfish, VehicleType.Needlefish),
    AmmunitionCapacity(VehicleAttachmentDefinitionIndex.ShipCruiseMissile, 10,
                       VehicleType.Carrier, VehicleType.Swordfish, VehicleType.Needlefish),
    AmmunitionCapacity(VehicleAttachmentDefinitionIndex.MissileIRLauncher, 10,
                       VehicleType.Carrier, VehicleType.Swordfish, VehicleType.Needlefish),
    AmmunitionCapacity(VehicleAttachmentDefinitionIndex.Gun30mm, 800,
                       VehicleType.Carrier, VehicleType.Swordfish, VehicleType.Needlefish),
    AmmunitionCapacity(VehicleAttachmentDefinitionIndex.Gun40mm, 500,
                       VehicleType.Carrier, VehicleType.Swordfish, VehicleType.Needlefish),
    AmmunitionCapacity(VehicleAttachmentDefinitionIndex.Gun100mm, 55,
                       VehicleType.Carrier, VehicleType.Swordfish, VehicleType.Needlefish),
    AmmunitionCapacity(VehicleAttachmentDefinitionIndex.Gun100mm, 55,
                       VehicleType.Carrier, VehicleType.Swordfish, VehicleType.Needlefish),
    AmmunitionCapacity(VehicleAttachmentDefinitionIndex.Gun100mmHeavy, 55,
                       VehicleType.Carrier, VehicleType.Swordfish, VehicleType.Needlefish),
    AmmunitionCapacity(VehicleAttachmentDefinitionIndex.Flares, 50,
                       VehicleType.Carrier, VehicleType.Swordfish, VehicleType.Needlefish),
    AmmunitionCapacity(VehicleAttachmentDefinitionIndex.SmokeTrail, 50,
                       VehicleType.Carrier, VehicleType.Swordfish, VehicleType.Needlefish),
    AmmunitionCapacity(VehicleAttachmentDefinitionIndex.SmokeBomb, 50,
                       VehicleType.Carrier, VehicleType.Swordfish, VehicleType.Needlefish),
    AmmunitionCapacity(VehicleAttachmentDefinitionIndex.SonicPulse, 8,
                       VehicleType.Carrier, VehicleType.Swordfish, VehicleType.Needlefish),
    AmmunitionCapacity(VehicleAttachmentDefinitionIndex.RocketPod, 60,
                       VehicleType.Carrier, VehicleType.Swordfish, VehicleType.Needlefish),
    AmmunitionCapacity(VehicleAttachmentDefinitionIndex.RocketPod, 20,
                       VehicleType.Manta, VehicleType.Albatross, VehicleType.Petrel, VehicleType.Razorbill),
    AmmunitionCapacity(VehicleAttachmentDefinitionIndex.VirusBot, 1,
                       VehicleType.Seal, VehicleType.Walrus)
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

ATTACHMENT_CAPACITY.extend([
    AmmunitionCapacity(VehicleAttachmentDefinitionIndex.Gun20mm,
                       500, VehicleType.Mule
                       ),
    AmmunitionCapacity(VehicleAttachmentDefinitionIndex.Gun40mm,
                       500, VehicleType.Mule
                       )
    ]
)
ATTACHMENT_CAPACITY.append(
    AmmunitionCapacity(VehicleAttachmentDefinitionIndex.Refuel,
                       160, VehicleType.Mule
                       )
)
ATTACHMENT_CAPACITY.append(
    AmmunitionCapacity(VehicleAttachmentDefinitionIndex.RearmIR,
                       20, VehicleType.Mule
                       )
)
ATTACHMENT_CAPACITY.append(
    AmmunitionCapacity(VehicleAttachmentDefinitionIndex.Rearm20mm,
                       400, VehicleType.Mule
                       )
)
ATTACHMENT_CAPACITY.append(
    AmmunitionCapacity(VehicleAttachmentDefinitionIndex.Rearm40mm,
                       300, VehicleType.Mule
                       )
)
ATTACHMENT_CAPACITY.extend(
    [
        AmmunitionCapacity(VehicleAttachmentDefinitionIndex.BattleDroids,
                           1, VehicleType.Mule, VehicleType.Needlefish, VehicleType.Swordfish,
                           ),
        AmmunitionCapacity(VehicleAttachmentDefinitionIndex.VirusBot,
                           1, VehicleType.Mule, VehicleType.Needlefish, VehicleType.Swordfish,
                           )
     ]
)

# mobile SAM
ATTACHMENT_CAPACITY.append(
    AmmunitionCapacity(VehicleAttachmentDefinitionIndex.MissileAA, 4,
                       VehicleType.Seal, VehicleType.Walrus, VehicleType.Bear, VehicleType.Mule))

# Ship launched VLS SAM
ATTACHMENT_CAPACITY.append(
    AmmunitionCapacity(VehicleAttachmentDefinitionIndex.MissileAA, 8,
                       VehicleType.Needlefish))
ATTACHMENT_CAPACITY.append(
    AmmunitionCapacity(VehicleAttachmentDefinitionIndex.MissileAA, 24,
                       VehicleType.Swordfish))


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

    cap = None
    if attachment in TURRET_ATTACHMENTS + [VehicleAttachmentDefinitionIndex.Gun20mm, VehicleAttachmentDefinitionIndex.GimbalGun]:
        # default 100 rounds
        cap = AmmunitionCapacity(attachment, 100, vehicle)
    elif attachment in HARDPOINT_ATTACHMENTS:
        cap = AmmunitionCapacity(attachment, 1, vehicle)
    if attachment in [VehicleAttachmentDefinitionIndex.FuelTank]:
        cap = FuelTankCapacity(attachment, 100, vehicle)

    if attachment == VehicleAttachmentDefinitionIndex.Autocannon:
        cap = AmmunitionCapacity(attachment, 250, vehicle)

    return cap


def get_default_hitpoints(v_type: VehicleType) -> Optional[float]:
    states = get_default_state(v_type)
    for item in states:
        if isinstance(item, Hitpoints):
            return item.count
    return None


def get_default_state(v_type: VehicleType) -> List[Capacity]:
    values = []
    for item in VEHICLE_DEFAULT_STATE:
        if v_type in item.vtypes:
            values.append(item)
    return values


def get_cc2_appdata() -> str:
    cc2dir = os.path.expandvars(r'%APPDATA%\\Carrier Command 2')
    return cc2dir


def get_persistent_file_path() -> str:
    persistent = os.path.join(get_cc2_appdata(), "persistent_data.xml")
    return persistent


def read_save_slots(slots_file: Optional[str] = None) -> List[Dict[str, str]]:
    if slots_file is None:
        slots_file = get_persistent_file_path()
    slots = []
    with open(slots_file, "r") as xmlfile:
        xml = xmlfile.read()
    etree = ElementTree.fromstring(xml)
    for item in etree:
        if isinstance(item, Element):
            filename = item.attrib.get("save_name")
            text = item.attrib.get("display_name")
            if filename:
                slots.append({
                    "filename": filename,
                    "display": text
                })
    return slots

