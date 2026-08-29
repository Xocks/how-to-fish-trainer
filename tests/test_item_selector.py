"""Tests for the non-blocking F7 item selector state and rendering."""

from rich.console import Group
from rich.panel import Panel
from rich.table import Table

from howtofish_cheat.features.spawner import (
    ItemCategory,
    SpawnableItem,
)
from howtofish_cheat.models import SpawnSafety
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


def test_selector_accepts_four_digit_managed_catalog_ids():
    item = SpawnableItem(1086, "Hidden Rod", "hiddenrod", ItemCategory.FISHING)
    state = ItemSelectorState()

    result = _type_id(state, 1086, [item])

    assert result.action == SelectorAction.SELECTED
    assert result.item == item


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


def test_selector_refuses_blocked_network_actor_without_confirmation():
    blocked = SpawnableItem(
        53,
        "角色",
        "deadplayer",
        ItemCategory.ITEM,
        False,
        SpawnSafety.BLOCKED,
        "network_actor_requires_player_state",
    )
    state = ItemSelectorState()
    result = _type_id(state, 53, [blocked])
    assert result.action == SelectorAction.CONTINUE
    assert state.pending_confirmation is None
    assert state.message_key == "selector_blocked"


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


def test_selector_resize_preserves_the_previous_first_visible_item():
    state = ItemSelectorState(page_size=20)
    state.page = 3

    state.resize_page(60, item_count=85)

    assert state.page == 1
    assert state.page_size == 60
    assert state.page * state.page_size <= 60


def test_selector_resize_rejects_invalid_page_size():
    state = ItemSelectorState()

    try:
        state.resize_page(0, item_count=85)
    except ValueError as exc:
        assert str(exc) == "page_size must be greater than zero"
    else:
        raise AssertionError("resize_page should reject a zero page size")


def test_selector_renderer_shows_four_id_item_pairs_per_row():
    items = [
        SpawnableItem(item_id, f"物品 {item_id}", f"item-{item_id}", ItemCategory.ITEM)
        for item_id in range(1, 10)
    ]
    state = ItemSelectorState(page_size=20)
    panel = TrainerUI().generate_item_selector(items, state, language="zh")

    assert isinstance(panel, Panel)
    assert isinstance(panel.renderable, Group)
    table = next(
        renderable
        for renderable in panel.renderable.renderables
        if isinstance(renderable, Table)
    )
    assert len(table.columns) == 8
    assert [column.header for column in table.columns] == [
        "ID",
        "物品",
        "ID",
        "物品",
        "ID",
        "物品",
        "ID",
        "物品",
    ]
    assert len(table.rows) == 3
    assert all(column.no_wrap for column in table.columns[1::2])
    assert all(column.overflow == "ellipsis" for column in table.columns[1::2])
    assert table.columns[0]._cells == ["1", "5", "9"]
    assert [cell.plain for cell in table.columns[1]._cells] == [
        "物品 1",
        "物品 5",
        "物品 9",
    ]
    assert table.columns[6]._cells == ["4", "8", ""]


def test_selector_renderer_marks_risky_item_in_compact_name_cell():
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
    assert table.columns[0]._cells == ["42"]
    assert table.columns[1]._cells[0].plain == "Rifle !"
    assert table.columns[2]._cells == [""]


def test_selector_renderer_adapts_to_two_item_pairs():
    items = _catalog()
    state = ItemSelectorState(page_size=3)
    panel = TrainerUI().generate_item_selector(
        items, state, language="zh", column_count=2
    )

    table = next(
        renderable
        for renderable in panel.renderable.renderables
        if isinstance(renderable, Table)
    )
    assert len(table.columns) == 4
    assert len(table.rows) == 2
    assert table.columns[0]._cells == ["1", "42"]
    assert table.columns[2]._cells == ["2", ""]
