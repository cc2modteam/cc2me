from typing import Optional
from xml.etree.ElementTree import XMLParser, Element

import xmlschema
import os
import re
from xml.etree import ElementTree
from io import StringIO
from ..paths import SCHEMA
from .logging import logger

XML_START = '<?xml version="1.0" encoding="UTF-8"?>'


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


def load_save_file(filename: str) -> dict:
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
        buf.write(re.sub(r"[\r\n]", "", full_content))
    buf.seek(0, os.SEEK_SET)

    for root in xs.root_elements:
        pre_feed = None
        if buf.tell() != 0:
            pre_feed = XML_START

        element = CC2ElementTree(buf, root.name, pre_feed=pre_feed).cc2parse(buf.tell())
        tree = ElementTree.ElementTree(element=element)
        resp[root.name] = tree

    return resp


