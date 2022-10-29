from abc import ABC, abstractmethod
from typing import List, Optional
from xml.etree.ElementTree import Element

from .teams import Team
from .tiles import Tile
from .vehicles.vehicle import Vehicle
from .vehicles.vehicle_state import VehicleStateContainer
from ..constants import VehicleType


class CC2Save(ABC):

    @property
    @abstractmethod
    def tiles(self) -> List[Tile]:
        pass

    @abstractmethod
    def tile(self, tile_id: int) -> Tile:
        """Get a tile by ID"""
        pass

    @abstractmethod
    def vehicle(self, vid: int):
        pass

    @property
    @abstractmethod
    def tiles_parent(self) -> Element:
        pass

    @property
    @abstractmethod
    def scene_vehicles(self) -> Element:
        pass

    @abstractmethod
    def new_tile(self) -> Tile:
        pass

    @abstractmethod
    def remove_tile(self, tile: Tile):
        """Delete a tile"""
        pass

    @abstractmethod
    def remove_vehicle(self, vehicle: Vehicle):
        """Delete a vehicle and its state data"""
        pass

    @property
    @abstractmethod
    def teams(self) -> List[Team]:
        pass

    @abstractmethod
    def team(self, teamid: int) -> Team:
        """Get a team by ID"""
        pass

    @property
    @abstractmethod
    def vehicles_parent(self) -> Element:
        pass

    @property
    @abstractmethod
    def vehicles(self) -> List[Vehicle]:
        pass

    @abstractmethod
    def vehicle_state(self, vid) -> Optional[VehicleStateContainer]:
        pass

    @property
    @abstractmethod
    def vehicle_states_parent(self) -> Element:
        pass

    @property
    @abstractmethod
    def vehicle_states(self) -> List[VehicleStateContainer]:
        pass

    @abstractmethod
    def new_vehicle(self, v_type: VehicleType):
        pass

    @abstractmethod
    def export(self) -> str:
        pass
