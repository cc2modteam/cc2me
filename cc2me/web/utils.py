from typing import Tuple, List, Dict, Any, Union
from dataclasses import dataclass
from ..savedata.types.utils import Location, Point3D

SCALE_MAP_COORDS = 10000


def cc2_to_minutes(num: float) -> float:
    return num / SCALE_MAP_COORDS


def latlong_to_cc2loc(lat: float, lon: float) -> Location:
    loc = Location()
    loc.x = lon * SCALE_MAP_COORDS
    loc.z = lat * SCALE_MAP_COORDS
    return loc


@dataclass
class GPoint:

    lng: float
    lat: float

    def move(self, dx: float = 0, dy: float = 0) -> "GPoint":
        self.lng += dx
        self.lat += dy
        return self

    def as_list(self):
        return [self.lat, self.lng]


def loc_to_geo(loc: Union[Location, Point3D]) -> GPoint:
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


def make_geodata(**kwargs) -> Dict[str, Any]:
    res = {
        "type": "Feature",
        "properties": {},
    }
    for name, value in kwargs.items():
        res[name] = value
    return res
