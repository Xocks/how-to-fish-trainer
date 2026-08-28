"""Unit coverage for runtime aim, ESP, main-thread dispatch, and models."""

import struct
from unittest.mock import MagicMock, patch

from howtofish_cheat.features.runtime import (
    AimAssistCheat,
    EspOverlayCheat,
    ManagedRuntimeController,
    MousePanelFeature,
)
from howtofish_cheat.models import AimSettings, AimTargetKind
from howtofish_cheat.mono.main_thread import MainThreadDispatcher


def test_aim_settings_are_clamped_and_break_angle_tracks_acquire():
    settings = AimSettings(999, 50, 2, 0, True).normalized()
    assert settings.max_distance == 300
    assert settings.acquire_angle == 45
    assert settings.break_angle == 45
    assert settings.smoothing == 1
    assert settings.allow_players is True


def test_main_thread_stub_calls_function_and_waits_for_release():
    stub = MainThreadDispatcher.build_stub(0x11223344, 0x55667788)
    assert struct.pack("<Q", 0x11223344) in stub
    assert struct.pack("<Q", 0x55667788) in stub
    assert b"\x80\x38\x04" in stub


@patch("howtofish_cheat.features.runtime.runtime_assembly_path")
def test_runtime_controller_loads_helper_and_exposes_toggles(mock_path, tmp_path):
    helper = tmp_path / "HowToFishTrainer.Runtime.dll"
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
        str(helper), "HowToFishTrainer.Runtime"
    )
    assert "Initialize" in controller.methods
    assert "RequestClientItem" in controller.methods


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
