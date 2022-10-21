from typing import Tuple, cast, Optional

from .tiles import Tile
from .utils import ElementProxy, LocationMixin
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
            return temp.loc.x / LOC_SCALE_FACTOR, temp.loc.z / LOC_SCALE_FACTOR
        return None


class Island(CC2MapItem):
    def __init__(self, tile: Tile):
        super(Island, self).__init__(tile)

    def tile(self) -> Tile:
        return cast(Tile, self.object)


class Carrier(CC2MapItem):
    def __init__(self, carrier: Vehicle):
        super(Carrier, self).__init__(carrier)

    def carrier(self) -> Vehicle:
        return cast(Vehicle, self.object)
