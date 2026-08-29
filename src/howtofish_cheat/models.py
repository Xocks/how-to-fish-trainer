"""Shared, serialization-friendly trainer state models."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum, IntEnum


class SpawnSafety(str, Enum):
    """Whether a runtime prefab may be passed to the native spawn path."""

    SAFE = "safe"
    CONFIRM_REQUIRED = "confirm_required"
    HIGH_RISK_LOCAL = "high_risk_local"
    BLOCKED = "blocked"


class SpawnCatalogSource(str, Enum):
    """Where the managed runtime discovered a spawnable object."""

    GAME = "game"
    NAMED = "named"
    RESOURCE = "resource"
    ENGINE = "engine"


class AimTargetFilter(str, Enum):
    """Target sets exposed by the 360-degree aim selector."""

    FISH_ONLY = "fish_only"
    ALL_CREATURES = "all_creatures"


class AimTargetKind(IntEnum):
    NONE = 0
    CREATURE = 1
    PLAYER = 2


@dataclass(frozen=True)
class AimSettings:
    max_distance: float = 120.0
    acquire_angle: float = 12.0
    break_angle: float = 18.0
    smoothing: float = 18.0
    allow_players: bool = False
    target_filter: AimTargetFilter = AimTargetFilter.FISH_ONLY
    nearest_360: bool = True
    ignore_occlusion: bool = False
    recoil_compensation: float = 1.0
    switch_hysteresis: float = 0.10

    def normalized(self) -> "AimSettings":
        acquire = min(45.0, max(1.0, float(self.acquire_angle)))
        return AimSettings(
            max_distance=min(300.0, max(10.0, float(self.max_distance))),
            acquire_angle=acquire,
            break_angle=min(60.0, max(acquire, float(self.break_angle))),
            smoothing=min(60.0, max(1.0, float(self.smoothing))),
            allow_players=bool(self.allow_players),
            target_filter=AimTargetFilter(self.target_filter),
            nearest_360=bool(self.nearest_360),
            ignore_occlusion=bool(self.ignore_occlusion),
            recoil_compensation=min(
                1.0, max(0.0, float(self.recoil_compensation))
            ),
            switch_hysteresis=min(
                0.5, max(0.0, float(self.switch_hysteresis))
            ),
        )


@dataclass(frozen=True)
class EspSettings:
    max_distance: float = 150.0
    max_labels: int = 200
    font_size: int = 14
    projection_hz: int = 60

    def normalized(self) -> "EspSettings":
        return EspSettings(
            max_distance=min(500.0, max(10.0, float(self.max_distance))),
            max_labels=min(500, max(20, int(self.max_labels))),
            font_size=min(36, max(10, int(self.font_size))),
            projection_hz=min(60, max(15, int(self.projection_hz))),
        )


@dataclass(frozen=True)
class OverlayEntitySnapshot:
    instance_id: int
    kind: str
    name: str
    screen_x: float
    screen_y: float
    distance: float
    visible: bool
    danger: str = "normal"
    alive: bool = True

    def to_dict(self) -> dict:
        return asdict(self)


class ClientCapabilityState(str, Enum):
    DISABLED = "disabled"
    PROBE_REQUIRED = "probe_required"
    AVAILABLE = "available"
    PARTIAL = "partial"
    REJECTED = "rejected"
    FAILED_CLOSED = "failed_closed"
