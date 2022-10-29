from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Any, List, cast
from xml.etree.ElementTree import Element


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
    def __init__(self, attribute: ElementAttributeProxy, side_effect: Optional[callable] = None):
        super(e_property, self).__init__(
            self.do_get,
            self.do_set,
            None,
            f"get/set {attribute.name}")
        self.attribute = attribute
        self.side_effect: callable = side_effect

    # x = property(getx, setx, delx, "I'm the 'x' property.")
    def do_get(self, owner: "ElementProxy"):
        if owner is not None:
            self.attribute.parent = owner
        return self.attribute.get()

    def do_set(self, owner, value):
        if owner is not None:
            self.attribute.parent = owner
        self.attribute.set(value)
        if self.side_effect is not None:
            self.side_effect(owner)


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


class StrAttribute(ElementAttributeProxy):

    type_default = ""

    def get(self) -> Any:
        return str(super(StrAttribute, self).get())

    def set(self, value: Any):
        self.parent.set(self.name, str(value))


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

    def __init__(self, element: Optional[Element] = None, cc2obj: Optional[Any] = None):
        apply_defaults = False
        if element is None:
            element = Element(self.tag)
            apply_defaults = True
        self.element = element
        if apply_defaults:
            self.defaults()
        self.cc2obj: "CC2Save" = cc2obj

    @property
    def human_controlled(self) -> bool:
        return False

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
        try:
            added = proxy()
            self.element.append(added.element)
            return added
        except TypeError:
            pass


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


@dataclass
class Location:
    x: float = 0
    y: float = 0
    z: float = 0


class LocationMixin(ABC):
    @property
    @abstractmethod
    def loc(self) -> Location:
        pass


class MovableLocationMixin(LocationMixin, ABC):
    @abstractmethod
    def move(self, x: float, y: float, z: float) -> None:
        pass


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

    def __str__(self):
        return f"{self.min.x}, {self.min.y} => {self.max.x}, {self.max.y}"


class IsSetMixin:
    is_set = e_property(BoolAttribute("is_set", default_value=False))


class Transform(ElementProxy):
    """
    Movement and rotation of an object/body
    <transform m00="9.99983729e-01" m01="5.36093389e-03" m02="1.95000893e-03" m10="-5.40422454e-03" m11="9.99722757e-01" m12="2.29173339e-02" m20="-1.82660999e-03" m21="-2.29274993e-02" m22="9.99735462e-01" tx="8.82208525e+03" ty="-2.19774270e+00" tz="5.10294861e+03"/>
    """
    tag = "transform"

    # I have no idea what these do, perhaps it is 3d a rotation matrix?
    m00 = e_property(FloatAttribute("m00"))
    m01 = e_property(FloatAttribute("m01"))
    m02 = e_property(FloatAttribute("m02"))
    m10 = e_property(FloatAttribute("m10"))
    m11 = e_property(FloatAttribute("m11"))
    m12 = e_property(FloatAttribute("m12"))
    m20 = e_property(FloatAttribute("m20"))
    m21 = e_property(FloatAttribute("m21"))
    m22 = e_property(FloatAttribute("m22"))

    # location transform / position
    tx = e_property(FloatAttribute("tx"))
    ty = e_property(FloatAttribute("ty"))
    tz = e_property(FloatAttribute("tz"))


class LinearVelocity(Point3D):
    tag = "linear_velocity"


class AngularVelocity(Point3D):
    tag = "angular_velocity"


class Bodies(ElementProxy):
    tag = "bodies"

    def items(self) -> List["Body"]:
        return [Body(x) for x in self.children()]


class Body(ElementProxy):
    tag = "b"

    @property
    def linear_velocity(self) -> LinearVelocity:
        return cast(LinearVelocity, self.get_default_child_by_tag(LinearVelocity))

    @property
    def angular_velocity(self) -> AngularVelocity:
        return cast(AngularVelocity, self.get_default_child_by_tag(AngularVelocity))

    @property
    def transform(self) -> Transform:
        return cast(Transform, self.get_default_child_by_tag(Transform))

