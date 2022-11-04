import dataclasses
from typing import Optional, Iterable
from ..constants import VehicleAttachmentDefinitionIndex


@dataclasses.dataclass
class UnitAttachment:
    name: str
    position: int = 0
    choices: Optional[Iterable[VehicleAttachmentDefinitionIndex]] = None

