"""Static contracts for the Unity-main-thread helper.

These checks do not claim live game success. They prevent release builds from
silently dropping the safety and input rules that cannot run inside pytest.
"""

from pathlib import Path


SOURCE = (
    Path(__file__).parents[1]
    / "runtime"
    / "HowToFishTrainer.Runtime"
    / "TrainerRuntime.cs"
)


def _source() -> str:
    return SOURCE.read_text(encoding="utf-8")


def test_aim_contract_is_360_distance_first_and_recoil_aware():
    source = _source()
    assert "TargetRefreshInterval = 0.05f" in source
    assert "Vector3.Angle" not in source
    assert "distance < _lockedDistance * 0.9f" in source
    assert "CameraRecoilCurField" in source
    assert "ResetSwayRecoilPosRotVel" in source
    assert "FirePoint" in source


def test_esp_and_mouse_contracts_match_the_game_frame_and_restore_input():
    source = _source()
    assert "ProjectionInterval = 1f / 60f" in source
    assert '"PlayerLook", "PlayerLeftClick", "PlayerRightClick"' in source
    assert "_blockedActionStates" in source
    assert "RestoreInputCapture" in source
    assert "font = Mathf.RoundToInt" in source


def test_catalog_contract_separates_safe_fish_from_high_risk_engine_objects():
    source = _source()
    assert "SpawnCatalogSource { Game, Named, Resource, Engine }" in source
    assert "RuntimeSpawnSafety { Safe, Confirm, HighRiskLocal, Blocked }" in source
    assert "else if (item is Creature || item.Fish != null)" in source
    assert "else if (item.IsQuestItem)" in source
    assert "MaxRawClones = 20" in source
    assert "DestroyRawClones();" in source

