"""Trainer engine orchestrating process attachment, Mono runtime, and cheat hotkeys."""

import atexit
import logging
import signal
import sys
import time
from typing import List, Optional

try:
    import msvcrt
except ImportError:  # pragma: no cover - the trainer itself is Windows-only
    msvcrt = None

import keyboard
import pymem
import pymem.process
from rich.console import Console
from rich.live import Live
from rich.panel import Panel

from .features import (
    CheatFeature,
    LockHealthCheat,
    LockHungerCheat,
    InfiniteJumpCheat,
    UnlimitedAmmoCheat,
    DamageMultiplierCheat,
    AddMoneyCheat,
    ItemSpawnerCheat,
    get_default_features,
)
from .diagnostics import DiagnosticSession
from .mono.bridge import MonoBridge
from .mono.patcher import MethodPatcher
from .ui.console import TrainerUI
from .ui.selector import ItemSelectorState, SelectorAction
from .i18n import tr

logger = logging.getLogger(__name__)


class HowToFishTrainer:
    """Main trainer orchestrator for How to Fish."""

    SELECTOR_MAX_COLUMNS = 4
    SELECTOR_PAIR_MIN_WIDTH = 24
    SELECTOR_VERTICAL_OVERHEAD = 10

    def __init__(
        self,
        process_name: str = "How to Fish.exe",
        language: str = "zh",
        diagnostics: Optional[DiagnosticSession] = None,
    ):
        self.process_name = process_name
        self.language = language
        self.pm: Optional[pymem.Pymem] = None
        self.mono: Optional[MonoBridge] = None
        self.patcher: Optional[MethodPatcher] = None
        self.features: List[CheatFeature] = get_default_features()
        self.is_running = False
        self.status_message = tr("starting", self.language)
        self.console = Console()
        self.ui = TrainerUI(self.console)
        self._feature_hotkey_hooks = []
        self._control_hotkey_hooks = []
        self._selector_requested = False
        self._selector_active = False
        self.diagnostics = diagnostics or DiagnosticSession()
        self.diagnostics.record(
            "session_started", process_name=process_name, language=language
        )

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
            self.diagnostics.record(
                "attached",
                process_name=self.process_name,
                pid=self.pm.process_id,
                mono_domain=self.mono.root_domain,
            )
            return True
        except pymem.exception.ProcessNotFound:
            self.pm = None
            self.status_message = tr("waiting_process", self.language, process_name=self.process_name)
            return False
        except Exception as e:
            self.status_message = f"Attachment error: {e}"
            self.diagnostics.record("attach_failed", error=str(e))
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
        item_spawner = ItemSpawnerCheat(
            self.pm,
            self.mono,
            self.patcher,
            hotkey="F8",
            event_sink=self.diagnostics.sink,
        )

        health_cheat.prepare()
        hunger_cheat.prepare()
        jump_cheat.prepare()
        ammo_cheat.prepare()
        damage_cheat.prepare()
        money_cheat.prepare()
        item_spawner.prepare()

        self.features = [
            health_cheat,
            hunger_cheat,
            jump_cheat,
            ammo_cheat,
            damage_cheat,
            money_cheat,
            item_spawner,
        ]

    def _setup_feature_hotkeys(self) -> None:
        """Registers feature hotkeys (F1-F8, with F7 opening the selector)."""
        self._remove_feature_hotkeys()
        for feature in self.features:
            if isinstance(feature, ItemSpawnerCheat):
                try:
                    selector_hook = keyboard.add_hotkey(
                        feature.select_hotkey,
                        self._request_item_selector,
                        suppress=False,
                    )
                    self._feature_hotkey_hooks.append(selector_hook)
                except Exception as e:
                    logger.debug("Failed to register F7 item selector hotkey: %s", e)

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

    def _get_item_spawner(self) -> Optional[ItemSpawnerCheat]:
        return next(
            (f for f in self.features if isinstance(f, ItemSpawnerCheat)),
            None,
        )

    def _request_item_selector(self) -> None:
        """Queues the F7 selector so Rich UI work stays on the main thread."""
        if self._selector_active:
            return
        spawner = self._get_item_spawner()
        if not self.pm or not self.mono or not spawner:
            self.status_message = tr("selector_not_attached", self.language)
            return
        self._selector_requested = True
        self.status_message = tr("selector_loading", self.language)
        self.diagnostics.record("selector_requested")

    @staticmethod
    def _read_selector_key() -> Optional[str]:
        """Reads one non-blocking Windows console key for the selector."""
        if msvcrt is None or not msvcrt.kbhit():
            return None
        char = msvcrt.getwch()
        if char in {"\x00", "\xe0"}:
            extended = msvcrt.getwch()
            return {"I": "PAGEUP", "Q": "PAGEDOWN"}.get(extended)
        return {
            "\r": "ENTER",
            "\x08": "BACKSPACE",
            "\x1b": "ESC",
            "\x03": "ESC",
        }.get(char, char.upper())

    def _run_item_selector(self, live: Live) -> None:
        """Runs the F7 selector synchronously on the trainer main thread."""
        spawner = self._get_item_spawner()
        self._selector_requested = False
        if not spawner or not self.pm or not self.mono:
            self.status_message = tr("selector_not_attached", self.language)
            return

        self._selector_active = True
        try:
            live.update(
                Panel(
                    tr("selector_loading", self.language),
                    border_style="yellow",
                    padding=(1, 2),
                ),
                refresh=True,
            )
            catalog = spawner.load_catalog()
            if not catalog:
                self.status_message = tr("selector_empty", self.language)
                return

            grid_columns, page_size = self._selector_grid_size(
                self.console.width, self.console.height
            )
            state = ItemSelectorState(page_size=page_size)
            by_id = spawner.catalog_by_id
            console_size = (self.console.width, self.console.height)

            while self.is_running and self.pm:
                current_size = (self.console.width, self.console.height)
                if current_size != console_size:
                    console_size = current_size
                    grid_columns, page_size = self._selector_grid_size(*current_size)
                    state.resize_page(page_size, len(catalog))
                    self.console.clear()
                live.update(
                    self.ui.generate_item_selector(
                        catalog,
                        state,
                        self.language,
                        column_count=grid_columns,
                    ),
                    refresh=True,
                )
                key = self._read_selector_key()
                if key is None:
                    time.sleep(0.03)
                    continue

                result = state.handle_key(key, by_id)
                if result.action == SelectorAction.SELECTED and result.item:
                    selected = spawner.select_item(result.item.id)
                    self.status_message = tr(
                        "selector_selected",
                        self.language,
                        item_id=selected.id,
                        item_name=selected.display_name,
                    )
                    self.diagnostics.record(
                        "selector_confirmed", item=selected.to_dict()
                    )
                    break
                if result.action == SelectorAction.CANCELLED:
                    self.status_message = tr("selector_cancelled", self.language)
                    self.diagnostics.record("selector_cancelled")
                    break
        finally:
            self._selector_active = False
            self._selector_requested = False

    @classmethod
    def _selector_grid_size(cls, width: int, height: int) -> tuple[int, int]:
        """Returns responsive item-pair columns and page capacity."""
        usable_width = max(1, width - 6)
        columns = max(
            1,
            min(cls.SELECTOR_MAX_COLUMNS, usable_width // cls.SELECTOR_PAIR_MIN_WIDTH),
        )
        rows = max(2, height - cls.SELECTOR_VERTICAL_OVERHEAD)
        return columns, columns * rows

    def _on_hotkey_pressed(self, feature: CheatFeature) -> None:
        """Handles hotkey trigger and toggles feature."""
        if not self.pm or not self.mono:
            return
        if self._selector_active and isinstance(feature, ItemSpawnerCheat):
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
        elif isinstance(feature, ItemSpawnerCheat):
            self.status_message = feature.get_action_message(self.language)
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

        self.features = get_default_features()
        self._selector_requested = False
        self._selector_active = False
        self.diagnostics.record("game_resources_cleaned")

    def _cleanup(self) -> None:
        """Restores all memory patches, frees handles, and unhooks all hotkeys."""
        self._cleanup_game_resources()
        self._remove_control_hotkeys()

    def stop(self) -> None:
        """Stops the trainer loop."""
        self.is_running = False
        self.status_message = tr("shutting_down", self.language)
        self.diagnostics.record("stop_requested")

    def run(self) -> None:
        """Runs the live terminal trainer loop with guaranteed cleanup."""
        self.is_running = True
        self.console.clear()

        try:
            console_size = (self.console.width, self.console.height)
            with Live(console=self.console, refresh_per_second=4, screen=True) as live:
                while self.is_running:
                    current_size = (self.console.width, self.console.height)
                    if current_size != console_size:
                        console_size = current_size
                        self.console.clear()

                    if self.pm:
                        try:
                            _ = self.pm.read_int(self.mono.module_base)
                        except Exception:
                            self.status_message = tr("game_closed", self.language)
                            self.diagnostics.record("game_disconnected")
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

                    if self._selector_requested and self.pm and self.mono:
                        self._run_item_selector(live)

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
