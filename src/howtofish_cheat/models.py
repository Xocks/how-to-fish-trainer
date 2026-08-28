"""Shared, serialization-friendly trainer state models."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum, IntEnum


class SpawnSafety(str, Enum):
    """Whether a runtime prefab may be passed to the native spawn path."""

    SAFE = "safe"
    CONFIRM_REQUIRED = "confirm_required"
    BLOCKED = "blocked"


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

    def normalized(self) -> "AimSettings":
        acquire = min(45.0, max(1.0, float(self.acquire_angle)))
        return AimSettings(
            max_distance=min(300.0, max(10.0, float(self.max_distance))),
            acquire_angle=acquire,
            break_angle=min(60.0, max(acquire, float(self.break_angle))),
            smoothing=min(60.0, max(1.0, float(self.smoothing))),
            allow_players=bool(self.allow_players),
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
