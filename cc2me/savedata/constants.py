from enum import Enum
from typing import cast, Any

MAX_INTEGER = 4294967295

MIN_TILE_SEED = 10000
MAX_TILE_SEED = 200000

POS_Y_SEABOTTOM = -1

BIOME_GREEN_PINES = 0
BIOME_SNOW_PINES = 1
BIOME_SANDY_PINES = 3
BIOME_DARK_MESAS = 7

VEHICLE_DEF_CARRIER = 0


class IntEnum(Enum):

    @property
    def int(self) -> int:
        return cast(int, self.value)


class VehicleTypes(IntEnum):
    Carrier = 0
    Walrus = 4
    Seal = 2
    Bear = 6
    Albatross = 8
    Manta = 10
    Razorbill = 12
    Petrel = 14
    Barge = 16
    Lifeboat = 57
    Turret = 59
    Jetty = 64
    Needlefish = 77
    Swordfish = 79
    Mule = 88


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


def get_vehicle_name(definition_index: int) -> str:
    for item in VehicleTypes:
        if item.value == definition_index:
            return item.name

    return f"*** ({definition_index}) "
