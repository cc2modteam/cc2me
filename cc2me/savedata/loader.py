import os
import re
from xml.etree import ElementTree

from .constants import ROOT_ORDER, XML_START
from .types.save import CC2ElementTree, CC2XMLSave, StoppableStringIO
from .logging import logger


def load_save_file(filename: str) -> CC2XMLSave:
    """
    Load each of the roots from the save file and return them as distinct documents
    :param filename:
    :return:
    """
    resp = {}
    buf = StoppableStringIO()
    logger.info(f"open {filename}")
    with open(filename, "r") as original:
        # read as one big string so that we can use the offset
        full_content = original.read()
        buf.write(re.sub(r"[\r\n]", " ", full_content))
    buf.seek(0, os.SEEK_SET)
    for root in ROOT_ORDER:
        logger.info(f"parsing {root}")
        pre_feed = None
        if buf.tell() != 0:
            pre_feed = XML_START

        element = CC2ElementTree(buf, root, pre_feed=pre_feed).cc2parse(buf.tell())
        tree = ElementTree.ElementTree(element=element)
        resp[root] = tree
    logger.info("loaded")
    doc = CC2XMLSave()
    doc.roots = resp
    return doc


