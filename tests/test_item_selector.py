"""Tests for the non-blocking F7 item selector state and rendering."""

from rich.console import Group
from rich.panel import Panel
from rich.table import Table

from howtofish_cheat.features.spawner import (
    ItemCategory,
    SpawnableItem,
)
from howtofish_cheat.ui.console import TrainerUI
from howtofish_cheat.ui.selector import (
    ItemSelectorState,
    SelectorAction,
)


def _catalog():
    return [
        SpawnableItem(1, "普通箱子", "crate", ItemCategory.ITEM),
        SpawnableItem(2, "鲨鱼", "shark", ItemCategory.FISH),
        SpawnableItem(42, "Rifle", "rifle", ItemCategory.WEAPON, True),
    ]


def _type_id(state: ItemSelectorState, value: int, items):
    by_id = {item.id: item for item in items}
    for char in str(value):
        state.handle_key(char, by_id)
    return state.handle_key("ENTER", by_id)


def test_selector_selects_normal_item_and_rejects_invalid_id():
    items = _catalog()
    state = ItemSelectorState(page_size=2)
    result = _type_id(state, 2, items)
    assert result.action == SelectorAction.SELECTED
    assert result.item == items[1]

    state = ItemSelectorState(page_size=2)
    result = _type_id(state, 99, items)
    assert result.action == SelectorAction.CONTINUE
    assert state.message_key == "selector_invalid_id"
    assert state.message_kwargs == {"item_id": 99}


def test_selector_requires_second_confirmation_for_quest_item():
    items = _catalog()
    by_id = {item.id: item for item in items}
    state = ItemSelectorState()

    result = _type_id(state, 42, items)
    assert result.action == SelectorAction.CONTINUE
    assert state.pending_confirmation == items[2]

    result = state.handle_key("N", by_id)
    assert result.action == SelectorAction.CONTINUE
    assert state.pending_confirmation is None
    assert state.message_key == "selector_special_cancelled"

    state = ItemSelectorState()
    _type_id(state, 42, items)
    result = state.handle_key("Y", by_id)
    assert result.action == SelectorAction.SELECTED
    assert result.item == items[2]


def test_selector_paging_and_escape():
    items = _catalog()
    by_id = {item.id: item for item in items}
    state = ItemSelectorState(page_size=2)

    state.handle_key("PAGEDOWN", by_id)
    assert state.page == 1
    state.handle_key("PAGEDOWN", by_id)
    assert state.page == 1
    state.handle_key("PAGEUP", by_id)
    assert state.page == 0
    assert state.handle_key("ESC", by_id).action == SelectorAction.CANCELLED


def test_selector_renderer_shows_one_page_and_risk_badge():
    items = _catalog()
    state = ItemSelectorState(page_size=2)
    state.page = 1
    panel = TrainerUI().generate_item_selector(items, state, language="zh")

    assert isinstance(panel, Panel)
    assert isinstance(panel.renderable, Group)
    table = next(
        renderable
        for renderable in panel.renderable.renderables
        if isinstance(renderable, Table)
    )
    assert len(table.rows) == 1
