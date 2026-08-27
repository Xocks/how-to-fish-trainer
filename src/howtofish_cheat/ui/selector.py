"""Pure state machine for the keyboard-driven item selection screen."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from math import ceil
from typing import Dict, Optional

from ..features.spawner import SpawnableItem


class SelectorAction(str, Enum):
    CONTINUE = "continue"
    SELECTED = "selected"
    CANCELLED = "cancelled"


@dataclass(frozen=True)
class SelectorResult:
    action: SelectorAction
    item: Optional[SpawnableItem] = None


class ItemSelectorState:
    """Tracks pages, numeric input, validation, and risk confirmation."""

    def __init__(self, page_size: int = 20):
        if page_size <= 0:
            raise ValueError("page_size must be greater than zero")
        self.page_size = page_size
        self.page = 0
        self.input_buffer = ""
        self.message_key = ""
        self.message_kwargs = {}
        self.pending_confirmation: Optional[SpawnableItem] = None

    def total_pages(self, item_count: int) -> int:
        return max(1, ceil(item_count / self.page_size))

    def clamp_page(self, item_count: int) -> None:
        self.page = min(max(self.page, 0), self.total_pages(item_count) - 1)

    def resize_page(self, page_size: int, item_count: int) -> None:
        """Changes page capacity while keeping the previous first item visible."""
        if page_size <= 0:
            raise ValueError("page_size must be greater than zero")
        first_visible_index = self.page * self.page_size
        self.page_size = page_size
        self.page = first_visible_index // page_size
        self.clamp_page(item_count)

    def handle_key(
        self, key: str, catalog_by_id: Dict[int, SpawnableItem]
    ) -> SelectorResult:
        key = key.upper()
        item_count = len(catalog_by_id)

        if self.pending_confirmation:
            if key == "Y":
                item = self.pending_confirmation
                self.pending_confirmation = None
                return SelectorResult(SelectorAction.SELECTED, item)
            if key in {"N", "ESC"}:
                self.pending_confirmation = None
                self.message_key = "selector_special_cancelled"
                self.message_kwargs = {}
            return SelectorResult(SelectorAction.CONTINUE)

        if key == "ESC":
            return SelectorResult(SelectorAction.CANCELLED)
        if key == "PAGEUP":
            self.page -= 1
            self.clamp_page(item_count)
            return SelectorResult(SelectorAction.CONTINUE)
        if key == "PAGEDOWN":
            self.page += 1
            self.clamp_page(item_count)
            return SelectorResult(SelectorAction.CONTINUE)
        if key == "BACKSPACE":
            self.input_buffer = self.input_buffer[:-1]
            self.message_key = ""
            self.message_kwargs = {}
            return SelectorResult(SelectorAction.CONTINUE)
        if len(key) == 1 and key.isdigit():
            if len(self.input_buffer) < 3:
                self.input_buffer += key
                self.message_key = ""
                self.message_kwargs = {}
            return SelectorResult(SelectorAction.CONTINUE)
        if key != "ENTER":
            return SelectorResult(SelectorAction.CONTINUE)

        if not self.input_buffer:
            self.message_key = "selector_enter_id"
            self.message_kwargs = {}
            return SelectorResult(SelectorAction.CONTINUE)

        item_id = int(self.input_buffer)
        item = catalog_by_id.get(item_id)
        if not item:
            self.message_key = "selector_invalid_id"
            self.message_kwargs = {"item_id": item_id}
            return SelectorResult(SelectorAction.CONTINUE)

        if item.requires_confirmation:
            self.pending_confirmation = item
            self.message_key = ""
            self.message_kwargs = {}
            return SelectorResult(SelectorAction.CONTINUE)
        return SelectorResult(SelectorAction.SELECTED, item)
