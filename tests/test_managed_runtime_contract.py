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
    assert "AimTrackingMode { StableFirst, Continuous }" in source
    assert "AimUnstableGrace = 0.2f" in source
    assert "AimMaxAngularSpeed = 240f" in source
    assert "Vector3.MoveTowards" in source
    assert "_maxYawSpeed = 240f" in source
    assert "_maxPitchSpeed = 90f" in source
    assert "distance < _lockedDistance * 0.9f" in source
    assert "CameraRecoilCurField" in source
    recoil_body = source.split("private void ApplyRecoilCompensation", 1)[1].split(
        "internal void ApplyPreWeaponDirection", 1
    )[0]
    assert "ResetToolRecoilMethod" not in recoil_body
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
    assert "BuildCatalogExport();" in source
    assert "SetSelectedCatalogIndex" in source
    assert "EngineObjectCapability { NotEngine, VisualPreview, DiagnosticOnly }" in source
    assert "CopyPreviewHierarchy" in source
    assert "UnityEngine.Object.Instantiate(entry.Prefab" not in source
    assert "rendererCount == 0 ? -14 : -15" in source
    assert "SpawnRequestSequence++" in source


def test_third_person_contract_has_collision_and_all_restore_paths():
    source = _source()
    third_person = source.split("private void UpdateThirdPersonCamera", 1)[1].split(
        "private void UpdateTrackedProjectiles", 1
    )[0]
    assert "ThirdPersonBackend { None, RenderCallback, NativeObserverCamera }" in source
    assert "RenderPipelineManager.beginCameraRendering" in third_person
    assert "Camera.onPreCull" in third_person
    assert "Physics.SphereCastNonAlloc" in third_person
    assert "ResolveThirdPersonPivot" in third_person
    assert "pivot = source.transform.position" in third_person
    assert "pivot = local.Body.Head.position" not in third_person
    assert "ThirdPersonHeadOffsetMm" in third_person
    assert "sourceDisplacement <= Mathf.Min(12f, requestedDistance + 1f)" in third_person
    assert "actualDisplacement > 12f" in third_person
    assert "local.Camera.CamTransform" not in third_person
    assert "local.Body == null || local.Body.Head == null" not in third_person
    assert "DeathCameraField.GetValue" in third_person
    assert "local.SetCurCam(observer)" in third_person
    assert "EnableDeathCam(" not in third_person
    assert "RestoreThirdPerson();" in source
    assert "RestoreRenderOverride();" in source
    assert "_savedSourceCullingMask" in source
    assert "_savedObserverCullingMask" in source
    assert "_localBodyRendererStates" in source
    assert "_localBodyForceRenderingStates" in source
    assert "forceRenderingOff = false" in third_person
    assert "MaintainLocalBodyVisibility();" in third_person
    assert "_localArmRendererStates" in source
    assert "Home 第三人称" in source
    assert "ThirdPersonState = 1" in source
    assert "ThirdPersonState = 2" in source
    assert "Bootstrap.SetThirdPersonEnabled(false)" in source
    assert "ThirdPersonAvatarBackend { None, MirroredNetworkPresentation, LoadedPlayerTemplate, LocalBodyFallback }" in source
    assert "Resources.FindObjectsOfTypeAll<PlayerBody>()" in third_person
    assert "!body.gameObject.scene.IsValid()" in third_person
    assert "CountRenderableAvatarMeshes" in third_person
    assert "ApplyLocalAvatarAppearance(local);" in third_person
    assert "SkinInitializeOtherMethod.Invoke(localSkin, null)" in third_person
    assert "mirrorObject.layer = 0" in third_person
    assert "BuildAvatarIkRig(sourceRoot);" in third_person
    assert "AddComponent<IK>()" in third_person
    assert "IkResolveMethod.Invoke(binding.Solver, new object[] { false })" in third_person
    assert "BindNativeAvatarControllers(local)" in third_person
    assert "LegsUpdateMethod.Invoke(_avatarNativeLegs, null)" in third_person
    assert "HandsLateUpdateMethod.Invoke(_avatarNativeHands, null)" in third_person
    assert "BodyApplyMethod.Invoke(_avatarNativeBody, null)" in third_person
    assert "_avatarModelRoot.localPosition +=" not in third_person
    assert "_avatarGaitPhase" not in third_person
    assert "RestoreNativeAvatarControllers();" in third_person
    assert "var source = _avatarMirrorRoot != null ? _avatarSourceRoot : ResolveAvatarSourceRoot(local);" in third_person
    assert "CreateAvatarTransformHierarchy" in third_person
    assert "CopyAvatarRenderer" in third_person
    assert "SkinnedMeshRenderer" in third_person
    assert "mirror.bones = mirrorBones" in third_person
    assert "mirror.sharedMaterials = sourceSkinned.sharedMaterials" in third_person
    assert "destination.AddComponent<MeshFilter>()" in third_person
    assert "AddComponent<Animator>" not in third_person
    assert "AddComponent<Collider>" not in third_person
    assert "AddComponent<Rigidbody>" not in third_person
    assert "AddComponent<PlayerBody>" not in third_person
    assert "AddComponent<PlayerHands>" not in third_person
    assert "AddComponent<PlayerLegs>" not in third_person
    assert "DestroyAvatarMirror(reason);" in third_person


def test_pose_contract_reuses_original_send_window_and_pauses_in_menu():
    source = _source()
    assert "ApplyOutboundPose" in source
    assert "RestoreOutboundPose" in source
    assert "OnPreTick += ApplyOutboundPose" in source
    assert "OnPostTick += RestoreOutboundPose" in source
    assert "OnPreTick -= ApplyOutboundPose" in source
    assert "OnPostTick -= RestoreOutboundPose" in source
    assert "PutPoseHandlerFirst" in source
    assert "if (!_poseOrderingReady) { PoseState = -5; return; }" in source
    assert "_privateLobbyConsent || _menuOpen" in source
    assert "_poseSpinSpeed = 720f" in source
    assert "PoseMode { Off, HideHeadBackwards, HighSpeedSpin }" in source
    assert "view.y + 180f" in source
    assert "var pitch = _poseLookDown ? 89f : view.x" in source
    assert "SetPoseLookDown" in source
    assert "身体方向（互斥）与低头（可组合；面板打开时自动暂停）" in source
    assert "PoseRestoreCount++" in source


def test_aim_targets_merge_birds_and_use_shared_private_player_gate():
    source = _source()
    assert "AimTargetFlags { None = 0, Fish = 1, Bird = 2, OtherCreature = 4, Player = 8 }" in source
    assert "_aimTargetMask = AimTargetFlags.Fish | AimTargetFlags.Bird" in source
    assert 'typeof(BirdManager).GetField("_flyingBirds"' in source
    assert "Resources.FindObjectsOfTypeAll<BirdManager>()" in source
    assert "_aimCandidateIds.Add(id)" in source
    assert "TryGetPlayerTargetPosition" in source
    assert "bounds.center + Vector3.up * bounds.extents.y * 0.65f" in source
    assert "targetTransform.position + Vector3.up * 1.6f" in source
    assert "distance < _lockedDistance * 0.9f" in source
    assert "TargetPriority(" not in source
    assert "SetAimTargetMask" in source
    assert "TargetSpecies = _lockedSpecies" in source


def test_silent_aim_contract_preserves_spread_and_tracks_only_local_projectiles():
    source = _source()
    assert "ApplyPreWeaponDirection" in source
    assert "RestorePreWeaponDirection" in source
    assert "projectile.Owner != local || !projectile.IsLocal" in source
    assert "_ignoredExistingProjectiles" in source
    assert "silentRequested = _silentAimEnabled" in source
    assert "!state.InitialCorrected" in source
    assert "Vector3.RotateTowards" in source
    assert "180f * Mathf.Deg2Rad" in source
    assert "Target = _lockedTarget" in source
    assert "IsObstructed(projectile.Position" in source
    assert "if (state.Occluded" in source
    assert "AddProjectile(" not in source[source.index("private void UpdateTrackedProjectiles"):source.index("private static bool TryGetBoundTargetPosition")]
