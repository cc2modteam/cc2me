from typing import Optional, List
from xml.etree.ElementTree import XMLParser, Element
import random
import xmlschema
import os
import re
from xml.etree import ElementTree
from io import StringIO

from .types.teams import Team
from .types.tiles import Tile
from .types.vehicles.vehicle import Vehicle
from .types.vehicles.vehicle_state import VehicleStateContainer
from ..paths import SCHEMA
from .logging import logger
from .constants import POS_Y_SEABOTTOM, BIOME_SANDY_PINES

XML_START = '<?xml version="1.0" encoding="UTF-8"?>'
META_ROOT = "meta"
SCENE_ROOT = "scene"
VEHICLES_ROOT = "vehicles"
VEHICLE_STATES_ROOT = "vehicle_states"
MISSILES_ROOT = "missiles"
ROOT_ORDER = [META_ROOT, SCENE_ROOT, VEHICLES_ROOT, VEHICLE_STATES_ROOT, MISSILES_ROOT]

CARRIER_VEH_DEF_INDEX = "0"


class JunkRoot(Exception):
    def __init__(self, position: int, previous=None):
        self.pos = position
        self.prev = previous


class StoppableStringIO(StringIO):
    """control read() calls and only read 1 byte at a time"""
    def __init__(self):
        super(StoppableStringIO, self).__init__()
        self.stop_reads = False
        self.size = len(self.getvalue())

    def __repr__(self):
        return self.getvalue()[self.tell():-64]

    def read(self, size: Optional[int] = ...) -> str:
        if self.stop_reads:
            return ""
        # log reading
        pos = self.tell()
        if pos % 512 == 0:
            logger.info(f"reading {pos}/{self.size} ..")

        return super(StoppableStringIO, self).read(size)


class CC2XMLParser(ElementTree.XMLParser):
    def __init__(self, rootype):
        self._target = None
        super(CC2XMLParser, self).__init__()
        self.want_root = rootype

    def feed(self, *args) -> Optional[Element]:
        try:
            super(CC2XMLParser, self).feed(*args)
        except ElementTree.ParseError as err:
            if "junk after document element" in err.msg:
                # a new root element, close the document to see what we got
                # self.parser.Parse("", 1)
                found = self.target.close()
                if found is not None:
                    self._target = ElementTree.TreeBuilder()
                    raise JunkRoot(err.position[1], found)
            raise
        return None


class CC2ElementTree(ElementTree.ElementTree):

    def __init__(self, source: StoppableStringIO, want: str, pre_feed: Optional[str] = None):
        self._root = None
        super(CC2ElementTree, self).__init__()
        self.data_source = source
        self.want_root = want
        self.pre_feed = pre_feed

    def cc2parse(self, last_offset: Optional[int] = 0) -> Element:
        parser = CC2XMLParser(self.want_root)
        feedlen = 0
        if self.pre_feed:
            parser.feed(self.pre_feed)
            feedlen = len(self.pre_feed)
        while True:
            data = self.data_source.read(65536)
            if not data:
                break
            try:
                element = parser.feed(data)
                if element is not None:
                    self._root = element
                    break
            except JunkRoot as xroot:
                # found a new root, try again with a new parser
                self.data_source.seek(xroot.pos - feedlen + last_offset, os.SEEK_SET)
                self._root = xroot.prev
                break

        return self.getroot()


class CC2XMLSave:
    def __init__(self):
        self.roots = {}

    @property
    def _tiles(self) -> List[Element]:
        return self.roots[SCENE_ROOT].getroot().findall("./tiles/tiles/t")

    @property
    def tiles(self) -> List[Tile]:
        return [Tile(element=x, cc2obj=self) for x in self._tiles]

    def tile(self, tile_id: int) -> Tile:
        """Get a tile by ID"""
        for item in self.tiles:
            if item.id == tile_id:
                return item

        raise KeyError(tile_id)

    def find_vehicles_by_definition(self, definition_id: int):
        return [
            x for x in self.vehicles if x.definition_index == definition_id
        ]

    def vehicle(self, vid: int):
        for x in self.vehicles:
            if x.id == vid:
                return x
        raise KeyError(vid)

    @property
    def tiles_parent(self) -> Element:
        return self.roots[SCENE_ROOT].getroot().findall("./tiles")[0]

    @property
    def tiles_container(self) -> Element:
        return self.roots[SCENE_ROOT].getroot().findall("./tiles/tiles")[0]

    def new_tile(self) -> Tile:
        """Create a new tile"""
        tile = Tile(element=None, cc2obj=self)
        tile.cc2obj = self
        tile.biome_type = BIOME_SANDY_PINES
        tile.id = self.next_tile_attrib_integer("id")
        tile.index = self.next_tile_attrib_integer("index")
        self.tiles_parent.attrib.update(id_counter=str(tile.id))
        self.tiles_container.append(tile.element)
        tile.set_position(x=0, z=0, y=POS_Y_SEABOTTOM)
        return tile

    def remove_tile(self, tile: Tile):
        """Delete a tile"""
        # find the tile element, remove it, then re-compute the id and index values
        self.tiles_container.remove(tile.element)
        index_value = 0
        for tile in self.tiles:
            tile.id = index_value + 1
            tile.index = index_value
            index_value += 1
        self.tiles_parent.attrib.update(id_counter=str(index_value))

    @property
    def _teams(self) -> List[Element]:
        return self.roots[SCENE_ROOT].getroot().findall("./teams/teams/t")

    @property
    def teams(self) -> List[Team]:
        return [Team(x) for x in self._teams]

    def team(self, teamid: int) -> Team:
        """Get a team by ID"""
        for x in self.teams:
            if x.id == teamid:
                return x
        raise KeyError(teamid)

    @property
    def _vehicles(self) -> List[Element]:
        return self.roots[VEHICLES_ROOT].getroot().findall(f"./{VEHICLES_ROOT}/v")

    @property
    def vehicles(self) -> List[Vehicle]:
        return [Vehicle(element=x, cc2obj=self) for x in self._vehicles]

    def vehicle_state(self, vid) -> Optional[VehicleStateContainer]:
        for item in self.vehicle_states:
            if item.id == vid:
                return item
        return None

    @property
    def _vehicle_states(self) -> List[Element]:
        return self.roots[VEHICLE_STATES_ROOT].getroot().findall(f"./{VEHICLE_STATES_ROOT}/v")

    @property
    def vehicle_states(self) -> List[VehicleStateContainer]:
        return [VehicleStateContainer(element=x) for x in self._vehicle_states]

    def next_tile_attrib_integer(self, name: str) -> str:
        last_index = 0
        for item in self._tiles:
            value = int(item.attrib.get(name, "0"))
            last_index = max(value, last_index)
        return str(last_index + 1)

    def export(self) -> str:

        while len(self.tiles) > 63:
            self.remove_tile(self.tiles[-1])

        buf = StringIO()
        buf.write(XML_START)
        for root in ROOT_ORDER:
            buf.write("\n")
            subdoc = self.roots[root]
            if subdoc.getroot() is not None:
                subdoc.write(buf, encoding="unicode")
            else:
                # empty, probably missiles
                buf.write(f"<{root}></{root}>\n")

        return buf.getvalue()


def load_save_file(filename: str) -> CC2XMLSave:
    """
    Load each of the roots from the save file and return them as distinct documents
    :param filename:
    :return:
    """
    resp = {}
    xs = xmlschema.XMLSchema(SCHEMA)
    buf = StoppableStringIO()
    logger.info(f"open {filename}")
    with open(filename, "r") as original:
        # read as one big string so we can use the offset
        full_content = original.read()
        buf.write(re.sub(r"[\r\n]", " ", full_content))
    buf.seek(0, os.SEEK_SET)

    for root in xs.root_elements:
        logger.info(f"parsing {root.name}")
        pre_feed = None
        if buf.tell() != 0:
            pre_feed = XML_START

        element = CC2ElementTree(buf, root.name, pre_feed=pre_feed).cc2parse(buf.tell())
        tree = ElementTree.ElementTree(element=element)
        resp[root.name] = tree
    logger.info("loaded")
    doc = CC2XMLSave()
    doc.roots = resp
    return doc


