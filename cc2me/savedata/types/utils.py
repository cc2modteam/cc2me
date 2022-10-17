from abc import ABC, abstractmethod
from typing import Optional, Any, List, cast, Callable
from xml.etree.ElementTree import Element

MAX_INTEGER = 4294967295


class ElementAttributeProxy(ABC):

    type_default: Optional[Any] = None

    def __init__(self,
                 name: str,
                 parent: Optional["ElementProxy"] = None,
                 default_value: Optional[Any] = None):
        assert name
        self.parent = parent
        self.name = name
        self.base_default_value = default_value

    @property
    def default_value(self) -> Any:
        if self.base_default_value is not None:
            return self.base_default_value
        return self.type_default

    def get(self) -> Any:
        if self.parent is None:
            return self.default_value
        return self.parent.get(self.name, default_value=str(self.default_value))

    @abstractmethod
    def set(self, value: Any):
        pass


class e_property(property):
    def __init__(self, attribute: ElementAttributeProxy):
        self.attribute = attribute
        super(e_property, self).__init__(
            self.do_get,
            self.do_set,
            None,
            f"get/set {attribute.name}")

    # x = property(getx, setx, delx, "I'm the 'x' property.")
    def do_get(self, owner: "ElementProxy"):
        if owner is not None:
            self.attribute.parent = owner
        return self.attribute.get()

    def do_set(self, owner, value):
        if owner is not None:
            self.attribute.parent = owner
        self.attribute.set(value)


class BoolAttribute(ElementAttributeProxy):

    type_default = False

    def get(self) -> Any:
        value = super(BoolAttribute, self).get()
        return value == "true"

    def set(self, value: Any):
        value = str(value).lower()
        if value == "true":
            self.parent.set(self.name, "true")
        else:
            self.parent.set(self.name, "false")


class IntAttribute(ElementAttributeProxy):

    type_default = 0

    def get(self) -> Any:
        return int(super(IntAttribute, self).get())

    def set(self, value: Any):
        self.parent.set(self.name, str(int(value)))


class FloatAttribute(ElementAttributeProxy):

    type_default = 0.0

    def set(self, value: Any):
        self.parent.set(self.name, str(float(value)))

    def get(self) -> Any:
        return float(super(FloatAttribute, self).get())


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
    x = e_property(FloatAttribute("x"))
    y = e_property(FloatAttribute("y"))
    z = e_property(FloatAttribute("z"))


class Min(Point3D):
    tag = "min"

    def defaults(self):
        self.x = -2000
        self.y = -1000
        self.z = -2000


class Max(Point3D):
    tag = "max"

    def defaults(self):
        self.x = 2000
        self.y = 1000
        self.z = 2000


class WorldPosition(Point3D):
    tag = "world_position"


class Bounds(ElementProxy):
    tag = "bounds"

    def defaults(self):
        assert self.max
        assert self.min

    @property
    def min(self) -> Min:
        return cast(Min, self.get_default_child_by_tag(Min))

    @property
    def max(self):
        return cast(Max, self.get_default_child_by_tag(Max))


class IsSetMixin:
    is_set = e_property(BoolAttribute("is_set", default_value=False))
