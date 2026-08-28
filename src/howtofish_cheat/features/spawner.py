"""Server-authoritative item spawning through the game's native command path."""

from __future__ import annotations

import logging
import struct
import threading
import time
from dataclasses import asdict, dataclass
from enum import IntEnum
from typing import Callable, Dict, List, Optional, Tuple

from .base import CheatFeature
from ..i18n import tr
from ..models import ClientCapabilityState, SpawnSafety
from ..mono.main_thread import MAIN_THREAD_PATCH_LOCK

logger = logging.getLogger(__name__)


class ItemCategory(IntEnum):
    """Values used by the game's ``ItemType`` enum."""

    UNKNOWN = -1
    ITEM = 0
    FISH = 1
    WEAPON = 2


@dataclass(frozen=True)
class SpawnableItem:
    """Stable display metadata for a runtime-resolved item prefab."""

    id: int
    display_name: str
    spawn_key: str
    category: ItemCategory
    is_quest_item: bool = False
    safety: SpawnSafety = SpawnSafety.SAFE
    safety_reason: str = ""

    @property
    def requires_confirmation(self) -> bool:
        """Whether selecting this item must show the risk confirmation prompt."""
        return self.safety == SpawnSafety.CONFIRM_REQUIRED or (
            self.safety != SpawnSafety.BLOCKED
            and (self.is_quest_item or self.category == ItemCategory.UNKNOWN)
        )

    @property
    def is_selectable(self) -> bool:
        return self.safety != SpawnSafety.BLOCKED

    def to_dict(self) -> dict:
        data = asdict(self)
        data["category"] = self.category.name.lower()
        data["safety"] = self.safety.value
        return data


class ItemSpawnerCheat(CheatFeature):
    """Enumerates and spawns native Item prefabs for a local server/host."""

    SELECT_HOTKEY = "F7"
    SPAWN_COOLDOWN_SECONDS = 0.5
    CLIENT_SPAWN_COOLDOWN_SECONDS = 2.0
    MAIN_THREAD_TIMEOUT_SECONDS = 4.0
    MAIN_THREAD_PATCH_ID = "spawner.main_thread_dispatch"

    # Build 24911270 keeps catchable creatures at IDs 0-52. Item._type is not
    # serialized on the prefab catalog, so get_Type() returns its default value
    # until an item instance has gone through Unity initialization.
    FISH_ID_RANGE = range(0, 53)
    WEAPON_SPAWN_KEYS = frozenset(
        {
            "assaultrifle",
            "brassknuckles",
            "brassknucklespackedbackup",
            "dynamite",
            "knife",
            "knifepackedbackup",
            "pistol",
            "shotgun",
            "smg",
            "sniperrifle",
        }
    )
    BLOCKED_SPAWN_KEYS = frozenset({"deadplayer"})
    CONFIRM_SPAWN_KEYS = frozenset({"dynamite"})

    def __init__(
        self,
        pm: Optional[object] = None,
        mono: Optional[object] = None,
        patcher: Optional[object] = None,
        hotkey: str = "F8",
        event_sink: Optional[Callable[[str, dict], None]] = None,
        clock: Callable[[], float] = time.monotonic,
        wait_clock: Callable[[], float] = time.monotonic,
        sleeper: Callable[[float], None] = time.sleep,
        client_requester: Optional[Callable[[int], bool]] = None,
        client_state_reader: Optional[Callable[[], int]] = None,
        client_state_resetter: Optional[Callable[[], None]] = None,
    ):
        super().__init__(
            name="Item Spawner",
            description="F7 selects an item by ID; F8 spawns one item in front of the host player.",
            name_zh="物品生成器",
            description_zh="按 F7 输入物品 ID，按 F8 在房主人物前方生成一个物品。",
            hotkey=hotkey,
            pm=pm,
            mono=mono,
            patcher=patcher,
        )
        self.select_hotkey = self.SELECT_HOTKEY
        self.catalog: List[SpawnableItem] = []
        self.selected_item: Optional[SpawnableItem] = None
        self.last_action_message = ""
        self.last_action_key = ""
        self.last_action_kwargs: dict = {}
        self._event_sink = event_sink
        self._clock = clock
        self._wait_clock = wait_clock
        self._sleeper = sleeper
        self._last_spawn_at = float("-inf")
        self._last_client_spawn_at = float("-inf")
        self._spawn_lock = threading.Lock()
        self._pinned_spawn_strings: Dict[str, Tuple[int, int]] = {}

        self.get_spawnable_native: Optional[int] = None
        self.get_display_name_native: Optional[int] = None
        self.get_object_name_native: Optional[int] = None
        self.get_type_native: Optional[int] = None
        self.get_is_quest_item_native: Optional[int] = None
        self.get_dead_player_native: Optional[int] = None
        self.use_spawn_command_native: Optional[int] = None
        self.get_server_instance_native: Optional[int] = None
        self.get_is_server_initialized_native: Optional[int] = None
        self.player_late_update_native: Optional[int] = None
        self.client_requester = client_requester
        self.client_state_reader = client_state_reader
        self.client_state_resetter = client_state_resetter
        self.client_capability = ClientCapabilityState.DISABLED
        self._client_request_pending = False

    @property
    def catalog_by_id(self) -> Dict[int, SpawnableItem]:
        return {item.id: item for item in self.catalog}

    def _record(self, event: str, **data) -> None:
        if self._event_sink:
            try:
                self._event_sink(event, data)
            except Exception:
                logger.debug("Failed to write item spawner diagnostic event", exc_info=True)

    def _set_action(self, key: str, fallback: str, **kwargs) -> None:
        self.last_action_key = key
        self.last_action_kwargs = kwargs
        self.last_action_message = fallback

    def get_action_message(self, language: str = "en") -> str:
        if not self.last_action_key:
            return self.last_action_message
        return tr(self.last_action_key, language, **self.last_action_kwargs)

    def _compile(
        self,
        class_ptr: int,
        method_name: str,
        param_count: int,
        param_type_codes: Optional[tuple[int, ...]] = None,
    ) -> int:
        if param_type_codes is None:
            method = self.mono.find_method(class_ptr, method_name, param_count)
        else:
            method = self.mono.find_method_by_signature(
                class_ptr, method_name, param_type_codes
            )
        return self.mono.compile_method(method)

    def prepare(self) -> bool:
        """Resolves native entry points without scanning the catalog yet."""
        if not self.pm or not self.mono:
            return False
        try:
            game_info_cls = self.mono.find_class("Assembly-CSharp", "GameInfo")
            item_cls = self.mono.find_class("Assembly-CSharp", "Item")
            commands_cls = self.mono.find_class("Assembly-CSharp", "DazedCommands")
            server_cls = self.mono.find_class("Assembly-CSharp", "Server")
            unity_object_cls = self.mono.find_class(
                "UnityEngine.CoreModule", "Object", "UnityEngine"
            )
            network_behaviour_cls = self.mono.find_class(
                "FishNet.Runtime", "NetworkBehaviour", "FishNet.Object"
            )
            player_cls = self.mono.find_class("Assembly-CSharp", "Player")

            self.get_spawnable_native = self._compile(
                game_info_cls,
                "GetSpawnable",
                1,
                (self.mono.MONO_TYPE_U1,),
            )
            self.get_display_name_native = self._compile(item_cls, "GetName", 0)
            self.get_object_name_native = self._compile(unity_object_cls, "get_name", 0)
            self.get_type_native = self._compile(item_cls, "get_Type", 0)
            self.get_is_quest_item_native = self._compile(
                item_cls, "get_IsQuestItem", 0
            )
            self.get_dead_player_native = self._compile(
                item_cls, "get_DeadPlayer", 0
            )
            self.use_spawn_command_native = self._compile(
                commands_cls, "UseSpawnCommand", 2
            )
            self.get_server_instance_native = self._compile(
                server_cls, "get_Instance", 0
            )
            self.get_is_server_initialized_native = self._compile(
                network_behaviour_cls, "get_IsServerInitialized", 0
            )
            self.player_late_update_native = self._compile(
                player_cls, "LateUpdate", 0
            )
            self._record("spawner_prepared", success=True)
            return True
        except Exception as exc:
            logger.error("Failed to prepare Item Spawner: %s", exc)
            self._set_action(
                "spawner_init_failed",
                f"Item spawner initialization failed: {exc}",
                error=str(exc),
            )
            self._record("spawner_prepared", success=False, error=str(exc))
            return False

    def load_catalog(self, force: bool = False) -> List[SpawnableItem]:
        """Scans the game's byte-ID spawn registry and returns safe metadata."""
        if self.catalog and not force:
            return list(self.catalog)
        if not self.pm or not self.mono or not self.get_spawnable_native:
            if not self.prepare():
                return []

        discovered: List[SpawnableItem] = []
        failures = 0
        for item_id in range(256):
            try:
                prefab_ptr = self.mono.executor.call(
                    self.get_spawnable_native, item_id
                )
                if not prefab_ptr:
                    continue

                display_ptr = self.mono.executor.call(
                    self.get_display_name_native, prefab_ptr
                )
                object_name_ptr = self.mono.executor.call(
                    self.get_object_name_native, prefab_ptr
                )
                display_name = self.mono.read_string(display_ptr).strip()
                object_name = self.mono.read_string(object_name_ptr).strip()
                spawn_key = object_name.replace(" ", "").lower()
                if not spawn_key:
                    failures += 1
                    continue

                raw_category = int(
                    self.mono.executor.call(self.get_type_native, prefab_ptr)
                )
                try:
                    native_category = ItemCategory(raw_category)
                except ValueError:
                    native_category = ItemCategory.UNKNOWN
                category = self._classify_item(
                    item_id, spawn_key, native_category
                )

                is_quest_item = bool(
                    self.mono.executor.call(
                        self.get_is_quest_item_native, prefab_ptr
                    )
                )
                has_dead_player = bool(
                    self.mono.executor.call(
                        self.get_dead_player_native, prefab_ptr
                    )
                )
                safety, safety_reason = self._assess_safety(
                    item_id=item_id,
                    spawn_key=spawn_key,
                    category=category,
                    is_quest_item=is_quest_item,
                    has_dead_player=has_dead_player,
                )
                discovered.append(
                    SpawnableItem(
                        id=item_id,
                        display_name=display_name or object_name,
                        spawn_key=spawn_key,
                        category=category,
                        is_quest_item=is_quest_item,
                        safety=safety,
                        safety_reason=safety_reason,
                    )
                )
            except Exception:
                failures += 1
                logger.debug("Failed to inspect spawnable item ID %d", item_id, exc_info=True)

        order = {
            ItemCategory.ITEM: 0,
            ItemCategory.FISH: 1,
            ItemCategory.WEAPON: 2,
            ItemCategory.UNKNOWN: 3,
        }
        self.catalog = sorted(discovered, key=lambda item: (order[item.category], item.id))
        if self.selected_item and self.selected_item.id not in self.catalog_by_id:
            self.selected_item = None
        self._set_action(
            "spawner_catalog_loaded",
            f"Loaded {len(self.catalog)} spawnable items.",
            count=len(self.catalog),
        )
        self._record(
            "catalog_loaded",
            count=len(self.catalog),
            failures=failures,
            lookup="GameInfo.GetSpawnable(System.Byte)",
            category_counts={
                category.name.lower(): sum(
                    item.category == category for item in self.catalog
                )
                for category in ItemCategory
            },
            items=[item.to_dict() for item in self.catalog],
        )
        return list(self.catalog)

    @classmethod
    def _classify_item(
        cls,
        item_id: int,
        spawn_key: str,
        native_category: ItemCategory,
    ) -> ItemCategory:
        """Classifies uninitialized prefabs using native data plus build layout."""
        if native_category in {ItemCategory.FISH, ItemCategory.WEAPON}:
            return native_category
        if item_id in cls.FISH_ID_RANGE:
            return ItemCategory.FISH
        if spawn_key in cls.WEAPON_SPAWN_KEYS:
            return ItemCategory.WEAPON
        return native_category

    @classmethod
    def _assess_safety(
        cls,
        item_id: int,
        spawn_key: str,
        category: ItemCategory,
        is_quest_item: bool,
        has_dead_player: bool = False,
    ) -> tuple[SpawnSafety, str]:
        """Returns a fail-closed safety decision for an uninitialized prefab."""
        normalized = spawn_key.replace(" ", "").lower()
        if (
            item_id == 53
            or normalized in cls.BLOCKED_SPAWN_KEYS
            or has_dead_player
        ):
            return SpawnSafety.BLOCKED, "network_actor_requires_player_state"
        if is_quest_item:
            return SpawnSafety.CONFIRM_REQUIRED, "quest_item"
        if category == ItemCategory.FISH:
            return SpawnSafety.CONFIRM_REQUIRED, "creature_prefab"
        if category == ItemCategory.UNKNOWN:
            return SpawnSafety.CONFIRM_REQUIRED, "unknown_prefab"
        if normalized in cls.CONFIRM_SPAWN_KEYS:
            return SpawnSafety.CONFIRM_REQUIRED, "explosive_item"
        return SpawnSafety.SAFE, ""

    def select_item(self, item_id: int) -> Optional[SpawnableItem]:
        item = self.catalog_by_id.get(item_id)
        if item and not item.is_selectable:
            self._set_action(
                "spawner_blocked",
                f"ID {item.id}: {item.display_name} is blocked for crash safety.",
                item_id=item.id,
                item_name=item.display_name,
                reason=item.safety_reason,
            )
            self._record("item_selection_blocked", item=item.to_dict())
            return None
        if item:
            self.selected_item = item
            self._set_action(
                "spawner_selected",
                f"Selected ID {item.id}: {item.display_name}",
                item_id=item.id,
                item_name=item.display_name,
            )
            self._record("item_selected", item=item.to_dict())
        return item

    def is_server_authorized(self) -> bool:
        """Returns true only when the local game instance owns the server."""
        if (
            not self.mono
            or not self.get_server_instance_native
            or not self.get_is_server_initialized_native
        ):
            return False
        server_ptr = self.mono.executor.call(self.get_server_instance_native)
        if not server_ptr:
            return False
        return bool(
            self.mono.executor.call(
                self.get_is_server_initialized_native, server_ptr
            )
        )

    def _get_pinned_spawn_string(self, spawn_key: str) -> int:
        """Returns one process-lifetime pinned string for a spawn key.

        Build 24911270 crashes inside ``mono_gchandle_free`` when the handle is
        released immediately after the native spawn command. Keeping one
        handle per discovered key bounds the retained objects to the catalog
        size (currently 85) and lets the OS reclaim them with the game process.
        """
        cached = self._pinned_spawn_strings.get(spawn_key)
        if cached:
            return cached[0]

        managed_name = self.mono.create_string(spawn_key)
        gc_handle = self.mono.pin_object(managed_name)
        self._pinned_spawn_strings[spawn_key] = (managed_name, gc_handle)
        self._record(
            "spawn_string_pinned",
            spawn_key=spawn_key,
            lifetime="game_process",
            pinned_key_count=len(self._pinned_spawn_strings),
        )
        return managed_name

    @staticmethod
    def _build_main_thread_stub(
        state_addr: int, managed_name: int, spawn_function: int
    ) -> bytes:
        """Builds a one-shot x64 thunk executed by ``Player.LateUpdate``."""
        stub = bytearray()
        stub.extend(b"\x48\xB8" + struct.pack("<Q", state_addr))
        stub.extend(b"\x80\x38\x01")  # cmp byte ptr [rax], 1
        stub.extend(b"\x75\x00")  # jne done
        jump_displacement_index = len(stub) - 1
        stub.extend(b"\xC6\x00\x02")  # mov byte ptr [rax], 2
        stub.extend(b"\x48\x83\xEC\x28")  # shadow space + alignment
        stub.extend(b"\x48\xB9" + struct.pack("<Q", managed_name))
        stub.extend(b"\x31\xD2")  # xor edx, edx (spawnDead = false)
        stub.extend(b"\x48\xB8" + struct.pack("<Q", spawn_function))
        stub.extend(b"\xFF\xD0")  # call rax
        stub.extend(b"\x48\x83\xC4\x28")
        stub.extend(b"\x48\xB8" + struct.pack("<Q", state_addr))
        stub.extend(b"\xC6\x00\x03")  # mov byte ptr [rax], 3
        wait_index = len(stub)
        stub.extend(b"\xF3\x90")  # pause while the prologue is restored
        stub.extend(b"\x80\x38\x04")  # cmp byte ptr [rax], 4
        stub.extend(b"\x75\x00")  # jne wait
        wait_displacement_index = len(stub) - 1
        stub.extend(b"\xC3")
        done_index = len(stub)
        stub.extend(b"\xC3")
        stub[jump_displacement_index] = (
            done_index - (jump_displacement_index + 1)
        ) & 0xFF
        stub[wait_displacement_index] = (
            wait_index - (wait_displacement_index + 1)
        ) & 0xFF
        return bytes(stub)

    def _dispatch_spawn_on_main_thread(self, managed_name: int) -> None:
        with MAIN_THREAD_PATCH_LOCK:
            self._dispatch_spawn_on_main_thread_locked(managed_name)

    def _dispatch_spawn_on_main_thread_locked(self, managed_name: int) -> None:
        """Runs Unity/FishNet spawning once from the game's main update thread."""
        if (
            not self.pm
            or not self.mono
            or not self.patcher
            or not self.use_spawn_command_native
            or not self.player_late_update_native
            or not self.mono.executor.scratch_base
        ):
            raise RuntimeError("Main-thread spawn dispatcher is not prepared.")

        state_addr = self.mono.executor.scratch_base + 0x2800
        stub_addr = self.mono.executor.scratch_base + 0x3000
        stub = self._build_main_thread_stub(
            state_addr, managed_name, self.use_spawn_command_native
        )
        entry_jump = b"\x48\xB8" + struct.pack("<Q", stub_addr) + b"\xFF\xE0"
        original_prefix = self.pm.read_bytes(
            self.player_late_update_native, len(entry_jump)
        ).hex()
        self.pm.write_bytes(stub_addr, stub, len(stub))
        self.pm.write_uchar(state_addr, 1)

        started = self._wait_clock()
        self._record(
            "spawn_dispatch_armed",
            target=f"0x{self.player_late_update_native:X}",
            original_prefix=original_prefix,
            string_lifetime="game_process_pinned",
        )
        self.patcher.patch_custom(
            self.MAIN_THREAD_PATCH_ID,
            self.player_late_update_native,
            entry_jump,
        )
        restored = False
        released = False
        try:
            while True:
                state = int(self.pm.read_uchar(state_addr))
                if state == 3:
                    # The Unity thread deliberately spins inside the scratch
                    # thunk at state 3. Restore the JIT prologue while its
                    # instruction pointer is guaranteed to be elsewhere, then
                    # release it with state 4. This removes the restore race.
                    self.patcher.restore(self.MAIN_THREAD_PATCH_ID)
                    restored = True
                    self.pm.write_uchar(state_addr, 4)
                    released = True
                    self._record(
                        "spawn_dispatch_released",
                        duration_ms=round(
                            (self._wait_clock() - started) * 1000, 3
                        ),
                    )
                    return
                if state not in {1, 2}:
                    raise RuntimeError(
                        f"Invalid main-thread dispatcher state: {state}"
                    )
                if self._wait_clock() - started >= self.MAIN_THREAD_TIMEOUT_SECONDS:
                    raise TimeoutError(
                        f"Unity main-thread spawn timed out in state {state}."
                    )
                self._sleeper(0.005)
        finally:
            if not restored:
                self.patcher.restore(self.MAIN_THREAD_PATCH_ID)
            if not released:
                try:
                    if int(self.pm.read_uchar(state_addr)) == 3:
                        self.pm.write_uchar(state_addr, 4)
                except Exception:
                    pass

    def spawn_selected(self) -> bool:
        """Spawns one selected item through DazedCommands and FishNet Spawn."""
        if not self._spawn_lock.acquire(blocking=False):
            self._set_action(
                "spawner_cooldown", "A spawn request is already in progress."
            )
            self._record("spawn_rejected", reason="in_progress")
            return False
        try:
            return self._spawn_selected_locked()
        finally:
            self._spawn_lock.release()

    def _spawn_selected_locked(self) -> bool:
        """Implements one serialized spawn request."""
        item = self.selected_item
        if not item:
            self._set_action(
                "spawner_no_selection", "Select an item with F7 first."
            )
            self._record("spawn_rejected", reason="no_selection")
            return False
        if not item.is_selectable:
            self._set_action(
                "spawner_blocked",
                f"ID {item.id}: {item.display_name} is blocked for crash safety.",
                item_id=item.id,
                item_name=item.display_name,
                reason=item.safety_reason,
            )
            self._record("spawn_rejected", reason="blocked", item=item.to_dict())
            return False
        if not self.pm or not self.mono or not self.use_spawn_command_native:
            self._set_action(
                "spawner_not_attached", "Item spawner is not attached to the game."
            )
            self._record("spawn_rejected", reason="not_attached", item=item.to_dict())
            return False

        now = self._clock()
        if now - self._last_spawn_at < self.SPAWN_COOLDOWN_SECONDS:
            self._set_action(
                "spawner_cooldown", "Spawn cooldown active; please wait."
            )
            self._record("spawn_rejected", reason="cooldown", item=item.to_dict())
            return False

        try:
            if not self.is_server_authorized():
                if self.client_requester:
                    return self._request_client_spawn(item, now)
                self._set_action(
                    "spawner_not_server",
                    "Item spawning is limited to single-player or the host.",
                )
                self._record(
                    "spawn_rejected", reason="not_server", item=item.to_dict()
                )
                return False

            managed_name = self._get_pinned_spawn_string(item.spawn_key)
            started = self._clock()
            self._dispatch_spawn_on_main_thread(managed_name)
            self._last_spawn_at = now
            self.is_enabled = True
            self._set_action(
                "spawner_spawned",
                f"Spawned ID {item.id}: {item.display_name}",
                item_id=item.id,
                item_name=item.display_name,
            )
            self._record(
                "spawn_invoked",
                item=item.to_dict(),
                dispatch="Player.LateUpdate",
                duration_ms=round((self._clock() - started) * 1000, 3),
            )
            return True
        except Exception as exc:
            logger.error("Failed to spawn item ID %s: %s", item.id, exc)
            self._set_action(
                "spawner_spawn_failed",
                f"Item spawn failed: {exc}",
                error=str(exc),
            )
            self._record(
                "spawn_failed", item=item.to_dict(), error=str(exc)
            )
            return False

    def _request_client_spawn(self, item: SpawnableItem, now: float) -> bool:
        """Queues one fail-closed private-lobby ServerRpc request."""
        if not self.client_requester:
            return False
        if item.safety != SpawnSafety.SAFE or item.category not in {
            ItemCategory.ITEM,
            ItemCategory.WEAPON,
        }:
            self.client_capability = ClientCapabilityState.REJECTED
            self._set_action(
                "spawner_client_unsafe",
                "Joined-client requests only allow safe normal items and weapons.",
            )
            self._record(
                "client_spawn_rejected", reason="unsafe_item", item=item.to_dict()
            )
            return False
        if now - self._last_client_spawn_at < self.CLIENT_SPAWN_COOLDOWN_SECONDS:
            self._set_action(
                "spawner_client_cooldown",
                "Joined-client request cooldown active; please wait.",
            )
            return False
        if not self.client_requester(item.id):
            self.client_capability = ClientCapabilityState.FAILED_CLOSED
            self._set_action(
                "spawner_client_disabled",
                "Private-lobby consent is off or the previous request is unfinished.",
            )
            self._record(
                "client_spawn_rejected",
                reason="consent_or_pending",
                item=item.to_dict(),
            )
            return False
        self._last_client_spawn_at = now
        self._client_request_pending = True
        self.client_capability = ClientCapabilityState.PROBE_REQUIRED
        self.is_enabled = True
        self._set_action(
            "spawner_client_pending",
            f"Requested ID {item.id}: {item.display_name}; waiting for server sync.",
            item_id=item.id,
            item_name=item.display_name,
        )
        return True

    def update(self) -> None:
        if not self._client_request_pending or not self.client_state_reader:
            return
        state = int(self.client_state_reader())
        if state in {1, 2}:
            return
        self._client_request_pending = False
        item = self.selected_item
        if state == 3:
            self.client_capability = ClientCapabilityState.AVAILABLE
            self._set_action(
                "spawner_client_received",
                "Server synchronized the requested item into your hand.",
                item_id=item.id if item else -1,
                item_name=item.display_name if item else "",
            )
            self._record(
                "client_spawn_result",
                state=state,
                capability=self.client_capability.value,
                item=item.to_dict() if item else None,
            )
        elif state < 0:
            self.client_capability = ClientCapabilityState.FAILED_CLOSED
            self._set_action(
                "spawner_client_failed",
                "The server did not synchronize the item; client spawning is disabled for this attempt.",
                code=state,
            )
            self._record(
                "client_spawn_result",
                state=state,
                capability=self.client_capability.value,
                item=item.to_dict() if item else None,
            )
        if self.client_state_resetter:
            self.client_state_resetter()

    def enable(self) -> bool:
        return self.spawn_selected()

    def disable(self) -> bool:
        self.is_enabled = False
        self._client_request_pending = False
        return True

    def toggle(self) -> bool:
        return self.spawn_selected()

    def get_status_badge(self, language: str = "en") -> str:
        if self._client_request_pending:
            return (
                "[bold yellow]等待服务器同步[/bold yellow]"
                if language == "zh"
                else "[bold yellow]WAITING FOR SERVER[/bold yellow]"
            )
        if self.client_capability == ClientCapabilityState.AVAILABLE:
            return (
                "[bold green]客户端请求可用[/bold green]"
                if language == "zh"
                else "[bold green]CLIENT REQUEST OK[/bold green]"
            )
        if self.client_capability == ClientCapabilityState.FAILED_CLOSED:
            return (
                "[bold red]客户端请求已关闭[/bold red]"
                if language == "zh"
                else "[bold red]CLIENT FAILED CLOSED[/bold red]"
            )
        if self.selected_item:
            item = self.selected_item
            return f"[bold cyan]ID {item.id}: {item.display_name}[/bold cyan]"
        if language == "zh":
            return "[bold cyan]F7 选择 / F8 生成[/bold cyan]"
        return "[bold cyan]F7 SELECT / F8 SPAWN[/bold cyan]"
