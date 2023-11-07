import dataclasses
from typing import List, Dict, Optional

from .constants import VehicleType
from .constants import VehicleAttachmentDefinitionIndex

DRIVER = [
    VehicleAttachmentDefinitionIndex.DriverSeat]

SMALL_GROUND_TURRETS = [
    VehicleAttachmentDefinitionIndex.CIWS,
    VehicleAttachmentDefinitionIndex.Gun30mm,
    VehicleAttachmentDefinitionIndex.Gun40mm,
    VehicleAttachmentDefinitionIndex.Radar,
    VehicleAttachmentDefinitionIndex.ObsCam,
    VehicleAttachmentDefinitionIndex.VirusBot,
    VehicleAttachmentDefinitionIndex.MissileIRLauncher]

SMALL_GROUND_AUX = [
    VehicleAttachmentDefinitionIndex.SmallCam,
    VehicleAttachmentDefinitionIndex.SmokeBomb,
    VehicleAttachmentDefinitionIndex.SonicPulse,
    VehicleAttachmentDefinitionIndex.SmokeTrail,
    VehicleAttachmentDefinitionIndex.Flares]

SMALL_AIR_AUX = [
    VehicleAttachmentDefinitionIndex.SmokeBomb,
    VehicleAttachmentDefinitionIndex.SonicPulse,
    VehicleAttachmentDefinitionIndex.SmokeTrail,
    VehicleAttachmentDefinitionIndex.Flares]

LARGE_GROUND_TURRETS = [
    VehicleAttachmentDefinitionIndex.Gun100mm,
    VehicleAttachmentDefinitionIndex.Gun100mmHeavy,
    VehicleAttachmentDefinitionIndex.Gun120mm,
    VehicleAttachmentDefinitionIndex.MissileAALauncher,
]

SHIP_ATTACHMENTS = [
    VehicleAttachmentDefinitionIndex.ShipCam,
    VehicleAttachmentDefinitionIndex.ShipCIWS,
    VehicleAttachmentDefinitionIndex.ShipTorpedo,
    VehicleAttachmentDefinitionIndex.ShipGun160mm,
    VehicleAttachmentDefinitionIndex.MissileAALauncher,  # doesnt actually work on player ships
    VehicleAttachmentDefinitionIndex.ShipCruiseMissile,
    VehicleAttachmentDefinitionIndex.ShipFlare,
    VehicleAttachmentDefinitionIndex.Flares,
    VehicleAttachmentDefinitionIndex.AWACS,
    VehicleAttachmentDefinitionIndex.MissileIRLauncher,
    VehicleAttachmentDefinitionIndex.SmokeTrail,
    # some silly ones that work
    VehicleAttachmentDefinitionIndex.RocketPod,
    VehicleAttachmentDefinitionIndex.Gun100mm,
    VehicleAttachmentDefinitionIndex.Gun100mmHeavy,
    VehicleAttachmentDefinitionIndex.Gun40mm,
    VehicleAttachmentDefinitionIndex.Gun30mm,
    # missile truck
    VehicleAttachmentDefinitionIndex.MissileLaser,
    VehicleAttachmentDefinitionIndex.MissileAA,
]

HARDPOINT_ATTACHMENTS = [
    VehicleAttachmentDefinitionIndex.Gun20mm,
    VehicleAttachmentDefinitionIndex.MissileIR,
    VehicleAttachmentDefinitionIndex.MissileAA,
    VehicleAttachmentDefinitionIndex.MissileTV,
    VehicleAttachmentDefinitionIndex.MissileLaser,
    VehicleAttachmentDefinitionIndex.Torpedo,
    VehicleAttachmentDefinitionIndex.TorpedoCountermesure,
    VehicleAttachmentDefinitionIndex.Noisemaker,
    VehicleAttachmentDefinitionIndex.Bomb0,
    VehicleAttachmentDefinitionIndex.Bomb1,
    VehicleAttachmentDefinitionIndex.Bomb2,
    VehicleAttachmentDefinitionIndex.FuelTank,
    VehicleAttachmentDefinitionIndex.RocketPod,
]

GROUND_RESUPPLY = [
    VehicleAttachmentDefinitionIndex.Refuel,
    VehicleAttachmentDefinitionIndex.RearmIR,
    VehicleAttachmentDefinitionIndex.Rearm20mm,
    VehicleAttachmentDefinitionIndex.Rearm30mm,
    VehicleAttachmentDefinitionIndex.Rearm40mm,
    VehicleAttachmentDefinitionIndex.Rearm100mm,
    VehicleAttachmentDefinitionIndex.Rearm120mm,
    VehicleAttachmentDefinitionIndex.BattleDroids
]

AIR_GIMBAL_TURRETS = [
    VehicleAttachmentDefinitionIndex.AirObsCam,
    VehicleAttachmentDefinitionIndex.GimbalGun,
    VehicleAttachmentDefinitionIndex.BattleDroids,
    VehicleAttachmentDefinitionIndex.Radar,
]


UNIT_ATTACHMENT_OPTIONS: Dict[VehicleType, List[List[Optional[VehicleAttachmentDefinitionIndex]]]] = {
    VehicleType.Barge: [
        DRIVER,
    ],
    VehicleType.Turret: [
        SMALL_GROUND_TURRETS + [VehicleAttachmentDefinitionIndex.Gun120mm, VehicleAttachmentDefinitionIndex.MissileAALauncher],
    ],
    VehicleType.Seal: [
        DRIVER,
        SMALL_GROUND_TURRETS + HARDPOINT_ATTACHMENTS,
        SMALL_GROUND_AUX,
        SMALL_GROUND_AUX
    ],
    VehicleType.Walrus: [
        DRIVER,
        SMALL_GROUND_TURRETS + HARDPOINT_ATTACHMENTS,
        SMALL_GROUND_AUX + [VehicleAttachmentDefinitionIndex.Autocannon],
        SMALL_GROUND_AUX + [VehicleAttachmentDefinitionIndex.Autocannon],
    ],
    VehicleType.Bear: [
        DRIVER,
        SMALL_GROUND_AUX,
        SMALL_GROUND_TURRETS + LARGE_GROUND_TURRETS + HARDPOINT_ATTACHMENTS + [VehicleAttachmentDefinitionIndex.ShipCruiseMissile],
        SMALL_GROUND_AUX,
    ],
    VehicleType.Droid: [
        DRIVER,
        [VehicleAttachmentDefinitionIndex.Autocannon]
    ],
    VehicleType.Mule: [
        DRIVER,
        GROUND_RESUPPLY + SMALL_GROUND_TURRETS,
        GROUND_RESUPPLY + SMALL_GROUND_TURRETS,
        GROUND_RESUPPLY,
        GROUND_RESUPPLY,
        GROUND_RESUPPLY,
        GROUND_RESUPPLY + [VehicleAttachmentDefinitionIndex.MissileAA],
    ],
    VehicleType.Needlefish: [
        DRIVER,
        SHIP_ATTACHMENTS + GROUND_RESUPPLY + [VehicleAttachmentDefinitionIndex.VirusBot],
        SHIP_ATTACHMENTS + GROUND_RESUPPLY,
    ],
    VehicleType.Swordfish: [
        DRIVER,
        SHIP_ATTACHMENTS,
        SHIP_ATTACHMENTS,
        SHIP_ATTACHMENTS,
        SHIP_ATTACHMENTS + GROUND_RESUPPLY,
    ],
    VehicleType.Razorbill: [
        DRIVER,
        HARDPOINT_ATTACHMENTS,
        HARDPOINT_ATTACHMENTS,
        SMALL_AIR_AUX + [VehicleAttachmentDefinitionIndex.Autocannon],
        SMALL_AIR_AUX + [VehicleAttachmentDefinitionIndex.Autocannon],
    ],
    VehicleType.Petrel: [
        DRIVER,
        AIR_GIMBAL_TURRETS,
        HARDPOINT_ATTACHMENTS + [VehicleAttachmentDefinitionIndex.Gun40mm],
        HARDPOINT_ATTACHMENTS + [VehicleAttachmentDefinitionIndex.Gun40mm, VehicleAttachmentDefinitionIndex.Gun100mm],
        HARDPOINT_ATTACHMENTS + [VehicleAttachmentDefinitionIndex.Gun40mm, VehicleAttachmentDefinitionIndex.Gun100mm],
        HARDPOINT_ATTACHMENTS + [VehicleAttachmentDefinitionIndex.Gun40mm],
    ],
    VehicleType.Albatross: [
        DRIVER,
        AIR_GIMBAL_TURRETS,
        HARDPOINT_ATTACHMENTS,
        HARDPOINT_ATTACHMENTS,
        HARDPOINT_ATTACHMENTS,
        HARDPOINT_ATTACHMENTS,
    ],
    VehicleType.Manta: [
        DRIVER,
        AIR_GIMBAL_TURRETS,
        HARDPOINT_ATTACHMENTS,
        HARDPOINT_ATTACHMENTS,
        HARDPOINT_ATTACHMENTS,
        HARDPOINT_ATTACHMENTS,
        [VehicleAttachmentDefinitionIndex.AWACS, VehicleAttachmentDefinitionIndex.Gun40mm],
        SMALL_AIR_AUX,
        SMALL_AIR_AUX,
    ]
}


def get_unit_attachment_choices(v_type: VehicleType, slot: int) -> Optional[List[VehicleAttachmentDefinitionIndex]]:
    unit = UNIT_ATTACHMENT_OPTIONS.get(v_type, None)
    if unit:
        if len(unit) > slot:
            return list(unit[slot])
    return None


def get_unit_attachment_slots(v_type: VehicleType) -> List[Optional[int]]:
    positions = []
    unit = UNIT_ATTACHMENT_OPTIONS.get(v_type, None)
    if unit:
        for _ in unit:
            positions.append(len(positions))

    return positions
