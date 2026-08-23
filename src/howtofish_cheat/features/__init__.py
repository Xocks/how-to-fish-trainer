"""Cheat features package."""

from .base import CheatFeature
from .health import LockHealthCheat
from .hunger import LockHungerCheat
from .jump import InfiniteJumpCheat
from .ammo import UnlimitedAmmoCheat
from .damage import DamageMultiplierCheat

__all__ = [
    "CheatFeature",
    "LockHealthCheat",
    "LockHungerCheat",
    "InfiniteJumpCheat",
    "UnlimitedAmmoCheat",
    "DamageMultiplierCheat",
]


