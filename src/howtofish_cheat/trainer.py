"""Trainer engine orchestrating process attachment, Mono runtime, and cheat hotkeys."""

import atexit
import logging
import signal
import sys
import time
from typing import List, Optional
import keyboard
import pymem
import pymem.process
from rich.console import Console
from rich.live import Live

from .features.base import CheatFeature
from .features.health import LockHealthCheat
from .features.hunger import LockHungerCheat
from .features.jump import InfiniteJumpCheat
from .mono.bridge import MonoBridge
from .mono.patcher import MethodPatcher
from .ui.console import TrainerUI

logger = logging.getLogger(__name__)


class HowToFishTrainer:
    """Main trainer orchestrator for How to Fish."""

    def __init__(self, process_name: str = "How to Fish.exe"):
        self.process_name = process_name
        self.pm: Optional[pymem.Pymem] = None
        self.mono: Optional[MonoBridge] = None
        self.patcher: Optional[MethodPatcher] = None
        self.features: List[CheatFeature] = []
        self.is_running = False
        self.status_message = "Starting..."
        self.console = Console()
        self.ui = TrainerUI(self.console)
        self._hotkey_hooks = []

        # Ensure cleanup is called on process termination
        atexit.register(self._cleanup)
        try:
            signal.signal(signal.SIGINT, self._signal_handler)
            signal.signal(signal.SIGTERM, self._signal_handler)
        except Exception:
            pass

    def _signal_handler(self, signum, frame):
        """Catches exit signals and triggers clean shutdown."""
        self.stop()

    def attach(self) -> bool:
        """Attempts to find and attach to the game process and Mono runtime."""
        try:
            self.pm = pymem.Pymem(self.process_name)
            self.status_message = f"Found {self.process_name}. Initializing Mono bridge..."
            self.patcher = MethodPatcher(self.pm)
            self.mono = MonoBridge(self.pm)
            self._setup_features()
            self._setup_hotkeys()
            self.status_message = "Successfully attached! Ready. Press F1 / F2 / F3."
            return True
        except pymem.exception.ProcessNotFound:
            self.pm = None
            self.status_message = f"Waiting for {self.process_name} to launch..."
            return False
        except Exception as e:
            self.status_message = f"Attachment error: {e}"
            self._cleanup()
            return False

    def _setup_features(self) -> None:
        """Initializes all available cheat features and pre-compiles JIT methods."""
        health_cheat = LockHealthCheat(self.pm, self.mono, self.patcher, hotkey="F1")
        hunger_cheat = LockHungerCheat(self.pm, self.mono, self.patcher, hotkey="F2")
        jump_cheat = InfiniteJumpCheat(self.pm, self.mono, self.patcher, hotkey="F3")

        health_cheat.prepare()
        hunger_cheat.prepare()
        jump_cheat.prepare()

        self.features = [health_cheat, hunger_cheat, jump_cheat]

    def _setup_hotkeys(self) -> None:
        """Registers global hotkeys using keyboard hook."""
        self._remove_hotkeys()
        for feature in self.features:
            def make_handler(f):
                return lambda: self._on_hotkey_pressed(f)
            hook = keyboard.add_hotkey(feature.hotkey, make_handler(feature), suppress=False)
            self._hotkey_hooks.append(hook)

        # Register exit hotkey
        exit_hook = keyboard.add_hotkey("F10", self.stop, suppress=False)
        self._hotkey_hooks.append(exit_hook)

    def _remove_hotkeys(self) -> None:
        """Unregisters all active hotkey hooks."""
        for hook in self._hotkey_hooks:
            try:
                keyboard.remove_hotkey(hook)
            except Exception:
                pass
        self._hotkey_hooks.clear()

    def _on_hotkey_pressed(self, feature: CheatFeature) -> None:
        """Handles hotkey trigger and toggles feature."""
        if not self.pm or not self.mono:
            return
        feature.toggle()
        state = "ENABLED" if feature.is_enabled else "DISABLED"
        self.status_message = f"{feature.name} is now [{state}]"

    def _cleanup(self) -> None:
        """Restores all memory patches and frees handles."""
        self._remove_hotkeys()

        for f in self.features:
            try:
                f.disable()
            except Exception:
                pass

        if self.patcher:
            try:
                self.patcher.restore_all()
            except Exception:
                pass
            self.patcher = None

        if self.mono:
            try:
                self.mono.close()
            except Exception:
                pass
            self.mono = None

        if self.pm:
            try:
                self.pm.close_process()
            except Exception:
                pass
            self.pm = None

        self.features.clear()

    def stop(self) -> None:
        """Stops the trainer loop."""
        self.is_running = False
        self.status_message = "Shutting down trainer..."

    def run(self) -> None:
        """Runs the live terminal trainer loop with guaranteed cleanup."""
        self.is_running = True
        self.console.clear()

        try:
            with Live(console=self.console, refresh_per_second=4, screen=False) as live:
                while self.is_running:
                    if self.pm:
                        try:
                            _ = self.pm.read_int(self.mono.module_base)
                        except Exception:
                            self.status_message = "Game closed. Waiting to reconnect..."
                            self._cleanup()

                    if not self.pm:
                        self.attach()

                    if self.pm and self.features:
                        for f in self.features:
                            if f.is_enabled:
                                try:
                                    f.update()
                                except Exception:
                                    pass

                    is_attached = self.pm is not None and self.mono is not None
                    pid = self.pm.process_id if self.pm else 0
                    domain = self.mono.root_domain if (self.mono and self.mono.root_domain) else 0

                    dashboard = self.ui.generate_dashboard(
                        is_attached=is_attached,
                        process_name=self.process_name,
                        pid=pid,
                        mono_domain=domain,
                        features=self.features,
                        status_message=self.status_message,
                    )
                    live.update(dashboard)
                    time.sleep(0.25)
        finally:
            self._cleanup()
            self.console.print("\n[bold green]Trainer stopped cleanly. All memory patches and original game logic restored.[/bold green]")
