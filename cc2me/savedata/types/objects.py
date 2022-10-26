from typing import Tuple, cast, Optional

from .tiles import Tile
from .utils import ElementProxy, LocationMixin, MovableLocationMixin
from .vehicles.vehicle import Vehicle

LOC_SCALE_FACTOR = 1000


class CC2MapItem:
    def __init__(self, obj: ElementProxy):
        self.object = obj

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


class Unit(CC2MapItem):
    def __init__(self, unit: Vehicle):
        super(Unit, self).__init__(unit)

    def vehicle(self) -> Vehicle:
        return cast(Vehicle, self.object)

    def altitude(self, alt: float):
        if isinstance(self.object, MovableLocationMixin):
            temp = cast(MovableLocationMixin, self.object)
            temp.move(temp.loc.z,
                      alt,
                      temp.loc.x)


class Carrier(Unit):
    def __init__(self, carrier: Vehicle):
        super(Carrier, self).__init__(carrier)

    def carrier(self) -> Vehicle:
        return self.vehicle()
