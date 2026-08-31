"""Cheat features package."""

from typing import List
from .base import CheatFeature
from .health import LockHealthCheat
from .hunger import LockHungerCheat
from .jump import InfiniteJumpCheat
from .ammo import UnlimitedAmmoCheat
from .damage import DamageMultiplierCheat
from .money import AddMoneyCheat
from .spawner import ItemCategory, ItemSpawnerCheat, SpawnableItem
from .runtime import (
    AimAssistCheat,
    EspOverlayCheat,
    ManagedRuntimeController,
    MousePanelFeature,
    SilentAimFeature,
    ThirdPersonFeature,
)


def get_default_features() -> List[CheatFeature]:
    """Returns unattached instance placeholders for all known cheat features for display purposes."""
    return [
        LockHealthCheat(),
        LockHungerCheat(),
        InfiniteJumpCheat(),
        UnlimitedAmmoCheat(),
        DamageMultiplierCheat(),
        AddMoneyCheat(),
        ItemSpawnerCheat(),
    ]


__all__ = [
    "CheatFeature",
    "LockHealthCheat",
    "LockHungerCheat",
    "InfiniteJumpCheat",
    "UnlimitedAmmoCheat",
    "DamageMultiplierCheat",
    "AddMoneyCheat",
    "ItemCategory",
    "ItemSpawnerCheat",
    "SpawnableItem",
    "ManagedRuntimeController",
    "AimAssistCheat",
    "EspOverlayCheat",
    "MousePanelFeature",
    "ThirdPersonFeature",
    "SilentAimFeature",
    "get_default_features",
]



