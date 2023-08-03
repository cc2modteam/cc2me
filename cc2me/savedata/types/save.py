import os
import random
from io import StringIO
from typing import Optional, List, Tuple, cast, Union, Iterable, Any
from xml.etree import ElementTree
from xml.etree.ElementTree import Element

from .attachments import Attachments, Attachment
from .utils import (
    ElementProxy, e_property, IntAttribute, BoolAttribute, Location, MovableLocationMixin,
    FloatAttribute, Bounds, WorldPosition, IsSetMixin, StrAttribute, Transform, Bodies)
from ..constants import (
    BIOME_SANDY_PINES, POS_Y_SEABOTTOM, VehicleType, get_default_state, MAX_INTEGER,
    generate_island_seed, get_spawn_attachment_type, VehicleAttachmentDefinitionIndex,
    XML_START, SCENE_ROOT, VEHICLES_ROOT, ROOT_ORDER, REMOTE_DRIVEABLE_VEHICLES, get_attachment_capacity)
from ..logging import logger


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


class JunkRoot(Exception):
    def __init__(self, position: int, previous=None):
        self.pos = position
        self.prev = previous


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


class VehicleSpawnAttachment(ElementProxy):
    tag = "a"
    ammo = e_property(IntAttribute("ammo"))

    attachment_type = e_property(IntAttribute("attachment_type"))

    @property
    def definition_index(self) -> int:
        return int(self.element.attrib.get("definition_index", "0"))

    @definition_index.setter
    def definition_index(self, value: int):
        self.element.attrib["definition_index"] = str(value)
        att_type = get_spawn_attachment_type(VehicleAttachmentDefinitionIndex.lookup(value))
        self.attachment_type = att_type


class VehicleSpawnAttachments(ElementProxy):
    tag = "attachments"

    def items(self) -> List[VehicleSpawnAttachment]:
        return [VehicleSpawnAttachment(x) for x in self.children()]


class EmbeddedData(ElementProxy):
    tag = "data"

    def to_string(self):
        buf = '<?xml version="1.0" encoding="UTF-8"?>'
        buf += ElementTree.tostring(self.element, short_empty_elements=False, encoding="unicode")
        return buf


class Quantity(ElementProxy):
    tag = "q"
    value = e_property(IntAttribute("value"))


class QuantitiyList(ElementProxy):
    tag = "item_quantities"

    def items(self) -> List[int]:
        return [Quantity(x).value for x in self.children()]


class Inventory(ElementProxy):
    tag = "inventory"
    total_weight = e_property(IntAttribute("total_weight"))

    @property
    def item_quantities(self) -> QuantitiyList:
        return cast(QuantitiyList, self.get_default_child_by_tag(QuantitiyList))


class EmbeddedVehicleStateData(EmbeddedData):
    # see cc2me/tests/canned_saves/manta-state.xml
    # and cc2me/tests/canned_saves/carrier-state.xml
    tag = "data"

    # e.g. glued to another unit, eg, this is a docked unit
    attached_to_vehicle_id = e_property(IntAttribute("attached_to_vehicle_id"))

    internal_fuel_remaining = e_property(FloatAttribute("internal_fuel_remaining"))
    is_destroyed = e_property(BoolAttribute("is_destroyed"))
    hitpoints = e_property(IntAttribute("hitpoints"))

    def defaults(self):
        self.is_destroyed = False
        self.hitpoints = 80
        self.internal_fuel_remaining = 400


class EmbeddedAttachmentStateData(EmbeddedData):
    ammo = e_property(IntAttribute("ammo"))
    fuel_capacity = e_property(FloatAttribute("fuel_capacity"))
    fuel_remaining = e_property(FloatAttribute("fuel_remaining"))


class VehicleAttachmentState(ElementProxy):
    tag = "a"
    attachment_index = e_property(IntAttribute("attachment_index"))
    state = e_property(StrAttribute("state"))

    _cached_data = None

    def defaults(self):
        data = self.data
        self.data = data

    @property
    def data(self) -> EmbeddedAttachmentStateData:
        if self._cached_data is None:
            root = None
            try:
                root = ElementTree.fromstring(self.state)
            except ElementTree.ParseError:
                pass
            self._cached_data = EmbeddedAttachmentStateData(element=root)
        return self._cached_data

    @data.setter
    def data(self, value: EmbeddedAttachmentStateData):
        self._cached_data = value
        self.state = value.to_string()


class VehicleAttachmentStates(ElementProxy):
    tag = "attachments"

    def items(self) -> List[VehicleAttachmentState]:
        return [VehicleAttachmentState(x) for x in self.children()]

    def __getitem__(self, attachment_index) -> Optional[VehicleAttachmentState]:
        for item in self.items():
            if item.attachment_index == attachment_index:
                return item
        return None

    def __delitem__(self, attachment):
        if attachment:
            a_id = str(attachment.attachment_index)
            children = [x for x in self.element]
            for child in children:
                if child.attrib.get("attachment_index", "-1") == a_id:
                    self.element.remove(child)

    def replace(self, attachment: VehicleAttachmentState):
        del self[attachment]
        self.element.append(attachment.element)


class VehicleStateContainer(ElementProxy):
    tag = "v"
    id = e_property(IntAttribute("id", default_value=0))
    state = e_property(StrAttribute("state", default_value=""))

    _cached_state = None
    _cached_waypoints = []

    def defaults(self):
        data = self.data
        self.data = data  # uuuh..

    @property
    def attachments(self) -> VehicleAttachmentStates:
        return cast(VehicleAttachmentStates, self.get_default_child_by_tag(VehicleAttachmentStates))

    @property
    def data(self) -> EmbeddedVehicleStateData:
        return self.get_embdata()

    def get_embdata(self):
        if self._cached_state is None:
            root = None
            try:
                root = ElementTree.fromstring(self.state)
            except ElementTree.ParseError:
                pass
            state = EmbeddedVehicleStateData(element=root)
            self._cached_state = state
        else:
            assert True
        return self._cached_state

    @data.setter
    def data(self, value: EmbeddedVehicleStateData):
        self.set_embdata(value)
        self.state = value.to_string()

    def set_embdata(self, value: EmbeddedVehicleStateData):
        self.state = value

    @property
    def waypoints(self) -> List[Element]:
        ret = []
        for child in self.get_embdata().children():
            if child.tag == "waypoints":
                ret = child.findall("w")
                break
        return ret



class VehicleSpawnData(ElementProxy):
    tag = "data"

    respawn_id = e_property(IntAttribute("respawn_id", default_value=0))
    definition_index = e_property(IntAttribute("definition_index", default_value=0))
    hitpoints = e_property(IntAttribute("hitpoints", default_value=0))
    orientation = e_property(FloatAttribute("orientation", default_value=0))

    @property
    def attachments(self) -> VehicleSpawnAttachments:
        return cast(VehicleSpawnAttachments, self.get_default_child_by_tag(VehicleSpawnAttachments))

    @property
    def world_position(self) -> WorldPosition:
        return cast(WorldPosition, self.get_default_child_by_tag(WorldPosition))


class VehicleSpawn(ElementProxy, MovableLocationMixin):

    def move(self, x: float, y: float, z: float) -> None:
        self.data.world_position.x = x
        self.data.world_position.y = y
        self.data.world_position.z = z

    def translate(self, dx: float, dy: float, dz: float) -> None:
        self.move(self.data.world_position.x + dx,
                  self.data.world_position.y + dy,
                  self.data.world_position.z + dz)

    @property
    def loc(self) -> Location:
        pos = self.data.world_position
        return Location(pos.x, pos.y, pos.z)

    tag = "v"
    spawn_type = e_property(IntAttribute("spawn_type", default_value=0))

    @property
    def data(self) -> VehicleSpawnData:
        return cast(VehicleSpawnData, self.get_default_child_by_tag(VehicleSpawnData))

    @data.setter
    def data(self, value: VehicleSpawnData):
        children = [x for x in self.element]
        for child in children:
            self.element.remove(child)
        self.element.append(value.element)


class VehicleSpawnContainer(ElementProxy):
    tag = "vehicles"

    def items(self) -> Iterable[VehicleSpawn]:
        ret = []
        for element in self.children():
            ret.append(VehicleSpawn(element, self.cc2obj))
        return ret

    def remove(self, child: Union[VehicleSpawn, int]):
        remove_ident = -1
        if isinstance(child, VehicleSpawn):
            remove_ident = child.data.respawn_id
        elif isinstance(child, int):
            remove_ident = child
        children = self.items()
        for item in children:
            item: VehicleSpawn
            if item.data.respawn_id == remove_ident:
                self.element.remove(item.element)

    def append(self, item: VehicleSpawn):
        self.element.append(item.element)


class SpawnData(ElementProxy, IsSetMixin):
    tag = "spawn_data"
    team_id = e_property(IntAttribute("team_id", default_value=0))

    def defaults(self):
        self.is_set = True

    @property
    def vehicles(self) -> VehicleSpawnContainer:
        return cast(VehicleSpawnContainer, self.get_default_child_by_tag(VehicleSpawnContainer))




class Team(ElementProxy):
    id = e_property(IntAttribute("id"))
    pattern_index = e_property(IntAttribute("pattern_index", default_value=5))
    is_ai_controlled = e_property(BoolAttribute("is_ai_controlled", default_value=False))
    is_neutral = e_property(BoolAttribute("is_neutral", default_value=False))
    is_destroyed = e_property(BoolAttribute("is_destroyed", default_value=False))
    currency = e_property(IntAttribute("currency", default_value=1500))
    start_tile_id = e_property(IntAttribute("start_tile_id"))




class Vehicle(ElementProxy, MovableLocationMixin):
    tag = "v"

    _state: Optional[VehicleStateContainer] = None

    @property
    def state(self) -> Optional[VehicleStateContainer]:
        if self._state is None:
            self._state = self.cc2obj.vehicle_state(self.id)
        return self._state

    @state.setter
    def state(self, value: Optional[VehicleStateContainer]):
        self._state = value

    @property
    def human_controlled(self) -> bool:
        if self.cc2obj:
            team: Team = self.cc2obj.team(self.team_id)
            return team.human_controlled
        return False

    @property
    def type(self) -> VehicleType:
        return VehicleType.lookup(self.definition_index)

    @property
    def human_remote_pilot(self) -> bool:
        if self.human_controlled:
            return self.type in REMOTE_DRIVEABLE_VEHICLES
        return False

    def on_set_team_id(self):
        # if we are set to a human team, ensure there is a pilot seat for some unit types
        if self.human_remote_pilot:
            a0 = self.attachments[0]
            if a0 is None:
                pass
                # make a driver seat

    id = e_property(IntAttribute("id"))
    definition_index = e_property(IntAttribute("definition_index"))
    team_id = e_property(IntAttribute("team_id"), side_effect=on_set_team_id)

    @property
    def transform(self) -> Transform:
        return cast(Transform, self.get_default_child_by_tag(Transform))

    @property
    def bodies(self) -> Bodies:
        return cast(Bodies, self.get_default_child_by_tag(Bodies))

    @property
    def attachments(self) -> Attachments:
        return cast(Attachments, self.get_default_child_by_tag(Attachments))

    def set_location(self,
                     x: Optional[float] = None,
                     y: Optional[float] = None,
                     z: Optional[float] = None
                     ):
        """change the location of this vehicle and update all bodies and attachments with the delta"""
        current_position = self.transform
        if x is None:
            x = current_position.tx
        if y is None:
            y = current_position.ty
        if z is None:
            z = current_position.tz

        dx = x - current_position.tx
        dy = y - current_position.ty
        dz = z - current_position.tz

        # update positions
        self.transform.tx += dx
        self.transform.ty += dy
        self.transform.tz += dz

        for att in self.attachments.items():
            if att.bodies:
                for body in att.bodies.items():
                    body.transform.tx += dx
                    body.transform.ty += dy
                    body.transform.tz += dz

        for body in self.bodies.items():
            body.transform.tx += dx
            body.transform.ty += dy
            body.transform.tz += dz

    def move(self, x: float, y: float, z: float) -> None:
        self.set_location(x, y, z)

    def translate(self, dx: float, dy: float, dz: float) -> None:
        self.set_location(self.loc.x + dx,
                          self.loc.y + dy,
                          self.loc.z + dz)

    @property
    def waypoints(self) -> List["Waypoint"]:
        ret = []
        wlist = self.state.waypoints
        for w in wlist:
            ret.append(Waypoint(w, cc2obj=self.cc2obj, vehicle=self))
        return ret

    @property
    def loc(self) -> Location:
        return Location(self.transform.tx, self.transform.ty, self.transform.tz)

    def get_attachment(self, attachment_index: int) -> Optional[VehicleAttachmentDefinitionIndex]:
        item = self.attachments[attachment_index]
        if item is not None:
            item = VehicleAttachmentDefinitionIndex.lookup(item.definition_index)
        return item

    def get_attachment_state(self, attachment_index: int) -> Optional[VehicleAttachmentState]:
        return self.state.attachments[attachment_index]

    def set_attachment(self, attachment_index: int,
                       value: Union[None, str, VehicleAttachmentDefinitionIndex]):
        if value == "None":
            value = None

        if isinstance(value, str):
            try:
                value = VehicleAttachmentDefinitionIndex.reverse_lookup(value)
            except KeyError:
                return

        if value is not None:
            value: VehicleAttachmentDefinitionIndex
            value_idx = value.value
            new_attachment = Attachment()
            new_attachment.attachment_index = attachment_index
            new_attachment.definition_index = value_idx
            self.attachments.replace(new_attachment)

            new_attachment_state = VehicleAttachmentState(element=None, cc2obj=self.cc2obj)
            new_attachment_state.attachment_index = attachment_index

            capacity = get_attachment_capacity(self.definition_index, value)
            if capacity is not None:
                data = new_attachment_state.data
                for attrib_name in capacity.attribs:
                    setattr(data, attrib_name, capacity.count)

                new_attachment_state.data = data
                self.state.attachments.replace(new_attachment_state)
        else:
            del self.attachments[attachment_index]
            del self.state.attachments[attachment_index]


class Waypoint(ElementProxy, MovableLocationMixin):

    def __init__(self, element: Optional[Element] = None, cc2obj: Optional[Any] = None, vehicle: Optional[Vehicle] = None):
        super().__init__(element, cc2obj)
        self.vehicle = vehicle

    def set_location(self,
                     x: Optional[float] = None,  # y in xml
                     y: Optional[float] = None,  # alt in xml
                     z: Optional[float] = None   # x in xml
                     ):
        if y is not None:
            self.element.set("altitude", str(y))
        position = self.element.find("position")
        if position is not None:
            if x is not None:
                position.set("y", str(x))
            if z is not None:
                position.set("x", str(z))

    def move(self, x: float, y: float, z: float) -> None:
        self.set_location(x, y, z)

    @property
    def loc(self) -> Location:
        position = self.element.find("position")
        location = Location(float(position.get("x")),
                            float(self.element.get("altitude")),
                            float(position.get("y")))
        return location

    def translate(self, dx: float, dy: float, dz: float) -> None:
        self.set_location(self.loc.x + dx,
                          self.loc.y + dy,
                          self.loc.z + dz)

    tag = "w"



class Facility(ElementProxy):
    tag = "facility"

    category = e_property(IntAttribute("category", default_value=1))
    fitting = e_property(IntAttribute("fitting", default_value=60))
    production_timer = e_property(IntAttribute("production_timer", default_value=MAX_INTEGER))
    production_timer_defense = e_property(IntAttribute("production_timer_defense", default_value=MAX_INTEGER))

    def defaults(self):
        self.category = random.randint(1, 7)
        self.fitting = 60


class Tile(ElementProxy, MovableLocationMixin):
    tag = "t"

    id = e_property(IntAttribute("id", default_value=0))
    index = e_property(IntAttribute("index", default_value=1))
    seed = e_property(IntAttribute("seed", default_value=12000))
    biome_type = e_property(IntAttribute("biome_type"))
    team_capture = e_property(IntAttribute("team_capture", default_value=MAX_INTEGER))
    team_capture_progress = e_property(FloatAttribute("team_capture_progress"))
    difficulty_factor = e_property(FloatAttribute("difficulty_factor"))

    @property
    def human_controlled(self) -> bool:
        if self.cc2obj:
            team: Team = self.cc2obj.team(self.team_control)
            return team.human_controlled
        return False

    def on_set_team_control(self):
        self.spawn_data.team_id = self.team_control

    team_control = e_property(IntAttribute("team_control"), side_effect=on_set_team_control)

    def defaults(self):
        self.seed = generate_island_seed()
        self.biome_type = random.randint(1, 7)
        self.team_capture_progress = 0.0
        self.team_control = 0
        self.difficulty_factor = 0.0
        assert self.bounds
        assert self.facility
        assert self.world_position
        assert self.spawn_data

    @property
    def bounds(self) -> Bounds:
        return cast(Bounds, self.get_default_child_by_tag(Bounds))

    @property
    def island_radius(self) -> float:
        return self.bounds.max.x

    @island_radius.setter
    def island_radius(self, radius: int):
        radius = int(radius)
        if radius > 2000:
            if radius > 7000:
                radius = 7000
            self.bounds.min.x = -1 * radius
            self.bounds.min.z = -1 * radius
            self.bounds.max.x = radius
            self.bounds.max.z = radius

    @property
    def spawn_data(self) -> SpawnData:
        sd = cast(SpawnData, self.get_default_child_by_tag(SpawnData))
        sd.cc2obj = self.cc2obj
        return sd

    @property
    def world_position(self) -> WorldPosition:
        return cast(WorldPosition, self.get_default_child_by_tag(WorldPosition))

    @property
    def facility(self) -> Facility:
        return cast(Facility, self.get_default_child_by_tag(Facility))

    def set_position(self, *,
                     x: Optional[float] = None,
                     y: Optional[float] = None,
                     z: Optional[float] = None):
        dx = 0.0
        if x is not None:
            dx = x - self.world_position.x
            self.world_position.x = x
        dy = 0.0
        if y is not None:
            dy = y - self.world_position.y
            self.world_position.y = y
        dz = 0.0
        if z is not None:
            dz = z - self.world_position.z
            self.world_position.z = z

        # update the spawn locations
        for item in self.spawn_data.vehicles.items():
            item.data.world_position.x += dx
            item.data.world_position.y += dy
            item.data.world_position.z += dz

    def move(self, x: float, y: float, z: float) -> None:
        self.set_position(x=x, y=y, z=z)

    def translate(self, dx: float, dy: float, dz: float) -> None:
        self.set_position(x=self.loc.x + dx,
                          y=self.loc.y + dy,
                          z=self.loc.z + dz)

    @property
    def loc(self) -> Location:
        return Location(self.world_position.x, self.world_position.y, self.world_position.z)


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

    def spawn(self, spawn_id: int) -> Optional[VehicleSpawn]:
        for tile in self.tiles:
            for spawn in tile.spawn_data.vehicles.items():
                if spawn.data.respawn_id == spawn_id:
                    return spawn
        return None

    def get_spawn_tile(self, spawn_id: int) -> Tuple[Optional[Tile], Optional[VehicleSpawn]]:
        for tile in self.tiles:
            for spawn in tile.spawn_data.vehicles.items():
                if spawn.data.respawn_id == spawn_id:
                    return tile, spawn
        return None, None

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
    def scene_vehicles(self) -> Element:
        return self.roots[SCENE_ROOT].getroot().findall("./vehicles")[0]

    @property
    def tiles_container(self) -> Element:
        return self.roots[SCENE_ROOT].getroot().findall("./tiles/tiles")[0]

    def new_tile(self) -> Tile:
        """Create a new tile"""
        tile = Tile(element=None, cc2obj=self)
        tile.cc2obj = self
        tile.biome_type = BIOME_SANDY_PINES
        tile.id = self.next_tile_id
        tile.index = tile.id - 1
        self.last_tile_id = tile.id
        self.tiles_container.append(tile.element)
        tile.set_position(x=0, z=0, y=POS_Y_SEABOTTOM)
        return tile

    def remove_tile(self, tile: Tile):
        """Delete a tile"""
        # find the tile element, remove it, then re-compute the id and index values
        tid = str(tile.id)
        index_value = 0
        for tile in self.tiles:
            tile.id = index_value + 1
            tile.index = index_value
            index_value += 1
        tids = [x for x in self.tiles_container if x.attrib.get("id") == tid]
        if tids:
            self.tiles_container.remove(tids[0])
        self.tiles_parent.attrib.update(id_counter=str(index_value))

    def remove_vehicle(self, vehicle: Vehicle):
        """Delete a vehicle and its state data"""
        # this might go wrong if other units refer to this vehicle somehow..
        vparent = self.vehicles_parent
        vsparent = self.vehicle_states_parent

        if vehicle:
            if vehicle.definition_index == VehicleType.Jetty.value:
                return  # dont' delete a jetty, it causes problems if the carrier isnt launched
            if vehicle.definition_index == VehicleType.Carrier.value:
                # if this is the last carrier a team has, mark the team as destroyed.
                team_carriers = [x for x in self.vehicles
                                 if x.team_id == vehicle.team_id and x.definition_index == vehicle.definition_index]
                if len(team_carriers) == 1:
                    # destroy the team
                    team = self.team(vehicle.team_id)
                    team.is_destroyed = True

            vid = str(vehicle.id)
            state = vehicle.state
            if state:
                vse = [x for x in vsparent if x.attrib.get("id") == vid]
                if vse:
                    vsparent.remove(vse[0])
            ve = [x for x in vparent if x.attrib.get("id") == vid]
            if ve:
                vparent.remove(ve[0])
            # if there was a spawn, remove that too
            spawn = self.spawn(vehicle.id)
            if spawn:
                self.remove_spawn(vehicle.id)

    def remove_spawn(self, spawn_id: int):
        tile, spawn = self.get_spawn_tile(spawn_id)
        if spawn and tile:
            tile.spawn_data.vehicles.remove(spawn_id)

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
    def vehicles_parent(self) -> Element:
        return self.roots[VEHICLES_ROOT].getroot().findall("./vehicles")[0]

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
        return self.roots[VEHICLES_ROOT].getroot().findall(f"./vehicle_states/v")

    @property
    def vehicle_states_parent(self) -> Element:
        return self.roots[VEHICLES_ROOT].getroot().findall("./vehicle_states")[0]

    @property
    def vehicle_states(self) -> List[VehicleStateContainer]:
        return [VehicleStateContainer(element=x) for x in self._vehicle_states]

    def new_vehicle(self, v_type: VehicleType):
        # find next id
        v_id = 0
        for item in self.vehicles:
            if item.id > v_id:
                v_id = item.id + 1

        v_next = int(self.scene_vehicles.attrib.get("id_counter", str(v_id)))
        if v_next > v_id:
            v_id = v_next
        v_id += 1
        self.scene_vehicles.attrib["id_counter"] = str(v_id)

        v = Vehicle(element=None, cc2obj=self)
        v.id = v_id
        v.definition_index = v_type.value
        v_state = VehicleStateContainer(element=None, cc2obj=self)
        v_state.id = v_id

        # set default altitude to 20, any lower and things on land probably appear inside terrain and vanish
        # there is no "fall" damage so stuff just falls into place
        v.set_location(y=20)

        statevalues = get_default_state(v_type)
        for statevalue in statevalues:
            # set initial state data
            data = v_state.data
            for attrib_name in statevalue.attribs:
                setattr(data, attrib_name, statevalue.count)
            v_state.data = data

        vpar = self.vehicles_parent
        vpar.append(v.element)
        vspar = self.vehicle_states_parent
        vspar.append(v_state.element)

        return v

    @property
    def next_respawn_id(self) -> int:
        next_id = 0
        for tile in self.tiles:
            for item in tile.spawn_data.vehicles.items():
                if item.data.respawn_id > next_id:
                    next_id = item.data.respawn_id
        return next_id + 1

    @property
    def last_tile_id(self) -> int:
        return int(self.tiles_parent.attrib["id_counter"])

    @last_tile_id.setter
    def last_tile_id(self, value: int):
        self.tiles_parent.attrib["id_counter"] = str(value)

    @property
    def next_tile_id(self) -> int:
        return 1 + self.last_tile_id

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


