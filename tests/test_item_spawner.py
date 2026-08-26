"""Unit tests for native item catalog discovery and spawning guards."""

from unittest.mock import MagicMock, patch

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
    mono.find_class.side_effect = range(0x1000, 0x1006)
    mono.find_method.return_value = 0x2000
    mono.find_method_by_signature.return_value = 0x2100
    mono.compile_method.side_effect = lambda method: method + 0x100
    cheat = ItemSpawnerCheat(pm=MagicMock(), mono=mono, patcher=MagicMock())

    assert cheat.prepare() is True
    mono.find_method_by_signature.assert_called_once_with(
        0x1000, "GetSpawnable", (0x05,)
    )
    assert cheat.get_spawnable_native == 0x2200


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

    def call(func, *args):
        if func == 100:
            return 0xCAFE
        if func == 101:
            return 1
        if func == 99:
            return 0
        raise AssertionError(func)

    cheat.mono.executor.call.side_effect = call
    assert cheat.spawn_selected() is True
    cheat.mono.create_string.assert_called_once_with("basicrifle")
    cheat.mono.executor.call.assert_any_call(99, 0x1234, 0)

    assert cheat.spawn_selected() is False
    assert "cooldown" in cheat.last_action_message.lower()


@patch("howtofish_cheat.trainer.keyboard")
def test_trainer_registers_f7_selector_and_f8_spawn(mock_keyboard):
    trainer = HowToFishTrainer(diagnostics=MagicMock())
    trainer.features = [
        ItemSpawnerCheat(pm=MagicMock(), mono=MagicMock(), patcher=MagicMock())
    ]

    trainer._setup_feature_hotkeys()

    registered = [call.args[0] for call in mock_keyboard.add_hotkey.call_args_list]
    assert registered[-2:] == ["F7", "F8"]
