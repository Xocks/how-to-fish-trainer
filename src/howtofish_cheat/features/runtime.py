"""Managed Unity runtime controller for aim, ESP, third person, and mouse UI."""

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
        return bundled / "runtime" / "HowToFishTrainer.Runtime.V030.dll"
    return (
        project_root()
        / "runtime"
        / "HowToFishTrainer.Runtime"
        / "bin"
        / "Release"
        / "HowToFishTrainer.Runtime.V030.dll"
    )


class ManagedRuntimeController:
    """Loads and controls the reversible in-memory Unity helper."""

    ASSEMBLY_NAME = "HowToFishTrainer.Runtime.V030"
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
        self._prepare_attempted = False
        self.last_error = ""
        self.methods: dict[str, int] = {}
        self.dispatcher: Optional[MainThreadDispatcher] = None
        self._status_lock = threading.Lock()
        self._status_word = 0
        self._status_polled_at = float("-inf")
        self._last_catalog_count: Optional[int] = None
        self._last_managed_spawn_state: Optional[int] = None
        self._last_managed_spawn_detail: Optional[tuple[int, int, int]] = None
        self._last_combat_detail: Optional[tuple[int, ...]] = None
        self._last_third_person_detail: Optional[tuple[int, ...]] = None

    def _record(self, event: str, **data) -> None:
        if self.event_sink:
            try:
                self.event_sink(event, data)
            except Exception:
                logger.debug("Failed to record managed runtime event", exc_info=True)

    def prepare(self) -> bool:
        if self.prepared:
            return True
        if self._prepare_attempted:
            return False
        self._prepare_attempted = True
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
                "SetThirdPersonEnabled": 1,
                "SetSilentAimEnabled": 1,
                "SetSilentAimMode": 1,
                "SetAimTrackingMode": 1,
                "SetAimTargetMask": 1,
                "SetPoseMode": 1,
                "SetPoseSpinSpeed": 1,
                "SetPoseLookDown": 1,
                "GetAimEnabled": 0,
                "GetEspEnabled": 0,
                "GetMenuOpen": 0,
                "GetEspCount": 0,
                "GetAimTargetKind": 0,
                "GetAimTargetSpecies": 0,
                "GetAimTargetMask": 0,
                "GetBirdAliveCandidateCount": 0,
                "GetBirdFlyingCandidateCount": 0,
                "GetPlayerCandidateCount": 0,
                "GetLastErrorCode": 0,
                "GetLastSpawnStage": 0,
                "GetLastSpawnRendererCount": 0,
                "GetSpawnRequestSequence": 0,
                "GetStatusWord": 0,
                "GetPrivateLobbyConsent": 0,
                "GetThirdPersonEnabled": 0,
                "GetThirdPersonState": 0,
                "GetThirdPersonBackend": 0,
                "GetThirdPersonSourceCameraId": 0,
                "GetThirdPersonRenderCount": 0,
                "GetThirdPersonRequestedDistanceMm": 0,
                "GetThirdPersonCollisionDistanceMm": 0,
                "GetThirdPersonAppliedDistanceMm": 0,
                "GetThirdPersonHeadOffsetMm": 0,
                "GetThirdPersonBodyRendererCount": 0,
                "GetThirdPersonBodyVisibleCount": 0,
                "GetThirdPersonRestoreReason": 0,
                "GetThirdPersonAvatarBackend": 0,
                "GetAvatarMirrorState": 0,
                "GetAvatarSourceRootId": 0,
                "GetAvatarMeshCount": 0,
                "GetAvatarSkinnedMeshCount": 0,
                "GetAvatarBoneCount": 0,
                "GetAvatarBoundsDistanceMm": 0,
                "GetAvatarRebuildReason": 0,
                "GetAvatarTemplateCandidateCount": 0,
                "GetAvatarAppearanceApplyState": 0,
                "GetAvatarIkCount": 0,
                "GetAvatarAnimationState": 0,
                "GetAvatarAnimationFrameCount": 0,
                "GetAvatarNativeStage": 0,
                "GetAvatarNativeFailureCount": 0,
                "GetSilentAimEnabled": 0,
                "GetSilentAimMode": 0,
                "GetAimTrackingMode": 0,
                "GetPoseState": 0,
                "GetPoseMode": 0,
                "GetPoseSpinSpeed": 0,
                "GetPoseLookDown": 0,
                "GetPoseSentPitchMilliDegrees": 0,
                "GetPoseSentYawMilliDegrees": 0,
                "GetPoseRestoreCount": 0,
                "GetSilentAimState": 0,
                "GetTrackedProjectileCount": 0,
                "SetSelectedSpawnId": 1,
                "SetSelectedCatalogIndex": 1,
                "RequestSelectedSpawn": 0,
                "GetSelectedSpawnId": 0,
                "GetSelectedSpawnMode": 0,
                "GetSelectedSpawnState": 0,
                "GetCatalogCount": 0,
                "GetCatalogEntry": 1,
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
            self.last_error = ""
            self._record(
                "managed_runtime_prepared",
                helper_path=str(helper_path),
                methods=sorted(self.methods),
            )
            return True
        except Exception as exc:
            self.last_error = str(exc)
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
            self.last_error = str(exc)
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
            self.last_error = str(exc)
            self._record("managed_runtime_failed", stage=method, error=str(exc))
            return False

    def get_int(self, method: str, default: int = 0) -> int:
        if not self.initialized:
            return default
        try:
            raw = int(self.mono.executor.call(self.methods[method]))
            raw &= 0xFFFFFFFFFFFFFFFF
            return raw - (1 << 64) if raw & (1 << 63) else raw
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
                catalog_count = self.get_int("GetCatalogCount")
                spawn_state = self.get_int("GetSelectedSpawnState")
                if catalog_count != self._last_catalog_count:
                    self._last_catalog_count = catalog_count
                    self._record(
                        "managed_catalog_state", count=catalog_count
                    )
                if spawn_state != self._last_managed_spawn_state:
                    self._last_managed_spawn_state = spawn_state
                    self._record(
                        "managed_spawn_state", state=spawn_state
                    )
                spawn_detail = (
                    self.get_int("GetSpawnRequestSequence"),
                    self.get_int("GetLastSpawnStage"),
                    self.get_int("GetLastSpawnRendererCount"),
                )
                if spawn_detail != self._last_managed_spawn_detail:
                    self._last_managed_spawn_detail = spawn_detail
                    self._record(
                        "managed_spawn_detail",
                        request_sequence=spawn_detail[0],
                        stage=spawn_detail[1],
                        renderer_count=spawn_detail[2],
                        native_invoked=spawn_detail[1] >= 2 and spawn_state == 4,
                        preview_created=spawn_detail[1] >= 2 and spawn_state != 4,
                        visibility_validated=spawn_detail[1] >= 3,
                    )
                combat_detail = (
                    self.get_int("GetAimTargetKind"),
                    self.get_int("GetAimTargetSpecies"),
                    self.get_int("GetAimTargetMask"),
                    self.get_int("GetThirdPersonState"),
                    self.get_int("GetPoseState"),
                    self.get_int("GetPoseMode"),
                    self.get_int("GetSilentAimState"),
                    self.get_int("GetTrackedProjectileCount"),
                    self.get_int("GetBirdAliveCandidateCount"),
                    self.get_int("GetBirdFlyingCandidateCount"),
                    self.get_int("GetPlayerCandidateCount"),
                    self.get_int("GetPoseSentPitchMilliDegrees"),
                    self.get_int("GetPoseSentYawMilliDegrees"),
                    self.get_int("GetPoseRestoreCount"),
                    self.get_int("GetPoseLookDown"),
                )
                if combat_detail != self._last_combat_detail:
                    self._last_combat_detail = combat_detail
                    self._record(
                        "managed_combat_state",
                        target_kind=combat_detail[0],
                        target_species=combat_detail[1],
                        target_mask=combat_detail[2],
                        third_person_state=combat_detail[3],
                        pose_state=combat_detail[4],
                        pose_mode=combat_detail[5],
                        silent_aim_state=combat_detail[6],
                        tracked_projectiles=combat_detail[7],
                        bird_alive_candidates=combat_detail[8],
                        bird_flying_candidates=combat_detail[9],
                        player_candidates=combat_detail[10],
                        pose_sent_pitch_mdeg=combat_detail[11],
                        pose_sent_yaw_mdeg=combat_detail[12],
                        pose_restore_count=combat_detail[13],
                        pose_look_down=bool(combat_detail[14]),
                        network_effect_verified=False,
                    )
                third_person_detail = (
                    self.get_int("GetThirdPersonState"),
                    self.get_int("GetThirdPersonBackend"),
                    self.get_int("GetThirdPersonSourceCameraId"),
                    self.get_int("GetThirdPersonRenderCount"),
                    self.get_int("GetThirdPersonRequestedDistanceMm"),
                    self.get_int("GetThirdPersonCollisionDistanceMm"),
                    self.get_int("GetThirdPersonAppliedDistanceMm"),
                    self.get_int("GetThirdPersonHeadOffsetMm"),
                    self.get_int("GetThirdPersonBodyRendererCount"),
                    self.get_int("GetThirdPersonBodyVisibleCount"),
                    self.get_int("GetThirdPersonRestoreReason"),
                    self.get_int("GetThirdPersonAvatarBackend"),
                    self.get_int("GetAvatarMirrorState"),
                    self.get_int("GetAvatarSourceRootId"),
                    self.get_int("GetAvatarMeshCount"),
                    self.get_int("GetAvatarSkinnedMeshCount"),
                    self.get_int("GetAvatarBoneCount"),
                    self.get_int("GetAvatarBoundsDistanceMm"),
                    self.get_int("GetAvatarRebuildReason"),
                    self.get_int("GetAvatarTemplateCandidateCount"),
                    self.get_int("GetAvatarAppearanceApplyState"),
                    self.get_int("GetAvatarIkCount"),
                    self.get_int("GetAvatarAnimationState"),
                    self.get_int("GetAvatarAnimationFrameCount"),
                    self.get_int("GetAvatarNativeStage"),
                    self.get_int("GetAvatarNativeFailureCount"),
                )
                if third_person_detail != self._last_third_person_detail:
                    self._last_third_person_detail = third_person_detail
                    self._record(
                        "managed_third_person_state",
                        state=third_person_detail[0],
                        backend=third_person_detail[1],
                        source_camera_id=third_person_detail[2],
                        render_count=third_person_detail[3],
                        requested_distance_mm=third_person_detail[4],
                        collision_distance_mm=third_person_detail[5],
                        applied_distance_mm=third_person_detail[6],
                        head_offset_mm=third_person_detail[7],
                        body_renderer_count=third_person_detail[8],
                        body_visible_count=third_person_detail[9],
                        restore_reason=third_person_detail[10],
                        avatar_backend=third_person_detail[11],
                        avatar_state=third_person_detail[12],
                        avatar_source_root_id=third_person_detail[13],
                        avatar_mesh_count=third_person_detail[14],
                        avatar_skinned_mesh_count=third_person_detail[15],
                        avatar_bone_count=third_person_detail[16],
                        avatar_bounds_distance_mm=third_person_detail[17],
                        avatar_rebuild_reason=third_person_detail[18],
                        avatar_template_candidates=third_person_detail[19],
                        avatar_appearance_apply_state=third_person_detail[20],
                        avatar_ik_count=third_person_detail[21],
                        avatar_animation_state=third_person_detail[22],
                        avatar_animation_frame_count=third_person_detail[23],
                        avatar_native_stage=third_person_detail[24],
                        avatar_native_failure_count=third_person_detail[25],
                        render_path_active=third_person_detail[0] in {1, 2}
                        and third_person_detail[3] > 0
                        and 0 < third_person_detail[6] <= 12000,
                    )
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

    def set_aim_tracking_mode(self, mode: int) -> bool:
        if not self.initialize():
            return False
        try:
            self.mono.executor.call(
                self.methods["SetAimTrackingMode"], 1 if int(mode) == 1 else 0
            )
            return True
        except Exception as exc:
            self.last_error = str(exc)
            return False

    def set_aim_target_mask(self, mask: int) -> bool:
        if not self.initialize():
            return False
        try:
            self.mono.executor.call(self.methods["SetAimTargetMask"], int(mask) & 0x0F)
            return True
        except Exception as exc:
            self.last_error = str(exc)
            return False

    def set_pose_mode(self, mode: int) -> bool:
        if not self.initialize():
            return False
        try:
            self.mono.executor.call(self.methods["SetPoseMode"], int(mode))
            return True
        except Exception as exc:
            self.last_error = str(exc)
            return False

    def set_pose_spin_speed(self, degrees_per_second: int) -> bool:
        if not self.initialize():
            return False
        try:
            value = min(1440, max(90, int(degrees_per_second)))
            self.mono.executor.call(self.methods["SetPoseSpinSpeed"], value)
            return True
        except Exception as exc:
            self.last_error = str(exc)
            return False

    def set_pose_look_down(self, enabled: bool) -> bool:
        if not self.initialize():
            return False
        try:
            self.mono.executor.call(self.methods["SetPoseLookDown"], bool(enabled))
            return True
        except Exception as exc:
            self.last_error = str(exc)
            return False

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

    def set_selected_spawn_id(self, item_id: int) -> bool:
        """Queues an ID selection; Unity applies it on its main thread."""
        if not self.initialize() or not 0 <= int(item_id) <= 255:
            return False
        try:
            accepted = bool(
                self.mono.executor.call(
                    self.methods["SetSelectedSpawnId"], int(item_id)
                )
            )
            self._record(
                "managed_spawn_selection",
                item_id=int(item_id),
                accepted=accepted,
            )
            return accepted
        except Exception as exc:
            self.last_error = str(exc)
            self._record(
                "managed_runtime_failed",
                stage="SetSelectedSpawnId",
                error=str(exc),
            )
            return False

    def set_selected_catalog_index(self, catalog_index: int) -> bool:
        """Selects one immutable managed catalog entry on Unity's main thread."""
        if not self.initialize() or int(catalog_index) < 0:
            return False
        try:
            accepted = bool(
                self.mono.executor.call(
                    self.methods["SetSelectedCatalogIndex"], int(catalog_index)
                )
            )
            self._record(
                "managed_catalog_selection",
                catalog_index=int(catalog_index),
                accepted=accepted,
            )
            return accepted
        except Exception as exc:
            self.last_error = str(exc)
            self._record(
                "managed_runtime_failed",
                stage="SetSelectedCatalogIndex",
                error=str(exc),
            )
            return False

    def request_selected_spawn(self) -> bool:
        """Queues the managed panel/F7 selection for main-thread spawning."""
        if not self.initialize():
            return False
        try:
            accepted = bool(
                self.mono.executor.call(self.methods["RequestSelectedSpawn"])
            )
            self._record(
                "managed_spawn_requested",
                accepted=accepted,
                selected_id=self.get_int("GetSelectedSpawnId", -1),
                selected_mode=self.get_int("GetSelectedSpawnMode"),
            )
            return accepted
        except Exception as exc:
            self._record(
                "managed_runtime_failed",
                stage="RequestSelectedSpawn",
                error=str(exc),
            )
            return False

    def get_selected_spawn_state(self) -> int:
        return self.get_int("GetSelectedSpawnState")

    def get_catalog_count(self) -> int:
        return self.get_int("GetCatalogCount")

    def get_catalog_entries(self, timeout: float = 1.5) -> list[dict]:
        """Reads the immutable catalog snapshot built by Unity's main thread."""
        if not self.initialize():
            return []
        deadline = time.monotonic() + max(0.0, float(timeout))
        count = self.get_catalog_count()
        while count <= 0 and time.monotonic() < deadline:
            time.sleep(0.05)
            count = self.get_catalog_count()
        entries: list[dict] = []
        for index in range(max(0, count)):
            try:
                value_ptr = self.mono.executor.call(
                    self.methods["GetCatalogEntry"], index
                )
                encoded = self.mono.read_string(value_ptr)
                fields = encoded.split("\t")
                if len(fields) not in {8, 10}:
                    continue
                entries.append(
                    {
                        "index": int(fields[0]),
                        "native_id": int(fields[1]),
                        "display_name": fields[2],
                        "spawn_key": fields[3],
                        "source": int(fields[4]),
                        "category": int(fields[5]),
                        "safety": int(fields[6]),
                        "safety_reason": fields[7],
                        "engine_capability": int(fields[8]) if len(fields) >= 10 else 0,
                        "renderer_count": int(fields[9]) if len(fields) >= 10 else 0,
                    }
                )
            except Exception as exc:
                self.last_error = str(exc)
                self._record(
                    "managed_catalog_entry_failed", index=index, error=str(exc)
                )
        self._record(
            "managed_catalog_exported", count=len(entries), runtime_count=count
        )
        return entries

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
        if self.controller.last_error:
            self.last_action_message += f" {self.controller.last_error}"
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
            description="360-degree nearest enabled fish/bird/creature aim while ADS + right mouse, with recoil compensation; players require private-room consent.",
            name_zh="枪械锁头",
            description_zh="持枪瞄准并按住右键时 360°锁定最近的已启用鱼、鸟或生物并补偿后坐力；玩家目标要求私房确认。",
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
            description="Shows 60 Hz item/creature labels with adjustable font size and staggered occlusion.",
            name_zh="物品 / 生物透视",
            description_zh="最高 60 FPS 显示物品/生物标签，支持字体调节与分批遮挡检测。",
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
            description="Opens Combat, ESP, Spawn, Experiment, and Diagnostics without moving the camera.",
            name_zh="鼠标控制面板",
            description_zh="打开战斗、透视、生成器、实验和诊断面板，鼠标不会带动视角。",
            hotkey=hotkey,
        )


class ThirdPersonFeature(RuntimeToggleFeature):
    method_name = "SetThirdPersonEnabled"
    getter_name = "GetThirdPersonEnabled"
    status_mask = 0x10

    def __init__(self, controller: ManagedRuntimeController, hotkey: str = "Home"):
        super().__init__(
            controller,
            name="Third Person Camera",
            description="Reversible shoulder camera with collision shortening and optional reticle.",
            name_zh="第三人称",
            description_zh="可逆肩后相机，支持墙体缩距和可选准星。",
            hotkey=hotkey,
        )

    def get_status_badge(self, language: str = "en") -> str:
        if not self.is_enabled:
            return "[dim red]已关闭[/dim red]" if language == "zh" else "[dim red]DISABLED[/dim red]"
        state = self.controller.get_int("GetThirdPersonState")
        backend = self.controller.get_int("GetThirdPersonBackend")
        renders = self.controller.get_int("GetThirdPersonRenderCount")
        applied = self.controller.get_int("GetThirdPersonAppliedDistanceMm")
        if state in {1, 2} and renders > 0 and 0 < applied <= 12000:
            if language == "zh":
                return "[bold green]渲染回调已生效[/bold green]" if backend == 1 else "[bold green]观察相机已生效[/bold green]"
            return "[bold green]RENDER CALLBACK ACTIVE[/bold green]" if backend == 1 else "[bold green]OBSERVER CAMERA ACTIVE[/bold green]"
        if state == -1:
            return "[bold yellow]等待本地玩家[/bold yellow]" if language == "zh" else "[bold yellow]WAITING FOR PLAYER[/bold yellow]"
        if state == -2:
            return "[bold yellow]等待当前相机[/bold yellow]" if language == "zh" else "[bold yellow]WAITING FOR CAMERA[/bold yellow]"
        if state == -3:
            return "[bold yellow]玩家死亡，已恢复[/bold yellow]" if language == "zh" else "[bold yellow]PLAYER DEAD / RESTORED[/bold yellow]"
        if state == -9:
            return "[bold red]两个相机后端均失败[/bold red]" if language == "zh" else "[bold red]ALL CAMERA BACKENDS FAILED[/bold red]"
        if state == -10:
            return "[bold red]异常相机坐标已阻止[/bold red]" if language == "zh" else "[bold red]INVALID CAMERA COORDINATES BLOCKED[/bold red]"
        return "[bold yellow]等待实际渲染[/bold yellow]" if language == "zh" else "[bold yellow]WAITING FOR RENDER[/bold yellow]"


class SilentAimFeature(RuntimeToggleFeature):
    method_name = "SetSilentAimEnabled"
    getter_name = "GetSilentAimEnabled"
    status_mask = 0x20

    def __init__(self, controller: ManagedRuntimeController, hotkey: str = "End"):
        super().__init__(
            controller,
            name="Silent Aim (Experimental)",
            description="Pre-locks a target without right mouse and corrects the original fire path without moving the camera; private-room network behavior is unverified.",
            name_zh="静默自瞄（实验）",
            description_zh="无需右键预锁目标且不移动镜头，修正游戏原有开火路径；普通客户端网络效果仍需私房验证。",
            hotkey=hotkey,
        )

    def get_status_badge(self, language: str = "en") -> str:
        if not self.is_enabled:
            return "[dim red]已关闭[/dim red]" if language == "zh" else "[dim red]DISABLED[/dim red]"
        state = self.controller.get_int("GetSilentAimState")
        projectiles = self.controller.get_int("GetTrackedProjectileCount")
        if state < 0:
            return f"[bold red]失败关闭 {state}[/bold red]" if language == "zh" else f"[bold red]FAILED {state}[/bold red]"
        return f"[bold yellow]待实测 / {projectiles} 弹丸[/bold yellow]" if language == "zh" else f"[bold yellow]UNVERIFIED / {projectiles} PROJECTILES[/bold yellow]"
