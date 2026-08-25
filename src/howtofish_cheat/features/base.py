"""Base cheat feature class definition."""

from abc import ABC, abstractmethod
from typing import Optional
import pymem
from ..mono.bridge import MonoBridge
from ..mono.patcher import MethodPatcher


class CheatFeature(ABC):
    """Abstract base class for individual cheat features."""

    def __init__(
        self,
        name: str,
        description: str,
        hotkey: str,
        pm: Optional[pymem.Pymem] = None,
        mono: Optional[MonoBridge] = None,
        patcher: Optional[MethodPatcher] = None,
        name_zh: Optional[str] = None,
        description_zh: Optional[str] = None,
    ):
        self.name = name
        self.description = description
        self.name_zh = name_zh or name
        self.description_zh = description_zh or description
        self.hotkey = hotkey
        self.pm = pm
        self.mono = mono
        self.patcher = patcher
        self.is_enabled = False

    def get_name(self, language: str = "en") -> str:
        """Returns the localized feature name."""
        return self.name_zh if language == "zh" else self.name

    def get_description(self, language: str = "en") -> str:
        """Returns the localized feature description."""
        return self.description_zh if language == "zh" else self.description

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
