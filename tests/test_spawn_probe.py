"""Tests for the controlled live spawn-probe orchestration."""

from unittest.mock import MagicMock

from howtofish_cheat.spawn_probe import run_spawn_probe


def test_spawn_probe_runs_one_attempt_and_cleans_up():
    diagnostics = MagicMock()
    pm = MagicMock()
    pm.base_address = 0x400000
    mono = MagicMock()
    patcher = MagicMock()
    item = MagicMock()
    item.to_dict.return_value = {"id": 56, "spawn_key": "beer"}
    spawner = MagicMock()
    spawner.prepare.return_value = True
    spawner.select_item.return_value = item
    spawner.spawn_selected.return_value = True
    sleeper = MagicMock()

    result = run_spawn_probe(
        56,
        diagnostics=diagnostics,
        pm_factory=MagicMock(return_value=pm),
        mono_factory=MagicMock(return_value=mono),
        patcher_factory=MagicMock(return_value=patcher),
        spawner_factory=MagicMock(return_value=spawner),
        sleeper=sleeper,
    )

    assert result == 0
    spawner.load_catalog.assert_called_once_with()
    spawner.select_item.assert_called_once_with(56)
    spawner.spawn_selected.assert_called_once_with()
    sleeper.assert_called_once_with(5.0)
    pm.read_bytes.assert_called_once_with(0x400000, 2)
    spawner.disable.assert_called_once_with()
    patcher.restore_all.assert_called_once_with()
    mono.close.assert_called_once_with()
    pm.close_process.assert_called_once_with()


def test_spawn_probe_stops_before_spawn_for_unknown_id():
    diagnostics = MagicMock()
    pm = MagicMock()
    mono = MagicMock()
    patcher = MagicMock()
    spawner = MagicMock()
    spawner.prepare.return_value = True
    spawner.select_item.return_value = None

    result = run_spawn_probe(
        255,
        diagnostics=diagnostics,
        pm_factory=MagicMock(return_value=pm),
        mono_factory=MagicMock(return_value=mono),
        patcher_factory=MagicMock(return_value=patcher),
        spawner_factory=MagicMock(return_value=spawner),
        sleeper=MagicMock(),
    )

    assert result == 2
    spawner.spawn_selected.assert_not_called()
    patcher.restore_all.assert_called_once_with()
    mono.close.assert_called_once_with()
    pm.close_process.assert_called_once_with()
