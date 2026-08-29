"""Unit coverage for runtime aim, ESP, main-thread dispatch, and models."""

import struct
from unittest.mock import MagicMock, patch

from howtofish_cheat.features.runtime import (
    AimAssistCheat,
    EspOverlayCheat,
    ManagedRuntimeController,
    MousePanelFeature,
)
from howtofish_cheat.models import AimSettings, AimTargetKind, EspSettings
from howtofish_cheat.mono.main_thread import MainThreadDispatcher


def test_aim_settings_are_clamped_and_break_angle_tracks_acquire():
    settings = AimSettings(999, 50, 2, 0, True).normalized()
    assert settings.max_distance == 300
    assert settings.acquire_angle == 45
    assert settings.break_angle == 45
    assert settings.smoothing == 1
    assert settings.allow_players is True
    assert settings.nearest_360 is True
    assert settings.recoil_compensation == 1.0


def test_aim_and_esp_extended_settings_are_clamped():
    aim = AimSettings(
        recoil_compensation=3,
        switch_hysteresis=-1,
    ).normalized()
    esp = EspSettings(999, 999, 99, 144).normalized()
    assert aim.recoil_compensation == 1
    assert aim.switch_hysteresis == 0
    assert esp.max_distance == 500
    assert esp.max_labels == 500
    assert esp.font_size == 36
    assert esp.projection_hz == 60


def test_main_thread_stub_calls_function_and_waits_for_release():
    stub = MainThreadDispatcher.build_stub(0x11223344, 0x55667788)
    assert struct.pack("<Q", 0x11223344) in stub
    assert struct.pack("<Q", 0x55667788) in stub
    assert b"\x80\x38\x04" in stub


@patch("howtofish_cheat.features.runtime.runtime_assembly_path")
def test_runtime_controller_loads_helper_and_exposes_toggles(mock_path, tmp_path):
    helper = tmp_path / "HowToFishTrainer.Runtime.RC2Hotfix1.dll"
    helper.write_bytes(b"managed")
    mock_path.return_value = helper
    mono = MagicMock()
    mono.find_class.return_value = 0x1000
    mono.find_method.side_effect = range(0x2000, 0x2100)
    mono.compile_method.side_effect = lambda value: value + 0x1000
    mono.executor.scratch_base = 0x100000
    controller = ManagedRuntimeController(MagicMock(), mono, MagicMock())

    assert controller.prepare() is True
    mono.load_assembly.assert_called_once_with(
        str(helper), "HowToFishTrainer.Runtime.RC2Hotfix1"
    )
    assert "Initialize" in controller.methods
    assert "RequestClientItem" in controller.methods
    assert "RequestSelectedSpawn" in controller.methods
    assert "SetSelectedSpawnId" in controller.methods
    assert "SetSelectedCatalogIndex" in controller.methods
    assert "GetCatalogEntry" in controller.methods


def test_runtime_feature_hotkeys_and_status_are_stable():
    controller = MagicMock()
    controller.pm = MagicMock()
    controller.mono = MagicMock()
    controller.patcher = MagicMock()
    controller.status_word.return_value = 0x1 | (int(AimTargetKind.PLAYER) << 8)
    controller.set_bool.return_value = True

    aim = AimAssistCheat(controller)
    esp = EspOverlayCheat(controller)
    panel = MousePanelFeature(controller)

    assert [aim.hotkey, esp.hotkey, panel.hotkey] == ["F9", "F11", "Insert"]
    assert aim.enable() is True
    assert "PLAYER" in aim.get_status_badge("en")


def test_runtime_prepare_failure_is_reported_only_once():
    mono = MagicMock()
    mono.load_assembly.side_effect = RuntimeError("old helper contract")
    controller = ManagedRuntimeController(MagicMock(), mono, MagicMock())

    assert controller.prepare() is False
    assert controller.prepare() is False
    assert controller.last_error == "old helper contract"
    assert mono.load_assembly.call_count == 1


def test_runtime_catalog_export_decodes_immutable_rows():
    mono = MagicMock()
    controller = ManagedRuntimeController(MagicMock(), mono, MagicMock())
    controller.initialized = True
    controller.methods = {"GetCatalogCount": 10, "GetCatalogEntry": 11}

    def call(method, *args):
        if method == 10:
            return 2
        if method == 11:
            return 0x1000 + args[0]
        raise AssertionError((method, args))

    mono.executor.call.side_effect = call
    mono.read_string.side_effect = {
        0x1000: "0\t54\tRifle\tassaultrifle\t0\t2\t0\t",
        0x1001: "1\t-1\tEngine Crate\tEngine Crate\t3\t6\t2\tlocal only",
    }.__getitem__

    entries = controller.get_catalog_entries(timeout=0)

    assert entries[0]["native_id"] == 54
    assert entries[1]["source"] == 3
    assert entries[1]["safety_reason"] == "local only"
