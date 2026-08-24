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
from .features.ammo import UnlimitedAmmoCheat
from .features.damage import DamageMultiplierCheat
from .features.money import AddMoneyCheat
from .mono.bridge import MonoBridge
from .mono.patcher import MethodPatcher
from .ui.console import TrainerUI
from .i18n import tr

logger = logging.getLogger(__name__)


class HowToFishTrainer:
    """Main trainer orchestrator for How to Fish."""

    def __init__(self, process_name: str = "How to Fish.exe", language: str = "zh"):
        self.process_name = process_name
        self.language = language
        self.pm: Optional[pymem.Pymem] = None
        self.mono: Optional[MonoBridge] = None
        self.patcher: Optional[MethodPatcher] = None
        self.features: List[CheatFeature] = []
        self.is_running = False
        self.status_message = tr("starting", self.language)
        self.console = Console()
        self.ui = TrainerUI(self.console)
        self._feature_hotkey_hooks = []
        self._control_hotkey_hooks = []

        # Register global control hotkeys (F10 exit, F12 toggle language) immediately
        self._setup_control_hotkeys()

        # Ensure cleanup is called on process termination
        atexit.register(self._cleanup)
        try:
            signal.signal(signal.SIGINT, self._signal_handler)
            signal.signal(signal.SIGTERM, self._signal_handler)
        except Exception:
            pass

    def _setup_control_hotkeys(self) -> None:
        """Registers persistent control hotkeys (F10, F12) that work at any time."""
        self._remove_control_hotkeys()
        try:
            exit_hook = keyboard.add_hotkey("F10", self.stop, suppress=False)
            self._control_hotkey_hooks.append(exit_hook)
        except Exception as e:
            logger.debug(f"Failed to register F10 exit hotkey: {e}")

        try:
            lang_hook = keyboard.add_hotkey("F12", self.toggle_language, suppress=False)
            self._control_hotkey_hooks.append(lang_hook)
        except Exception as e:
            logger.debug(f"Failed to register F12 language hotkey: {e}")

    def _remove_control_hotkeys(self) -> None:
        """Unregisters persistent control hotkeys."""
        for hook in self._control_hotkey_hooks:
            try:
                keyboard.remove_hotkey(hook)
            except Exception:
                pass
        self._control_hotkey_hooks.clear()

    def toggle_language(self) -> None:
        """Toggles interface language between Chinese ('zh') and English ('en')."""
        self.language = "en" if self.language == "zh" else "zh"
        self.status_message = tr("lang_switched", self.language)

    def _signal_handler(self, signum, frame):
        """Catches exit signals and triggers clean shutdown."""
        self.stop()

    def attach(self) -> bool:
        """Attempts to find and attach to the game process and Mono runtime."""
        try:
            self.pm = pymem.Pymem(self.process_name)
            self.status_message = tr("found_process", self.language, process_name=self.process_name)
            self.patcher = MethodPatcher(self.pm)
            self.mono = MonoBridge(self.pm)
            self._setup_features()
            self._setup_feature_hotkeys()
            self.status_message = tr("attached_ready", self.language)
            return True
        except pymem.exception.ProcessNotFound:
            self.pm = None
            self.status_message = tr("waiting_process", self.language, process_name=self.process_name)
            return False
        except Exception as e:
            self.status_message = f"Attachment error: {e}"
            self._cleanup_game_resources()
            return False

    def _setup_features(self) -> None:
        """Initializes all available cheat features and pre-compiles JIT methods."""
        health_cheat = LockHealthCheat(self.pm, self.mono, self.patcher, hotkey="F1")
        hunger_cheat = LockHungerCheat(self.pm, self.mono, self.patcher, hotkey="F2")
        jump_cheat = InfiniteJumpCheat(self.pm, self.mono, self.patcher, hotkey="F3")
        ammo_cheat = UnlimitedAmmoCheat(self.pm, self.mono, self.patcher, hotkey="F4")
        damage_cheat = DamageMultiplierCheat(self.pm, self.mono, self.patcher, hotkey="F5")
        money_cheat = AddMoneyCheat(self.pm, self.mono, self.patcher, hotkey="F6")

        health_cheat.prepare()
        hunger_cheat.prepare()
        jump_cheat.prepare()
        ammo_cheat.prepare()
        damage_cheat.prepare()
        money_cheat.prepare()

        self.features = [health_cheat, hunger_cheat, jump_cheat, ammo_cheat, damage_cheat, money_cheat]

    def _setup_feature_hotkeys(self) -> None:
        """Registers feature hotkeys (F1..F6)."""
        self._remove_feature_hotkeys()
        for feature in self.features:
            def make_handler(f):
                return lambda: self._on_hotkey_pressed(f)
            try:
                hook = keyboard.add_hotkey(feature.hotkey, make_handler(feature), suppress=False)
                self._feature_hotkey_hooks.append(hook)
            except Exception as e:
                logger.debug(f"Failed to register hotkey {feature.hotkey}: {e}")

    def _remove_feature_hotkeys(self) -> None:
        """Unregisters all active feature hotkey hooks."""
        for hook in self._feature_hotkey_hooks:
            try:
                keyboard.remove_hotkey(hook)
            except Exception:
                pass
        self._feature_hotkey_hooks.clear()

    def _on_hotkey_pressed(self, feature: CheatFeature) -> None:
        """Handles hotkey trigger and toggles feature."""
        if not self.pm or not self.mono:
            return
        feature.toggle()
        fname = feature.get_name(self.language) if hasattr(feature, "get_name") else feature.name
        if isinstance(feature, DamageMultiplierCheat):
            if self.language == "zh":
                mode_name = feature.MODES_ZH[feature.current_mode_index]
                self.status_message = f"{fname} 已设置为 [{mode_name}]"
            else:
                mode_name = feature.MODES[feature.current_mode_index]
                self.status_message = f"{fname} set to [{mode_name}]"
        elif isinstance(feature, AddMoneyCheat):
            if self.language == "zh":
                self.status_message = f"成功增加 +${feature.add_amount:,} 金币！(累计增加: +${feature.total_added:,})"
            else:
                self.status_message = f"+${feature.add_amount:,} money added! (Total added: +${feature.total_added:,})"
        elif hasattr(feature, "last_action_message") and feature.last_action_message:
            self.status_message = feature.last_action_message
        else:
            if self.language == "zh":
                state = "已开启" if feature.is_enabled else "已关闭"
                self.status_message = f"{fname} 当前状态: [{state}]"
            else:
                state = "ENABLED" if feature.is_enabled else "DISABLED"
                self.status_message = f"{fname} is now [{state}]"

    def _cleanup_game_resources(self) -> None:
        """Restores memory patches and frees game handles without unhooking global hotkeys."""
        self._remove_feature_hotkeys()

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

    def _cleanup(self) -> None:
        """Restores all memory patches, frees handles, and unhooks all hotkeys."""
        self._cleanup_game_resources()
        self._remove_control_hotkeys()

    def stop(self) -> None:
        """Stops the trainer loop."""
        self.is_running = False
        self.status_message = tr("shutting_down", self.language)

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
                            self.status_message = tr("game_closed", self.language)
                            self._cleanup_game_resources()

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
                        language=self.language,
                    )
                    live.update(dashboard)
                    time.sleep(0.25)
        finally:
            self._cleanup()
            exit_text = tr("stopped_clean", self.language)
            self.console.print(f"\n[bold green]{exit_text}[/bold green]")
