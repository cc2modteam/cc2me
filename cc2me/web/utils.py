from typing import Tuple, List
from dataclasses import dataclass
from ..savedata.types.utils import Location

SCALE_MAP_COORDS = 10000


@dataclass
class GPoint:
    lon: float
    lat: float

    def move(self, dx: float = 0, dy: float = 0) -> "GPoint":
        self.lon += dx
        self.lat += dy
        return self

    def as_list(self):
        return [self.lon, self.lat]


def loc_to_geo(loc: Location) -> GPoint:
    return GPoint(loc.x / SCALE_MAP_COORDS, loc.z / SCALE_MAP_COORDS)


def loc_to_geo_box(loc: Location, w: float, h: float) -> List:
    height = h / SCALE_MAP_COORDS
    width = w / SCALE_MAP_COORDS
    return [
        loc_to_geo(loc).move(dx=width / -2, dy=height / -2).as_list(),
        loc_to_geo(loc).move(dx=width / 2, dy=height / -2).as_list(),
        loc_to_geo(loc).move(dx=width / 2, dy=height / 2).as_list(),
        loc_to_geo(loc).move(dx=width / -2, dy=height / 2).as_list(),
        loc_to_geo(loc).move(dx=width / -2, dy=height / -2).as_list(),
    ]
