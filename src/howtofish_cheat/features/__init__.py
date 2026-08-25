"""Cheat features package."""

from typing import List
from .base import CheatFeature
from .health import LockHealthCheat
from .hunger import LockHungerCheat
from .jump import InfiniteJumpCheat
from .ammo import UnlimitedAmmoCheat
from .damage import DamageMultiplierCheat
from .money import AddMoneyCheat


def get_default_features() -> List[CheatFeature]:
    """Returns unattached instance placeholders for all known cheat features for display purposes."""
    return [
        LockHealthCheat(),
        LockHungerCheat(),
        InfiniteJumpCheat(),
        UnlimitedAmmoCheat(),
        DamageMultiplierCheat(),
        AddMoneyCheat(),
    ]


__all__ = [
    "CheatFeature",
    "LockHealthCheat",
    "LockHungerCheat",
    "InfiniteJumpCheat",
    "UnlimitedAmmoCheat",
    "DamageMultiplierCheat",
    "AddMoneyCheat",
    "get_default_features",
]



