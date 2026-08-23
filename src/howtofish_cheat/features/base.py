"""Base cheat feature class definition."""

from abc import ABC, abstractmethod
from typing import Optional
import pymem
from ..mono.bridge import MonoBridge
from ..mono.patcher import MethodPatcher


class CheatFeature(ABC):
    """Abstract base class for individual cheat features."""

    def __init__(self, name: str, description: str, hotkey: str, pm: pymem.Pymem, mono: MonoBridge, patcher: MethodPatcher):
        self.name = name
        self.description = description
        self.hotkey = hotkey
        self.pm = pm
        self.mono = mono
        self.patcher = patcher
        self.is_enabled = False

    @abstractmethod
    def enable(self) -> bool:
        """Enables the cheat."""
        pass

    @abstractmethod
    def disable(self) -> bool:
        """Disables the cheat."""
        pass

    def toggle(self) -> bool:
        """Toggles the cheat state."""
        if self.is_enabled:
            self.disable()
        else:
            self.enable()
        return self.is_enabled

    def update(self) -> None:
        """Optional tick callback for continuous maintenance."""
        pass
