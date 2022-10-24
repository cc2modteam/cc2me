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

