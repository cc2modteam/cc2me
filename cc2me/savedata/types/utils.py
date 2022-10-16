from abc import ABC
from typing import Optional, Any, List, cast
from xml.etree.ElementTree import Element


class ElementProxy(ABC):
    tag: str = "X"

    def __init__(self, element: Optional[Element] = None):
        apply_defaults = False
        if element is None:
            element = Element(self.tag)
            apply_defaults = True
        self.element = element
        if apply_defaults:
            self.defaults()

    def defaults(self):
        pass

    def set(self, attrib: str, value: Any):
        self.element.attrib[attrib] = str(value)

    def get(self, attrib: str, default_value: Optional[Any] = None):
        return self.element.attrib.get(attrib, default_value)

    def __getitem__(self, item):
        return self.get(item)

    def __setitem__(self, key, value):
        self.set(key, str(value))

    def children(self) -> List[Element]:
        return [x for x in self.element]

    def get_default_child_by_tag(self, proxy: callable) -> Element:
        for item in self.children():
            if item.tag == proxy.tag:
                return proxy(item)
        # no min!
        added = proxy()
        self.element.append(added.element)
        return added


class Point3D(ElementProxy):

    def defaults(self):
        self.x = 0
        self.y = 0
        self.z = 0

    @property
    def x(self) -> float:
        return float(self.get("x", 0))

    @x.setter
    def x(self, value: float):
        self.set("x", value)

    @property
    def y(self) -> float:
        return float(self.get("y", 0))

    @y.setter
    def y(self, value: float):
        self.set("y", value)

    @property
    def z(self) -> float:
        return float(self.get("z", 0))

    @z.setter
    def z(self, value: float):
        self.set("z", value)


class Min(Point3D):
    tag = "min"


class Max(Point3D):
    tag = "max"


class WorldPosition(Point3D):
    tag = "world_position"


class Bounds(ElementProxy):
    tag = "bounds"

    @property
    def min(self) -> Min:
        return cast(Min, self.get_default_child_by_tag(Min))

    @property
    def max(self):
        return cast(Max, self.get_default_child_by_tag(Max))
