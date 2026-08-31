"""Shared, serialization-friendly trainer state models."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum, IntEnum, IntFlag


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


class EngineObjectCapability(str, Enum):
    """What the trainer can safely do with a raw Unity resource object."""

    NOT_ENGINE = "not_engine"
    VISUAL_PREVIEW = "visual_preview"
    DIAGNOSTIC_ONLY = "diagnostic_only"


class AimTargetFilter(str, Enum):
    """Target sets exposed by the 360-degree aim selector."""

    FISH_ONLY = "fish_only"
    ALL_CREATURES = "all_creatures"


class AimTargetKind(IntEnum):
    NONE = 0
    CREATURE = 1
    PLAYER = 2


class AimTargetFlags(IntFlag):
    NONE = 0
    FISH = 1
    BIRD = 2
    OTHER_CREATURE = 4
    PLAYER = 8


class AimTargetSpecies(IntEnum):
    NONE = 0
    FISH = 1
    BIRD = 2
    OTHER_CREATURE = 3
    PLAYER = 4


class AimTrackingMode(str, Enum):
    """How abrupt target motion is handled by visible aim assistance."""

    STABLE_FIRST = "stable_first"
    CONTINUOUS = "continuous"


@dataclass(frozen=True)
class AimMotionSample:
    """Serializable motion observation used by aim-filter tests and logs."""

    instance_id: int
    x: float
    y: float
    z: float
    speed: float
    vertical_speed: float
    stable: bool
    sampled_at: float

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class AimSettings:
    max_distance: float = 120.0
    acquire_angle: float = 12.0
    break_angle: float = 18.0
    smoothing: float = 18.0
    allow_players: bool = False
    target_filter: AimTargetFilter = AimTargetFilter.FISH_ONLY
    target_mask: AimTargetFlags = AimTargetFlags.FISH | AimTargetFlags.BIRD
    nearest_360: bool = True
    ignore_occlusion: bool = False
    recoil_compensation: float = 1.0
    switch_hysteresis: float = 0.10
    tracking_mode: AimTrackingMode = AimTrackingMode.STABLE_FIRST
    max_yaw_speed: float = 240.0
    max_pitch_speed: float = 90.0
    continuous_pitch_speed: float = 120.0
    unstable_grace_seconds: float = 0.2

    def normalized(self) -> "AimSettings":
        acquire = min(45.0, max(1.0, float(self.acquire_angle)))
        target_mask = AimTargetFlags(int(self.target_mask) & 0x0F)
        if self.allow_players:
            target_mask |= AimTargetFlags.PLAYER
        else:
            target_mask &= ~AimTargetFlags.PLAYER
        return AimSettings(
            max_distance=min(300.0, max(10.0, float(self.max_distance))),
            acquire_angle=acquire,
            break_angle=min(60.0, max(acquire, float(self.break_angle))),
            smoothing=min(60.0, max(1.0, float(self.smoothing))),
            allow_players=bool(self.allow_players),
            target_filter=AimTargetFilter(self.target_filter),
            target_mask=target_mask,
            nearest_360=bool(self.nearest_360),
            ignore_occlusion=bool(self.ignore_occlusion),
            recoil_compensation=min(
                1.0, max(0.0, float(self.recoil_compensation))
            ),
            switch_hysteresis=min(
                0.5, max(0.0, float(self.switch_hysteresis))
            ),
            tracking_mode=AimTrackingMode(self.tracking_mode),
            max_yaw_speed=min(720.0, max(30.0, float(self.max_yaw_speed))),
            max_pitch_speed=min(360.0, max(15.0, float(self.max_pitch_speed))),
            continuous_pitch_speed=min(
                360.0, max(15.0, float(self.continuous_pitch_speed))
            ),
            unstable_grace_seconds=min(
                1.0, max(0.05, float(self.unstable_grace_seconds))
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


class ThirdPersonBackend(IntEnum):
    NONE = 0
    RENDER_CALLBACK = 1
    NATIVE_OBSERVER_CAMERA = 2


class ThirdPersonAvatarBackend(IntEnum):
    NONE = 0
    MIRRORED_NETWORK_PRESENTATION = 1
    LOADED_PLAYER_TEMPLATE = 2
    LOCAL_BODY_FALLBACK = 3


class AvatarMirrorState(IntEnum):
    OFF = 0
    BUILDING = 1
    ACTIVE = 2
    NO_SOURCE = 3
    NO_RENDERABLE_CONTENT = 4
    FAILED = 5


class PoseMode(IntEnum):
    OFF = 0
    HIDE_HEAD_BACKWARDS = 1
    HIGH_SPEED_SPIN = 2


@dataclass(frozen=True)
class ThirdPersonSettings:
    distance: float = 3.5
    height: float = 0.35
    shoulder_offset: float = 0.45
    show_crosshair: bool = False
    collision_radius: float = 0.2

    def normalized(self) -> "ThirdPersonSettings":
        return ThirdPersonSettings(
            distance=min(8.0, max(1.5, float(self.distance))),
            height=min(2.0, max(-0.5, float(self.height))),
            shoulder_offset=min(1.5, max(-1.5, float(self.shoulder_offset))),
            show_crosshair=bool(self.show_crosshair),
            collision_radius=min(0.5, max(0.05, float(self.collision_radius))),
        )


@dataclass(frozen=True)
class PoseExperimentSettings:
    enabled: bool = False
    look_down_pitch: float = 89.0
    look_down_enabled: bool = False
    face_backwards: bool = True
    spin_enabled: bool = False
    spin_speed: float = 720.0
    private_lobby_consent: bool = False
    mode: PoseMode = PoseMode.OFF

    def normalized(self) -> "PoseExperimentSettings":
        enabled = bool(self.enabled) and bool(self.private_lobby_consent)
        mode = PoseMode(self.mode)
        if enabled and mode == PoseMode.OFF:
            mode = PoseMode.HIGH_SPEED_SPIN if self.spin_enabled else PoseMode.HIDE_HEAD_BACKWARDS
        if not enabled:
            mode = PoseMode.OFF
        return PoseExperimentSettings(
            enabled=enabled,
            look_down_pitch=min(89.0, max(0.0, float(self.look_down_pitch))),
            look_down_enabled=bool(self.look_down_enabled) and enabled,
            face_backwards=bool(self.face_backwards),
            spin_enabled=bool(self.spin_enabled),
            spin_speed=min(1440.0, max(90.0, float(self.spin_speed))),
            private_lobby_consent=bool(self.private_lobby_consent),
            mode=mode,
        )


class SilentAimMode(str, Enum):
    INITIAL_CORRECTION = "initial_correction"
    PROJECTILE_TRACKING = "projectile_tracking"


@dataclass(frozen=True)
class ProjectileTrackingState:
    projectile_id: int
    target_instance_id: int
    speed: float
    occluded: bool = False
    target_alive: bool = True
    server_acceptance: ClientCapabilityState = ClientCapabilityState.PROBE_REQUIRED

    def to_dict(self) -> dict:
        data = asdict(self)
        data["server_acceptance"] = self.server_acceptance.value
        return data
