"""Managed Unity runtime controller for aim assist, ESP, and mouse UI."""

from __future__ import annotations

import logging
import sys
import threading
import time
from pathlib import Path
from typing import Callable, Optional

from .base import CheatFeature
from ..diagnostics import project_root
from ..models import AimTargetKind
from ..mono.main_thread import MainThreadDispatcher

logger = logging.getLogger(__name__)


def runtime_assembly_path() -> Path:
    if getattr(sys, "frozen", False):
        bundled = Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
        return bundled / "runtime" / "HowToFishTrainer.Runtime.dll"
    return (
        project_root()
        / "runtime"
        / "HowToFishTrainer.Runtime"
        / "bin"
        / "Release"
        / "HowToFishTrainer.Runtime.dll"
    )


class ManagedRuntimeController:
    """Loads and controls the reversible in-memory Unity helper."""

    ASSEMBLY_NAME = "HowToFishTrainer.Runtime"
    NAMESPACE = "HowToFishTrainer.Runtime"

    def __init__(
        self,
        pm: object,
        mono: object,
        patcher: object,
        event_sink: Optional[Callable[[str, dict], None]] = None,
    ):
        self.pm = pm
        self.mono = mono
        self.patcher = patcher
        self.event_sink = event_sink
        self.prepared = False
        self.initialized = False
        self.methods: dict[str, int] = {}
        self.dispatcher: Optional[MainThreadDispatcher] = None
        self._status_lock = threading.Lock()
        self._status_word = 0
        self._status_polled_at = float("-inf")

    def _record(self, event: str, **data) -> None:
        if self.event_sink:
            try:
                self.event_sink(event, data)
            except Exception:
                logger.debug("Failed to record managed runtime event", exc_info=True)

    def prepare(self) -> bool:
        if self.prepared:
            return True
        helper_path = runtime_assembly_path()
        try:
            self.mono.load_assembly(str(helper_path), self.ASSEMBLY_NAME)
            bootstrap = self.mono.find_class(
                self.ASSEMBLY_NAME, "Bootstrap", self.NAMESPACE
            )
            signatures = {
                "Initialize": 0,
                "SetAimEnabled": 1,
                "SetEspEnabled": 1,
                "SetMenuOpen": 1,
                "SetPrivateLobbyConsent": 1,
                "GetAimEnabled": 0,
                "GetEspEnabled": 0,
                "GetMenuOpen": 0,
                "GetEspCount": 0,
                "GetAimTargetKind": 0,
                "GetLastErrorCode": 0,
                "GetStatusWord": 0,
                "GetPrivateLobbyConsent": 0,
                "RequestClientItem": 1,
                "GetClientSpawnState": 0,
                "ResetClientSpawnState": 0,
                "Shutdown": 0,
            }
            for name, param_count in signatures.items():
                method = self.mono.find_method(bootstrap, name, param_count)
                self.methods[name] = self.mono.compile_method(method)

            player = self.mono.find_class("Assembly-CSharp", "Player")
            late_update = self.mono.compile_method(
                self.mono.find_method(player, "LateUpdate", 0)
            )
            self.dispatcher = MainThreadDispatcher(
                self.pm, self.mono, self.patcher, late_update
            )
            self.prepared = True
            self._record(
                "managed_runtime_prepared",
                helper_path=str(helper_path),
                methods=sorted(self.methods),
            )
            return True
        except Exception as exc:
            logger.error("Managed runtime preparation failed: %s", exc)
            self._record("managed_runtime_failed", stage="prepare", error=str(exc))
            return False

    def initialize(self) -> bool:
        if self.initialized:
            return True
        if not self.prepare() or not self.dispatcher:
            return False
        try:
            self.dispatcher.call_static(self.methods["Initialize"])
            self.initialized = True
            self._record("managed_runtime_initialized")
            return True
        except Exception as exc:
            logger.error("Managed runtime initialization failed: %s", exc)
            self._record("managed_runtime_failed", stage="initialize", error=str(exc))
            return False

    def set_bool(self, method: str, value: bool) -> bool:
        if not self.initialize():
            return False
        try:
            self.mono.executor.call(self.methods[method], int(bool(value)))
            self._record("managed_runtime_state", method=method, value=bool(value))
            return True
        except Exception as exc:
            self._record("managed_runtime_failed", stage=method, error=str(exc))
            return False

    def get_int(self, method: str, default: int = 0) -> int:
        if not self.initialized:
            return default
        try:
            return int(self.mono.executor.call(self.methods[method]))
        except Exception:
            return default

    def status_word(self, force: bool = False) -> int:
        now = time.monotonic()
        if not force and now - self._status_polled_at < 0.5:
            return self._status_word
        with self._status_lock:
            now = time.monotonic()
            if force or now - self._status_polled_at >= 0.5:
                self._status_word = self.get_int("GetStatusWord")
                self._status_polled_at = now
        return self._status_word

    def shutdown(self) -> None:
        if not self.initialized:
            return
        try:
            self.mono.executor.call(self.methods["Shutdown"])
            self._record("managed_runtime_shutdown_requested")
        except Exception as exc:
            self._record("managed_runtime_failed", stage="shutdown", error=str(exc))
        finally:
            self.initialized = False

    def has_private_lobby_consent(self) -> bool:
        return bool(self.status_word(force=True) & 0x8)

    def request_client_item(self, item_id: int) -> bool:
        if not self.initialize() or not 0 <= int(item_id) <= 255:
            return False
        try:
            accepted = bool(
                self.mono.executor.call(
                    self.methods["RequestClientItem"], int(item_id)
                )
            )
            self._record(
                "client_spawn_request_queued",
                item_id=int(item_id),
                accepted=accepted,
                private_lobby_consent=self.has_private_lobby_consent(),
            )
            return accepted
        except Exception as exc:
            self._record(
                "managed_runtime_failed",
                stage="RequestClientItem",
                error=str(exc),
            )
            return False

    def get_client_spawn_state(self) -> int:
        return self.get_int("GetClientSpawnState")

    def reset_client_spawn_state(self) -> None:
        if self.initialized:
            try:
                self.mono.executor.call(self.methods["ResetClientSpawnState"])
            except Exception:
                pass


class RuntimeToggleFeature(CheatFeature):
    method_name = ""
    getter_name = ""
    status_mask = 0

    def __init__(self, controller: ManagedRuntimeController, **kwargs):
        super().__init__(
            pm=controller.pm,
            mono=controller.mono,
            patcher=controller.patcher,
            **kwargs,
        )
        self.controller = controller
        self.last_action_message = ""

    def prepare(self) -> bool:
        return self.controller.prepare()

    def enable(self) -> bool:
        if self.controller.set_bool(self.method_name, True):
            self.is_enabled = True
            return True
        self.last_action_message = "Managed runtime is unavailable."
        return False

    def disable(self) -> bool:
        if self.controller.initialized:
            self.controller.set_bool(self.method_name, False)
        self.is_enabled = False
        return True

    def update(self) -> None:
        if self.controller.initialized and self.status_mask:
            self.is_enabled = bool(self.controller.status_word() & self.status_mask)


class AimAssistCheat(RuntimeToggleFeature):
    method_name = "SetAimEnabled"
    getter_name = "GetAimEnabled"
    status_mask = 0x1

    def __init__(self, controller: ManagedRuntimeController, hotkey: str = "F9"):
        super().__init__(
            controller,
            name="Head Aim",
            description="Locks guns to creature heads while ADS + right mouse; players require private-lobby consent.",
            name_zh="枪械锁头",
            description_zh="持枪瞄准并按住右键时锁定头部；玩家目标需私有测试房确认。",
            hotkey=hotkey,
        )

    def get_status_badge(self, language: str = "en") -> str:
        if not self.is_enabled:
            return (
                "[dim red]已关闭[/dim red]"
                if language == "zh"
                else "[dim red]DISABLED[/dim red]"
            )
        raw_kind = (self.controller.status_word() >> 8) & 0x3
        try:
            kind = AimTargetKind(raw_kind)
        except ValueError:
            kind = AimTargetKind.NONE
        label = {
            AimTargetKind.NONE: "等待目标" if language == "zh" else "WAITING",
            AimTargetKind.CREATURE: "锁定生物" if language == "zh" else "CREATURE",
            AimTargetKind.PLAYER: "锁定玩家" if language == "zh" else "PLAYER",
        }[kind]
        return f"[bold green]{label}[/bold green]"


class EspOverlayCheat(RuntimeToggleFeature):
    method_name = "SetEspEnabled"
    getter_name = "GetEspEnabled"
    status_mask = 0x2

    def __init__(self, controller: ManagedRuntimeController, hotkey: str = "F11"):
        super().__init__(
            controller,
            name="Item / Creature ESP",
            description="Shows categorized item and creature labels with distance and obstruction dimming.",
            name_zh="物品 / 生物透视",
            description_zh="显示物品和生物名称、距离、分类颜色，并将遮挡目标变暗。",
            hotkey=hotkey,
        )

    def get_status_badge(self, language: str = "en") -> str:
        if not self.is_enabled:
            return (
                "[dim red]已关闭[/dim red]"
                if language == "zh"
                else "[dim red]DISABLED[/dim red]"
            )
        count = (self.controller.status_word() >> 16) & 0x7FFF
        return (
            f"[bold green]{count} 标签[/bold green]"
            if language == "zh"
            else f"[bold green]{count} LABELS[/bold green]"
        )


class MousePanelFeature(RuntimeToggleFeature):
    method_name = "SetMenuOpen"
    getter_name = "GetMenuOpen"
    status_mask = 0x4

    def __init__(self, controller: ManagedRuntimeController, hotkey: str = "Insert"):
        super().__init__(
            controller,
            name="Mouse Control Panel",
            description="Opens a mouse-driven combat, ESP, experiment, and diagnostics panel.",
            name_zh="鼠标控制面板",
            description_zh="打开可用鼠标操作的战斗、透视、实验和诊断面板。",
            hotkey=hotkey,
        )
