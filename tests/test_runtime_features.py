"""Unit coverage for runtime aim, ESP, main-thread dispatch, and models."""

import struct
from unittest.mock import MagicMock, call, patch

from howtofish_cheat.features.runtime import (
    AimAssistCheat,
    EspOverlayCheat,
    ManagedRuntimeController,
    MousePanelFeature,
    SilentAimFeature,
    ThirdPersonFeature,
)
from howtofish_cheat.models import (
    AimMotionSample,
    AimSettings,
    AimTargetKind,
    AimTargetFlags,
    AimTargetSpecies,
    AimTrackingMode,
    EspSettings,
    ClientCapabilityState,
    PoseExperimentSettings,
    PoseMode,
    ProjectileTrackingState,
    SilentAimMode,
    ThirdPersonBackend,
    ThirdPersonAvatarBackend,
    AvatarMirrorState,
    ThirdPersonSettings,
)
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
    assert aim.tracking_mode == AimTrackingMode.STABLE_FIRST
    assert aim.max_yaw_speed == 240
    assert aim.max_pitch_speed == 90
    assert aim.continuous_pitch_speed == 120
    assert aim.unstable_grace_seconds == 0.2
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
    helper = tmp_path / "HowToFishTrainer.Runtime.V030.dll"
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
        str(helper), "HowToFishTrainer.Runtime.V030"
    )
    assert "Initialize" in controller.methods
    assert "RequestClientItem" in controller.methods
    assert "RequestSelectedSpawn" in controller.methods
    assert "SetSelectedSpawnId" in controller.methods
    assert "SetSelectedCatalogIndex" in controller.methods
    assert "GetCatalogEntry" in controller.methods
    assert "SetAimTrackingMode" in controller.methods
    assert "SetAimTargetMask" in controller.methods
    assert "GetAimTargetSpecies" in controller.methods
    assert "GetBirdFlyingCandidateCount" in controller.methods
    assert "GetLastSpawnRendererCount" in controller.methods
    assert "SetThirdPersonEnabled" in controller.methods
    assert "GetThirdPersonState" in controller.methods
    assert "GetThirdPersonBackend" in controller.methods
    assert "GetThirdPersonRenderCount" in controller.methods
    assert "GetThirdPersonCollisionDistanceMm" in controller.methods
    assert "GetThirdPersonAppliedDistanceMm" in controller.methods
    assert "GetThirdPersonHeadOffsetMm" in controller.methods
    assert "GetThirdPersonBodyRendererCount" in controller.methods
    assert "GetThirdPersonBodyVisibleCount" in controller.methods
    assert "GetThirdPersonAvatarBackend" in controller.methods
    assert "GetAvatarMirrorState" in controller.methods
    assert "GetAvatarBoneCount" in controller.methods
    assert "GetAvatarTemplateCandidateCount" in controller.methods
    assert "GetAvatarAppearanceApplyState" in controller.methods
    assert "GetAvatarIkCount" in controller.methods
    assert "GetAvatarAnimationState" in controller.methods
    assert "GetAvatarNativeStage" in controller.methods
    assert "GetAvatarNativeFailureCount" in controller.methods
    assert "SetPoseMode" in controller.methods
    assert "SetPoseSpinSpeed" in controller.methods
    assert "SetPoseLookDown" in controller.methods
    assert "SetSilentAimEnabled" in controller.methods
    assert "GetTrackedProjectileCount" in controller.methods


def test_runtime_int_reads_are_signed_and_motion_samples_serialize():
    mono = MagicMock()
    mono.executor.call.return_value = (1 << 64) - 11
    controller = ManagedRuntimeController(MagicMock(), mono, MagicMock())
    controller.initialized = True
    controller.methods = {"state": 1}

    assert controller.get_int("state") == -11
    sample = AimMotionSample(7, 1, 2, 3, 20, 5, True, 1.5)
    assert sample.to_dict()["stable"] is True


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
    third_person = ThirdPersonFeature(controller)
    silent = SilentAimFeature(controller)

    assert [aim.hotkey, esp.hotkey, panel.hotkey, third_person.hotkey, silent.hotkey] == [
        "F9", "F11", "Insert", "Home", "End"
    ]
    assert aim.enable() is True
    assert "PLAYER" in aim.get_status_badge("en")

    third_person.is_enabled = True
    controller.get_int.side_effect = lambda method: {
        "GetThirdPersonState": 1,
        "GetThirdPersonBackend": 1,
        "GetThirdPersonRenderCount": 12,
        "GetThirdPersonAppliedDistanceMm": 3500,
    }.get(method, 0)
    assert "RENDER CALLBACK ACTIVE" in third_person.get_status_badge("en")
    controller.get_int.side_effect = lambda method: {
        "GetThirdPersonState": -10,
        "GetThirdPersonBackend": 1,
        "GetThirdPersonRenderCount": 12,
        "GetThirdPersonAppliedDistanceMm": 403342,
    }.get(method, 0)
    assert "INVALID CAMERA COORDINATES BLOCKED" in third_person.get_status_badge("en")


def test_third_person_pose_and_projectile_models_fail_closed():
    third = ThirdPersonSettings(99, -99, 99, True, 9).normalized()
    assert third.distance == 8
    assert third.height == -0.5
    assert third.shoulder_offset == 1.5
    assert third.collision_radius == 0.5
    assert ThirdPersonBackend.RENDER_CALLBACK == 1
    assert ThirdPersonBackend.NATIVE_OBSERVER_CAMERA == 2
    assert ThirdPersonAvatarBackend.MIRRORED_NETWORK_PRESENTATION == 1
    assert ThirdPersonAvatarBackend.LOADED_PLAYER_TEMPLATE == 2
    assert ThirdPersonAvatarBackend.LOCAL_BODY_FALLBACK == 3
    assert AvatarMirrorState.ACTIVE == 2
    assert PoseMode.HIDE_HEAD_BACKWARDS != PoseMode.HIGH_SPEED_SPIN
    assert AimTargetFlags.FISH | AimTargetFlags.BIRD == 3
    assert AimTargetFlags.PLAYER not in (AimTargetFlags.FISH | AimTargetFlags.BIRD)
    assert AimTargetSpecies.PLAYER == 4

    pose = PoseExperimentSettings(enabled=True, spin_speed=9999).normalized()
    assert pose.enabled is False
    assert pose.spin_speed == 1440

    state = ProjectileTrackingState(
        projectile_id=9,
        target_instance_id=10,
        speed=20,
        server_acceptance=ClientCapabilityState.PROBE_REQUIRED,
    )
    assert SilentAimMode.PROJECTILE_TRACKING.value == "projectile_tracking"
    assert state.to_dict()["server_acceptance"] == "probe_required"


def test_runtime_controller_clamps_target_and_pose_controls():
    mono = MagicMock()
    controller = ManagedRuntimeController(MagicMock(), mono, MagicMock())
    controller.initialized = True
    controller.methods = {
        "SetAimTargetMask": 1,
        "SetPoseMode": 2,
        "SetPoseSpinSpeed": 3,
        "SetPoseLookDown": 4,
    }

    assert controller.set_aim_target_mask(0xFF) is True
    assert controller.set_pose_mode(PoseMode.HIGH_SPEED_SPIN) is True
    assert controller.set_pose_spin_speed(9000) is True
    assert controller.set_pose_look_down(True) is True
    assert mono.executor.call.call_args_list == [
        call(1, 0x0F),
        call(2, int(PoseMode.HIGH_SPEED_SPIN)),
        call(3, 1440),
        call(4, True),
    ]


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
        0x1001: "1\t-1\tEngine Crate\tEngine Crate\t3\t6\t2\tlocal only\t1\t4",
    }.__getitem__

    entries = controller.get_catalog_entries(timeout=0)

    assert entries[0]["native_id"] == 54
    assert entries[1]["source"] == 3
    assert entries[1]["safety_reason"] == "local only"
    assert entries[1]["engine_capability"] == 1
    assert entries[1]["renderer_count"] == 4
