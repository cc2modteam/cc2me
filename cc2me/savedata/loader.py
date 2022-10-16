from typing import Optional, List
from xml.etree.ElementTree import XMLParser, Element
import random
import xmlschema
import os
import re
from xml.etree import ElementTree
from io import StringIO

from .types.tiles import Tile
from ..paths import SCHEMA
from .logging import logger

XML_START = '<?xml version="1.0" encoding="UTF-8"?>'
META_ROOT = "meta"
SCENE_ROOT = "scene"
VEHICLES_ROOT = "vehicles"
MISSILES_ROOT = "missiles"
ROOT_ORDER = [META_ROOT, SCENE_ROOT, VEHICLES_ROOT, MISSILES_ROOT]

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
    def tiles(self) -> List[Element]:
        return self.roots[SCENE_ROOT].getroot().findall("./tiles/tiles/t")

    def tile(self, tile_id: int) -> Tile:
        """Get a tile by ID"""
        for item in self.tiles:
            t = Tile(item)
            if t.id == tile_id:
                return t
        raise KeyError(tile_id)

    def new_tile(self) -> Tile:
        """Create a new tile"""
        tiles_parent = self.roots[SCENE_ROOT].getroot().findall("./tiles")[0]
        tile_container = self.roots[SCENE_ROOT].getroot().findall("./tiles/tiles")[0]
        tile = Tile(None)
        tile.biome_type = 3
        tile.id = self.next_tile_attrib_integer("id")
        tile.index = self.next_tile_attrib_integer("index")
        tile.seed = random.randint(1, 8192)
        tiles_parent.attrib.update(id_counter=str(tile.id))
        tile_container.append(tile.element)
        tile.bounds.max.x = 2000
        tile.bounds.max.y = 1000
        tile.bounds.max.z = 2000
        tile.bounds.min.x = -2000
        tile.bounds.min.y = -1000
        tile.bounds.min.z = -2000
        tile.set_position(x=0, z=0, y=-1)

        return tile

    @property
    def teams(self) -> List[Element]:
        return self.roots[SCENE_ROOT].getroot().findall("./teams/teams/t")

    @property
    def vehicles(self) -> List[Element]:
        return self.roots[VEHICLES_ROOT].getroot().findall(f"./{VEHICLES_ROOT}/v")

    def next_tile_attrib_integer(self, name: str) -> str:
        last_index = 0
        for item in self.tiles:
            value = int(item.attrib.get(name, "0"))
            last_index = max(value, last_index)
        return str(last_index + 1)

    def export(self) -> str:
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
    with open(filename, "r") as original:
        # read as one big string so we can use the offset
        full_content = original.read()
        buf.write(re.sub(r"[\r\n]", " ", full_content))
    buf.seek(0, os.SEEK_SET)

    for root in xs.root_elements:
        pre_feed = None
        if buf.tell() != 0:
            pre_feed = XML_START

        element = CC2ElementTree(buf, root.name, pre_feed=pre_feed).cc2parse(buf.tell())
        tree = ElementTree.ElementTree(element=element)
        resp[root.name] = tree

    doc = CC2XMLSave()
    doc.roots = resp
    return doc


