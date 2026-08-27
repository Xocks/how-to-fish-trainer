"""Unit tests for native item catalog discovery and spawning guards."""

import struct
from unittest.mock import MagicMock, patch

import pytest

from howtofish_cheat.features.spawner import (
    ItemCategory,
    ItemSpawnerCheat,
    SpawnableItem,
)
from howtofish_cheat.trainer import HowToFishTrainer


def _catalog_cheat():
    mono = MagicMock()
    mono.executor = MagicMock()
    cheat = ItemSpawnerCheat(pm=MagicMock(), mono=mono, patcher=MagicMock())
    cheat.get_spawnable_native = 1
    cheat.get_display_name_native = 2
    cheat.get_object_name_native = 3
    cheat.get_type_native = 4
    cheat.get_is_quest_item_native = 5

    string_values = {
        0x1010: "鳕鱼",
        0x2010: "Cod Fish",
        0x1020: "Rifle",
        0x2020: "Basic Rifle",
    }
    mono.read_string.side_effect = string_values.__getitem__

    def call(func, *args):
        if func == 1:
            return {10: 0xA000, 20: 0xB000}.get(args[0], 0)
        if func == 2:
            return {0xA000: 0x1010, 0xB000: 0x1020}[args[0]]
        if func == 3:
            return {0xA000: 0x2010, 0xB000: 0x2020}[args[0]]
        if func == 4:
            return {0xA000: 1, 0xB000: 2}[args[0]]
        if func == 5:
            return int(args[0] == 0xB000)
        raise AssertionError((func, args))

    mono.executor.call.side_effect = call
    return cheat


def test_catalog_scan_reads_names_categories_and_quest_flags():
    cheat = _catalog_cheat()
    catalog = cheat.load_catalog()

    assert catalog == [
        SpawnableItem(10, "鳕鱼", "codfish", ItemCategory.FISH, False),
        SpawnableItem(20, "Rifle", "basicrifle", ItemCategory.WEAPON, True),
    ]
    assert cheat.select_item(20) == catalog[1]
    assert cheat.select_item(99) is None


def test_prepare_resolves_the_byte_get_spawnable_overload():
    mono = MagicMock()
    mono.MONO_TYPE_U1 = 0x05
    mono.find_class.side_effect = range(0x1000, 0x1007)
    mono.find_method.return_value = 0x2000
    mono.find_method_by_signature.return_value = 0x2100
    mono.compile_method.side_effect = lambda method: method + 0x100
    cheat = ItemSpawnerCheat(pm=MagicMock(), mono=mono, patcher=MagicMock())

    assert cheat.prepare() is True
    mono.find_method_by_signature.assert_called_once_with(
        0x1000, "GetSpawnable", (0x05,)
    )
    assert cheat.get_spawnable_native == 0x2200


def test_prefab_catalog_falls_back_to_build_categories():
    assert ItemSpawnerCheat._classify_item(
        20, "cod", ItemCategory.ITEM
    ) == ItemCategory.FISH
    assert ItemSpawnerCheat._classify_item(
        54, "assaultrifle", ItemCategory.ITEM
    ) == ItemCategory.WEAPON
    assert ItemSpawnerCheat._classify_item(
        56, "beer", ItemCategory.ITEM
    ) == ItemCategory.ITEM


def test_main_thread_dispatch_patches_one_late_update_and_restores():
    pm = MagicMock()
    pm.read_uchar.return_value = 3
    mono = MagicMock()
    mono.executor.scratch_base = 0x100000
    patcher = MagicMock()
    cheat = ItemSpawnerCheat(pm=pm, mono=mono, patcher=patcher)
    cheat.use_spawn_command_native = 0x200000
    cheat.player_late_update_native = 0x300000

    cheat._dispatch_spawn_on_main_thread(0x400000)

    state_addr = 0x102800
    stub_addr = 0x103000
    written_stub = pm.write_bytes.call_args.args[1]
    assert struct.pack("<Q", state_addr) in written_stub
    assert struct.pack("<Q", 0x400000) in written_stub
    assert struct.pack("<Q", 0x200000) in written_stub
    assert b"\x80\x38\x04" in written_stub
    assert pm.write_uchar.call_args_list == [
        ((state_addr, 1),),
        ((state_addr, 4),),
    ]
    patcher.patch_custom.assert_called_once_with(
        cheat.MAIN_THREAD_PATCH_ID,
        0x300000,
        b"\x48\xB8" + struct.pack("<Q", stub_addr) + b"\xFF\xE0",
    )
    patcher.restore.assert_called_once_with(cheat.MAIN_THREAD_PATCH_ID)


def test_main_thread_dispatch_restores_patch_on_timeout():
    times = iter([0.0, 5.0])
    pm = MagicMock()
    pm.read_uchar.return_value = 1
    mono = MagicMock()
    mono.executor.scratch_base = 0x100000
    patcher = MagicMock()
    cheat = ItemSpawnerCheat(
        pm=pm,
        mono=mono,
        patcher=patcher,
        wait_clock=lambda: next(times),
        sleeper=lambda _: None,
    )
    cheat.use_spawn_command_native = 0x200000
    cheat.player_late_update_native = 0x300000

    with pytest.raises(TimeoutError, match="state 1"):
        cheat._dispatch_spawn_on_main_thread(0x400000)

    patcher.restore.assert_called_once_with(cheat.MAIN_THREAD_PATCH_ID)


def test_spawn_requires_selection_attachment_and_server_authority():
    cheat = _catalog_cheat()
    assert cheat.spawn_selected() is False

    cheat.catalog = [
        SpawnableItem(20, "Rifle", "basicrifle", ItemCategory.WEAPON)
    ]
    cheat.select_item(20)
    cheat.use_spawn_command_native = 99
    cheat.get_server_instance_native = 100
    cheat.get_is_server_initialized_native = 101

    cheat.mono.executor.call.side_effect = lambda func, *args: {
        100: 0xCAFE,
        101: 0,
    }[func]
    assert cheat.spawn_selected() is False
    assert "single-player" in cheat.last_action_message


def test_spawn_invokes_native_command_once_and_enforces_cooldown():
    times = iter([10.0, 10.1, 10.2, 10.3])
    cheat = ItemSpawnerCheat(
        pm=MagicMock(),
        mono=MagicMock(),
        patcher=MagicMock(),
        clock=lambda: next(times),
    )
    cheat.mono.executor = MagicMock()
    cheat.catalog = [
        SpawnableItem(20, "Rifle", "basicrifle", ItemCategory.WEAPON)
    ]
    cheat.select_item(20)
    cheat.use_spawn_command_native = 99
    cheat.get_server_instance_native = 100
    cheat.get_is_server_initialized_native = 101
    cheat.mono.create_string.return_value = 0x1234
    cheat.mono.pin_object.return_value = 0x5678

    def call(func, *args):
        if func == 100:
            return 0xCAFE
        if func == 101:
            return 1
        raise AssertionError(func)

    cheat.mono.executor.call.side_effect = call
    with patch.object(cheat, "_dispatch_spawn_on_main_thread") as dispatch:
        assert cheat.spawn_selected() is True
    dispatch.assert_called_once_with(0x1234)
    cheat.mono.create_string.assert_called_once_with("basicrifle")
    cheat.mono.pin_object.assert_called_once_with(0x1234)
    cheat.mono.free_gchandle.assert_not_called()

    assert cheat.spawn_selected() is False
    assert "cooldown" in cheat.last_action_message.lower()


def test_spawn_key_string_is_pinned_once_and_never_freed_at_runtime():
    cheat = ItemSpawnerCheat(pm=MagicMock(), mono=MagicMock(), patcher=MagicMock())
    cheat.mono.create_string.return_value = 0x1234
    cheat.mono.pin_object.return_value = 0x5678

    assert cheat._get_pinned_spawn_string("knife") == 0x1234
    assert cheat._get_pinned_spawn_string("knife") == 0x1234

    cheat.mono.create_string.assert_called_once_with("knife")
    cheat.mono.pin_object.assert_called_once_with(0x1234)
    cheat.mono.free_gchandle.assert_not_called()
    assert cheat._pinned_spawn_strings == {"knife": (0x1234, 0x5678)}


@patch("howtofish_cheat.trainer.keyboard")
def test_trainer_registers_f7_selector_and_f8_spawn(mock_keyboard):
    trainer = HowToFishTrainer(diagnostics=MagicMock())
    trainer.features = [
        ItemSpawnerCheat(pm=MagicMock(), mono=MagicMock(), patcher=MagicMock())
    ]

    trainer._setup_feature_hotkeys()

    registered = [call.args[0] for call in mock_keyboard.add_hotkey.call_args_list]
    assert registered[-2:] == ["F7", "F8"]
