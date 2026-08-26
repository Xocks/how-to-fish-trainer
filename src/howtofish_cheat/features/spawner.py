"""Server-authoritative item spawning through the game's native command path."""

from __future__ import annotations

import logging
import time
from dataclasses import asdict, dataclass
from enum import IntEnum
from typing import Callable, Dict, List, Optional

from .base import CheatFeature
from ..i18n import tr

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

    def to_dict(self) -> dict:
        data = asdict(self)
        data["category"] = self.category.name.lower()
        return data


class ItemSpawnerCheat(CheatFeature):
    """Enumerates and spawns native Item prefabs for a local server/host."""

    SELECT_HOTKEY = "F7"
    SPAWN_COOLDOWN_SECONDS = 0.5

    def __init__(
        self,
        pm: Optional[object] = None,
        mono: Optional[object] = None,
        patcher: Optional[object] = None,
        hotkey: str = "F8",
        event_sink: Optional[Callable[[str, dict], None]] = None,
        clock: Callable[[], float] = time.monotonic,
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
        self._last_spawn_at = float("-inf")

        self.get_spawnable_native: Optional[int] = None
        self.get_display_name_native: Optional[int] = None
        self.get_object_name_native: Optional[int] = None
        self.get_type_native: Optional[int] = None
        self.get_is_quest_item_native: Optional[int] = None
        self.use_spawn_command_native: Optional[int] = None
        self.get_server_instance_native: Optional[int] = None
        self.get_is_server_initialized_native: Optional[int] = None

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
            self.use_spawn_command_native = self._compile(
                commands_cls, "UseSpawnCommand", 2
            )
            self.get_server_instance_native = self._compile(
                server_cls, "get_Instance", 0
            )
            self.get_is_server_initialized_native = self._compile(
                network_behaviour_cls, "get_IsServerInitialized", 0
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
                    category = ItemCategory(raw_category)
                except ValueError:
                    category = ItemCategory.UNKNOWN

                is_quest_item = bool(
                    self.mono.executor.call(
                        self.get_is_quest_item_native, prefab_ptr
                    )
                )
                discovered.append(
                    SpawnableItem(
                        id=item_id,
                        display_name=display_name or object_name,
                        spawn_key=spawn_key,
                        category=category,
                        is_quest_item=is_quest_item,
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
            items=[item.to_dict() for item in self.catalog],
        )
        return list(self.catalog)

    def select_item(self, item_id: int) -> Optional[SpawnableItem]:
        item = self.catalog_by_id.get(item_id)
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

    def spawn_selected(self) -> bool:
        """Spawns one selected item through DazedCommands and FishNet Spawn."""
        item = self.selected_item
        if not item:
            self._set_action(
                "spawner_no_selection", "Select an item with F7 first."
            )
            self._record("spawn_rejected", reason="no_selection")
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
                self._set_action(
                    "spawner_not_server",
                    "Item spawning is limited to single-player or the host.",
                )
                self._record(
                    "spawn_rejected", reason="not_server", item=item.to_dict()
                )
                return False

            managed_name = self.mono.create_string(item.spawn_key)
            started = self._clock()
            self.mono.executor.call(
                self.use_spawn_command_native, managed_name, 0
            )
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

    def enable(self) -> bool:
        return self.spawn_selected()

    def disable(self) -> bool:
        self.is_enabled = False
        return True

    def toggle(self) -> bool:
        return self.spawn_selected()

    def get_status_badge(self, language: str = "en") -> str:
        if self.selected_item:
            item = self.selected_item
            return f"[bold cyan]ID {item.id}: {item.display_name}[/bold cyan]"
        if language == "zh":
            return "[bold cyan]F7 选择 / F8 生成[/bold cyan]"
        return "[bold cyan]F7 SELECT / F8 SPAWN[/bold cyan]"
