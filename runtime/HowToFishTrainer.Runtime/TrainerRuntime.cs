using System;
using System.Collections;
using System.Collections.Generic;
using System.Reflection;
using UnityEngine;
using UnityEngine.InputSystem;
using UnityEngine.Rendering;
using UnityEngine.SceneManagement;

namespace HowToFishTrainer.Runtime
{
    public static class Bootstrap
    {
        private static TrainerRuntimeBehaviour _instance;
        private static TrainerPreRuntimeBehaviour _preInstance;
        private static volatile bool _aimEnabled, _espEnabled, _menuOpen, _privateLobbyConsent, _thirdPersonEnabled, _silentAimEnabled, _poseLookDown, _shutdownRequested;
        private static volatile int _aimTrackingMode, _silentAimMode = 1, _aimTargetMask = 3, _poseMode, _poseSpinSpeed = 720;
        private static volatile int _clientSpawnRequest = -1, _selectedSpawnIdRequest = -2, _selectedCatalogIndexRequest = -1;
        private static volatile bool _selectedSpawnRequested;
        private static int _lastSelectedSpawnRequestTick = int.MinValue;

        public static bool Initialize()
        {
            if (!ReferenceEquals(_instance, null)) return true;
            var host = new GameObject("HowToFishTrainer.Runtime");
            UnityEngine.Object.DontDestroyOnLoad(host);
            _instance = host.AddComponent<TrainerRuntimeBehaviour>();
            _preInstance = host.AddComponent<TrainerPreRuntimeBehaviour>();
            _preInstance.Owner = _instance;
            _instance.ApplyControlState(_aimEnabled, _espEnabled, _menuOpen, _privateLobbyConsent, _thirdPersonEnabled, _silentAimEnabled, _aimTrackingMode, _silentAimMode, _aimTargetMask, _poseMode, _poseSpinSpeed, _poseLookDown);
            return true;
        }

        public static void SetAimEnabled(bool value) { _aimEnabled = value; }
        public static void SetEspEnabled(bool value) { _espEnabled = value; }
        public static void SetMenuOpen(bool value) { _menuOpen = value; }
        public static void SetPrivateLobbyConsent(bool value) { _privateLobbyConsent = value; if (!value) { _aimTargetMask &= ~8; _poseMode = 0; _poseLookDown = false; } }
        public static void SetThirdPersonEnabled(bool value) { _thirdPersonEnabled = value; }
        public static void SetSilentAimEnabled(bool value) { _silentAimEnabled = value; }
        public static void SetSilentAimMode(int value) { _silentAimMode = value == 2 ? 2 : 1; }
        public static void SetAimTrackingMode(int value) { _aimTrackingMode = value == 1 ? 1 : 0; }
        public static void SetAimTargetMask(int value) { _aimTargetMask = value & 0x0F; }
        public static void SetPoseMode(int value) { _poseMode = value >= 0 && value <= 2 ? value : 0; }
        public static void SetPoseSpinSpeed(int value) { _poseSpinSpeed = Mathf.Clamp(value, 90, 1440); }
        public static void SetPoseLookDown(bool value) { _poseLookDown = value; }
        public static bool GetAimEnabled() { return _aimEnabled; }
        public static bool GetEspEnabled() { return _espEnabled; }
        public static bool GetMenuOpen() { return _menuOpen; }
        public static bool GetPrivateLobbyConsent() { return _privateLobbyConsent; }
        public static bool GetThirdPersonEnabled() { return _thirdPersonEnabled; }
        public static bool GetSilentAimEnabled() { return _silentAimEnabled; }
        public static int GetSilentAimMode() { return _silentAimMode; }
        public static int GetAimTrackingMode() { return _aimTrackingMode; }
        public static int GetAimTargetMask() { return _aimTargetMask; }
        public static int GetPoseMode() { return _poseMode; }
        public static int GetPoseSpinSpeed() { return _poseSpinSpeed; }
        public static bool GetPoseLookDown() { return _poseLookDown; }

        public static int SetSelectedSpawnId(int itemId)
        {
            if (ReferenceEquals(_instance, null) || itemId < 0 || itemId > 255) return 0;
            _selectedSpawnIdRequest = itemId;
            return 1;
        }

        public static int SetSelectedCatalogIndex(int catalogIndex)
        {
            if (ReferenceEquals(_instance, null) || catalogIndex < 0 || catalogIndex >= _instance.CatalogCount) return 0;
            _selectedCatalogIndexRequest = catalogIndex;
            return 1;
        }

        public static int RequestSelectedSpawn()
        {
            if (ReferenceEquals(_instance, null) || (_instance.SelectedSpawnMode == 0 && _selectedSpawnIdRequest == -2 && _selectedCatalogIndexRequest < 0)) return 0;
            var now = Environment.TickCount;
            if (_selectedSpawnRequested || (_lastSelectedSpawnRequestTick != int.MinValue && unchecked(now - _lastSelectedSpawnRequestTick) < 400)) return 0;
            _lastSelectedSpawnRequestTick = now;
            _selectedSpawnRequested = true;
            return 1;
        }

        public static int GetSelectedSpawnId() { return !ReferenceEquals(_instance, null) ? _instance.SelectedSpawnId : -1; }
        public static int GetSelectedSpawnMode() { return !ReferenceEquals(_instance, null) ? _instance.SelectedSpawnMode : 0; }
        public static int GetSelectedSpawnState() { return !ReferenceEquals(_instance, null) ? _instance.SelectedSpawnState : 0; }
        public static int GetCatalogCount() { return !ReferenceEquals(_instance, null) ? _instance.CatalogCount : 0; }
        public static string GetCatalogEntry(int catalogIndex) { return !ReferenceEquals(_instance, null) ? _instance.GetCatalogEntry(catalogIndex) : string.Empty; }
        public static int GetEspCount() { return !ReferenceEquals(_instance, null) ? _instance.EspCount : 0; }
        public static int GetAimTargetKind() { return !ReferenceEquals(_instance, null) ? _instance.AimTargetKind : 0; }
        public static int GetLastErrorCode() { return !ReferenceEquals(_instance, null) ? _instance.LastErrorCode : 0; }
        public static int GetLastSpawnStage() { return !ReferenceEquals(_instance, null) ? _instance.LastSpawnStage : 0; }
        public static int GetLastSpawnRendererCount() { return !ReferenceEquals(_instance, null) ? _instance.LastSpawnRendererCount : 0; }
        public static int GetSpawnRequestSequence() { return !ReferenceEquals(_instance, null) ? _instance.SpawnRequestSequence : 0; }
        public static int GetPoseState() { return !ReferenceEquals(_instance, null) ? _instance.PoseState : 0; }
        public static int GetAimTargetSpecies() { return !ReferenceEquals(_instance, null) ? _instance.AimTargetSpeciesValue : 0; }
        public static int GetBirdAliveCandidateCount() { return !ReferenceEquals(_instance, null) ? _instance.BirdAliveCandidateCount : 0; }
        public static int GetBirdFlyingCandidateCount() { return !ReferenceEquals(_instance, null) ? _instance.BirdFlyingCandidateCount : 0; }
        public static int GetPlayerCandidateCount() { return !ReferenceEquals(_instance, null) ? _instance.PlayerCandidateCount : 0; }
        public static int GetPoseSentPitchMilliDegrees() { return !ReferenceEquals(_instance, null) ? _instance.PoseSentPitchMilliDegrees : 0; }
        public static int GetPoseSentYawMilliDegrees() { return !ReferenceEquals(_instance, null) ? _instance.PoseSentYawMilliDegrees : 0; }
        public static int GetPoseRestoreCount() { return !ReferenceEquals(_instance, null) ? _instance.PoseRestoreCount : 0; }
        public static int GetThirdPersonState() { return !ReferenceEquals(_instance, null) ? _instance.ThirdPersonState : 0; }
        public static int GetThirdPersonBackend() { return !ReferenceEquals(_instance, null) ? _instance.ThirdPersonBackendValue : 0; }
        public static int GetThirdPersonSourceCameraId() { return !ReferenceEquals(_instance, null) ? _instance.ThirdPersonSourceCameraId : 0; }
        public static int GetThirdPersonRenderCount() { return !ReferenceEquals(_instance, null) ? _instance.ThirdPersonRenderCount : 0; }
        public static int GetThirdPersonRequestedDistanceMm() { return !ReferenceEquals(_instance, null) ? _instance.ThirdPersonRequestedDistanceMm : 0; }
        public static int GetThirdPersonCollisionDistanceMm() { return !ReferenceEquals(_instance, null) ? _instance.ThirdPersonCollisionDistanceMm : 0; }
        public static int GetThirdPersonAppliedDistanceMm() { return !ReferenceEquals(_instance, null) ? _instance.ThirdPersonAppliedDistanceMm : 0; }
        public static int GetThirdPersonHeadOffsetMm() { return !ReferenceEquals(_instance, null) ? _instance.ThirdPersonHeadOffsetMm : -1; }
        public static int GetThirdPersonBodyRendererCount() { return !ReferenceEquals(_instance, null) ? _instance.ThirdPersonBodyRendererCount : 0; }
        public static int GetThirdPersonBodyVisibleCount() { return !ReferenceEquals(_instance, null) ? _instance.ThirdPersonBodyVisibleCount : 0; }
        public static int GetThirdPersonRestoreReason() { return !ReferenceEquals(_instance, null) ? _instance.ThirdPersonRestoreReason : 0; }
        public static int GetThirdPersonAvatarBackend() { return !ReferenceEquals(_instance, null) ? _instance.ThirdPersonAvatarBackendValue : 0; }
        public static int GetAvatarMirrorState() { return !ReferenceEquals(_instance, null) ? _instance.AvatarMirrorStateValue : 0; }
        public static int GetAvatarSourceRootId() { return !ReferenceEquals(_instance, null) ? _instance.AvatarSourceRootId : 0; }
        public static int GetAvatarMeshCount() { return !ReferenceEquals(_instance, null) ? _instance.AvatarMeshCount : 0; }
        public static int GetAvatarSkinnedMeshCount() { return !ReferenceEquals(_instance, null) ? _instance.AvatarSkinnedMeshCount : 0; }
        public static int GetAvatarBoneCount() { return !ReferenceEquals(_instance, null) ? _instance.AvatarBoneCount : 0; }
        public static int GetAvatarBoundsDistanceMm() { return !ReferenceEquals(_instance, null) ? _instance.AvatarBoundsDistanceMm : -1; }
        public static int GetAvatarRebuildReason() { return !ReferenceEquals(_instance, null) ? _instance.AvatarRebuildReason : 0; }
        public static int GetAvatarTemplateCandidateCount() { return !ReferenceEquals(_instance, null) ? _instance.AvatarTemplateCandidateCount : 0; }
        public static int GetAvatarAppearanceApplyState() { return !ReferenceEquals(_instance, null) ? _instance.AvatarAppearanceApplyState : 0; }
        public static int GetAvatarIkCount() { return !ReferenceEquals(_instance, null) ? _instance.AvatarIkCount : 0; }
        public static int GetAvatarAnimationState() { return !ReferenceEquals(_instance, null) ? _instance.AvatarAnimationState : 0; }
        public static int GetAvatarAnimationFrameCount() { return !ReferenceEquals(_instance, null) ? _instance.AvatarAnimationFrameCount : 0; }
        public static int GetAvatarNativeStage() { return !ReferenceEquals(_instance, null) ? _instance.AvatarNativeStage : 0; }
        public static int GetAvatarNativeFailureCount() { return !ReferenceEquals(_instance, null) ? _instance.AvatarNativeFailureCount : 0; }
        public static int GetSilentAimState() { return !ReferenceEquals(_instance, null) ? _instance.SilentAimState : 0; }
        public static int GetTrackedProjectileCount() { return !ReferenceEquals(_instance, null) ? _instance.TrackedProjectileCount : 0; }

        public static int GetStatusWord()
        {
            var value = 0;
            if (_aimEnabled) value |= 1;
            if (_espEnabled) value |= 2;
            if (_menuOpen) value |= 4;
            if (_privateLobbyConsent) value |= 8;
            if (_thirdPersonEnabled) value |= 0x10;
            if (_silentAimEnabled) value |= 0x20;
            if (!ReferenceEquals(_instance, null))
            {
                value |= (_instance.AimTargetKind & 0x3) << 8;
                value |= (Mathf.Clamp(_instance.EspCount, 0, 0x7FFF) & 0x7FFF) << 16;
            }
            return value;
        }

        public static int RequestClientItem(int itemId)
        {
            if (!_privateLobbyConsent || ReferenceEquals(_instance, null) || itemId < 0 || itemId > 255) return 0;
            if (_instance.ClientSpawnState == 1 || _instance.ClientSpawnState == 2) return 0;
            _instance.ClientSpawnState = 1;
            _clientSpawnRequest = itemId;
            return 1;
        }

        public static int GetClientSpawnState() { return !ReferenceEquals(_instance, null) ? _instance.ClientSpawnState : 0; }
        public static void ResetClientSpawnState()
        {
            if (!ReferenceEquals(_instance, null) && _instance.ClientSpawnState != 1 && _instance.ClientSpawnState != 2) _instance.ClientSpawnState = 0;
        }

        public static void Shutdown()
        {
            _aimEnabled = _espEnabled = _menuOpen = _privateLobbyConsent = _thirdPersonEnabled = _silentAimEnabled = false;
            _aimTargetMask = 3;
            _poseMode = 0;
            _poseLookDown = false;
            _clientSpawnRequest = -1;
            _selectedSpawnIdRequest = -2;
            _selectedCatalogIndexRequest = -1;
            _selectedSpawnRequested = false;
            _lastSelectedSpawnRequestTick = int.MinValue;
            _shutdownRequested = true;
        }

        internal static void Tick()
        {
            if (ReferenceEquals(_instance, null)) return;
            _instance.ApplyControlState(_aimEnabled, _espEnabled, _menuOpen, _privateLobbyConsent, _thirdPersonEnabled, _silentAimEnabled, _aimTrackingMode, _silentAimMode, _aimTargetMask, _poseMode, _poseSpinSpeed, _poseLookDown);
            if (_selectedSpawnIdRequest != -2)
            {
                var id = _selectedSpawnIdRequest;
                _selectedSpawnIdRequest = -2;
                _instance.SelectSpawnById(id, true);
            }
            if (_selectedCatalogIndexRequest >= 0)
            {
                var index = _selectedCatalogIndexRequest;
                _selectedCatalogIndexRequest = -1;
                _instance.SelectSpawnByCatalogIndex(index, true);
            }
            if (_selectedSpawnRequested)
            {
                _selectedSpawnRequested = false;
                _instance.QueueSelectedSpawn();
            }
            if (_shutdownRequested)
            {
                _shutdownRequested = false;
                _instance.PrepareShutdown();
                var host = _instance.gameObject;
                _instance = null;
                _preInstance = null;
                UnityEngine.Object.Destroy(host);
            }
        }

        internal static int TakeClientSpawnRequest()
        {
            var value = _clientSpawnRequest;
            _clientSpawnRequest = -1;
            return value;
        }
    }

    internal enum RuntimeTargetKind { None, Creature, Player }
    [Flags] internal enum AimTargetFlags { None = 0, Fish = 1, Bird = 2, OtherCreature = 4, Player = 8 }
    internal enum AimTargetSpecies { None, Fish, Bird, OtherCreature, Player }
    internal enum AimTrackingMode { StableFirst, Continuous }
    internal enum SilentAimMode { InitialCorrection = 1, ProjectileTracking = 2 }
    internal enum ThirdPersonBackend { None, RenderCallback, NativeObserverCamera }
    internal enum PoseMode { Off, HideHeadBackwards, HighSpeedSpin }
    internal enum ThirdPersonAvatarBackend { None, MirroredNetworkPresentation, LoadedPlayerTemplate, LocalBodyFallback }
    internal enum AvatarMirrorState { Off, Building, Active, NoSource, NoRenderableContent, Failed }
    internal enum OverlayKind { Item = 1, Fish, Weapon, Quest, Dangerous }
    internal enum SpawnCatalogSource { Game, Named, Resource, Engine }
    internal enum SpawnCatalogCategory { Item, Fishing, Weapon, Fish, Quest, Explosive, Engine }
    internal enum RuntimeSpawnSafety { Safe, Confirm, HighRiskLocal, Blocked }
    internal enum EngineObjectCapability { NotEngine, VisualPreview, DiagnosticOnly }

    internal sealed class ProjectileTrackingState
    {
        internal uint Id;
        internal object Target;
        internal RuntimeTargetKind TargetKind;
        internal AimTargetSpecies TargetSpecies;
        internal float BoundAt;
        internal bool Occluded;
        internal bool InitialCorrected;
        internal bool TrackingStopped;
    }

    internal sealed class AimMotionSample
    {
        internal Vector3 RawPosition, FilteredPosition;
        internal float SampledAt, Speed, VerticalSpeed, UnstableUntil;
        internal bool Stable;
    }

    internal sealed class AvatarTransformBinding
    {
        internal Transform Source;
        internal Transform Mirror;
    }

    internal sealed class AvatarIkBinding
    {
        internal IK Solver;
        internal Transform Target, Pole;
        internal Vector3 DefaultTargetLocalPosition, DefaultPoleLocalPosition;
        internal Quaternion DefaultTargetLocalRotation, DefaultPoleLocalRotation;
        internal bool IsHand, IsFoot, IsLeft;
    }

    internal sealed class AvatarFieldRestore
    {
        internal object Target;
        internal FieldInfo Field;
        internal object OriginalValue;
    }

    internal sealed class OverlayEntry
    {
        internal int InstanceId;
        internal string Name;
        internal Transform Transform, TargetTransform;
        internal Item Item;
        internal Vector3 Screen;
        internal float Distance;
        internal bool Obstructed, Valid;
        internal OverlayKind Kind;
    }

    internal sealed class SpawnCatalogEntry
    {
        internal int Id, InstanceId;
        internal string DisplayName, SpawnKey, SafetyReason;
        internal Item Item;
        internal GameObject Prefab;
        internal SpawnCatalogSource Source;
        internal SpawnCatalogCategory Category;
        internal RuntimeSpawnSafety Safety;
        internal EngineObjectCapability EngineCapability;
        internal int RendererCount;
        internal bool IsNative { get { return Item != null; } }
    }

    [DefaultExecutionOrder(-32000)]
    public sealed class TrainerPreRuntimeBehaviour : MonoBehaviour
    {
        internal TrainerRuntimeBehaviour Owner;

        private void Update()
        {
            if (!ReferenceEquals(Owner, null)) Owner.ApplyPreWeaponDirection();
        }

    }

    [DefaultExecutionOrder(10000)]
    public sealed class TrainerRuntimeBehaviour : MonoBehaviour
    {
        private const float EntityRefreshInterval = 0.1f, ProjectionInterval = 1f / 60f, TargetRefreshInterval = 0.05f;
        private const float NativeSpawnCooldown = 0.5f, RawSpawnCooldown = 2f, ConfirmationLifetime = 10f;
        private const float AimUnstableGrace = 0.2f, AimMaxVerticalSpeed = 12f, AimMaxTargetSpeed = 35f, AimMaxAngularSpeed = 240f, AimTeleportDistance = 3f, ContinuousTargetSpeed = 15f;
        private const int DefaultMaxLabels = 200, MaxEngineEntries = 500, MaxRawClones = 20;

        private static readonly FieldInfo AliveCreaturesField = typeof(CreatureManager).GetField("_aliveCreatures", BindingFlags.Instance | BindingFlags.NonPublic);
        private static readonly FieldInfo FlyingBirdsField = typeof(BirdManager).GetField("_flyingBirds", BindingFlags.Instance | BindingFlags.NonPublic);
        private static readonly FieldInfo CameraRotationField = typeof(PlayerCamera).GetField("_rot", BindingFlags.Instance | BindingFlags.NonPublic);
        private static readonly FieldInfo CameraRecoilCurField = typeof(PlayerCamera).GetField("_recoilCur", BindingFlags.Instance | BindingFlags.NonPublic);
        private static readonly FieldInfo CameraRecoilTarField = typeof(PlayerCamera).GetField("_recoilTar", BindingFlags.Instance | BindingFlags.NonPublic);
        private static readonly FieldInfo RawLookInputField = typeof(PlayerCamera).GetField("_rawLookInput", BindingFlags.Instance | BindingFlags.NonPublic);
        private static readonly FieldInfo ControllerLookInputField = typeof(PlayerCamera).GetField("_controllerLookInput", BindingFlags.Instance | BindingFlags.NonPublic);
        private static readonly FieldInfo LookInputField = typeof(PlayerCamera).GetField("<LookInput>k__BackingField", BindingFlags.Instance | BindingFlags.NonPublic);
        private static readonly FieldInfo NameSpawnablesField = typeof(GameInfo).GetField("_nameToSpawnable", BindingFlags.Static | BindingFlags.NonPublic);
        private static readonly MethodInfo UseSpawnCommandMethod = typeof(DazedCommands).GetMethod("UseSpawnCommand", BindingFlags.Static | BindingFlags.Public | BindingFlags.NonPublic);
        private static readonly FieldInfo PlayerProjectilesField = typeof(ProjectileManager).GetField("_playerProjectiles", BindingFlags.Instance | BindingFlags.NonPublic);
        private static readonly FieldInfo SniperUiField = typeof(WeaponUI).GetField("_sniperUI", BindingFlags.Instance | BindingFlags.NonPublic);
        private static readonly FieldInfo PlayerUiWeaponField = typeof(PlayerUI).GetField("weaponUI", BindingFlags.Instance | BindingFlags.Public | BindingFlags.NonPublic);
        private static readonly FieldInfo DeathCameraField = typeof(PlayerDeathCam).GetField("_deathCam", BindingFlags.Instance | BindingFlags.NonPublic);
        private static readonly FieldInfo BodyNewCharacterField = typeof(PlayerBody).GetField("_newCharacter", BindingFlags.Instance | BindingFlags.NonPublic);
        private static readonly FieldInfo BodyOldCharacterField = typeof(PlayerBody).GetField("_oldCharacter", BindingFlags.Instance | BindingFlags.NonPublic);
        private static readonly FieldInfo BodyIsOldModelField = typeof(PlayerBody).GetField("_isOldModel", BindingFlags.Instance | BindingFlags.NonPublic);
        private static readonly FieldInfo PlayerOtherField = typeof(Player).GetField("_other", BindingFlags.Instance | BindingFlags.NonPublic);
        private static readonly FieldInfo OtherTransformField = typeof(OtherPlayer).GetField("_transform", BindingFlags.Instance | BindingFlags.NonPublic);
        private static readonly FieldInfo OtherCamProxyField = typeof(OtherPlayer).GetField("_camProxy", BindingFlags.Instance | BindingFlags.NonPublic);
        private static readonly FieldInfo OtherVelocityField = typeof(OtherPlayer).GetField("<Velocity>k__BackingField", BindingFlags.Instance | BindingFlags.NonPublic);
        private static readonly FieldInfo OtherFlatVelocityField = typeof(OtherPlayer).GetField("<FlatVelocity>k__BackingField", BindingFlags.Instance | BindingFlags.NonPublic);
        private static readonly FieldInfo OtherFlatLocalVelocityField = typeof(OtherPlayer).GetField("<FlatLocalVelocity>k__BackingField", BindingFlags.Instance | BindingFlags.NonPublic);
        private static readonly FieldInfo OtherVelMagField = typeof(OtherPlayer).GetField("<VelMag>k__BackingField", BindingFlags.Instance | BindingFlags.NonPublic);
        private static readonly FieldInfo OtherOnBoatField = typeof(OtherPlayer).GetField("<OnBoat>k__BackingField", BindingFlags.Instance | BindingFlags.NonPublic);
        private static readonly FieldInfo OtherGroundedField = typeof(OtherPlayer).GetField("_grounded", BindingFlags.Instance | BindingFlags.NonPublic);
        private static readonly MethodInfo BodyAwakeMethod = typeof(PlayerBody).GetMethod("Awake", BindingFlags.Instance | BindingFlags.NonPublic);
        private static readonly MethodInfo BodyApplyMethod = typeof(PlayerBody).GetMethod("SetAndApplyPosRots", BindingFlags.Instance | BindingFlags.NonPublic);
        private static readonly MethodInfo HandsAwakeMethod = typeof(PlayerHands).GetMethod("Awake", BindingFlags.Instance | BindingFlags.NonPublic);
        private static readonly MethodInfo HandsLateUpdateMethod = typeof(PlayerHands).GetMethod("LateUpdate", BindingFlags.Instance | BindingFlags.NonPublic);
        private static readonly MethodInfo LegsAwakeMethod = typeof(PlayerLegs).GetMethod("Awake", BindingFlags.Instance | BindingFlags.NonPublic);
        private static readonly MethodInfo LegsUpdateMethod = typeof(PlayerLegs).GetMethod("Update", BindingFlags.Instance | BindingFlags.NonPublic);
        private static readonly FieldInfo PlayerSkinField = typeof(Player).GetField("_playerSkin", BindingFlags.Instance | BindingFlags.NonPublic);
        private static readonly FieldInfo SkinBodyRendererField = typeof(PlayerSkin).GetField("_bodyRenderer", BindingFlags.Instance | BindingFlags.NonPublic);
        private static readonly FieldInfo SkinLeftHandRendererField = typeof(PlayerSkin).GetField("_leftHand", BindingFlags.Instance | BindingFlags.NonPublic);
        private static readonly FieldInfo SkinRightHandRendererField = typeof(PlayerSkin).GetField("_rightHand", BindingFlags.Instance | BindingFlags.NonPublic);
        private static readonly FieldInfo SkinOutfitRendererField = typeof(PlayerSkin).GetField("_outfitRenderer", BindingFlags.Instance | BindingFlags.NonPublic);
        private static readonly FieldInfo SkinHatRendererField = typeof(PlayerSkin).GetField("_hatRenderer", BindingFlags.Instance | BindingFlags.NonPublic);
        private static readonly FieldInfo SkinAccessoryRendererField = typeof(PlayerSkin).GetField("_accessoryRenderer", BindingFlags.Instance | BindingFlags.NonPublic);
        private static readonly MethodInfo SkinInitializeOtherMethod = typeof(PlayerSkin).GetMethod("InitializeOther", BindingFlags.Instance | BindingFlags.NonPublic);
        private static readonly FieldInfo IkTargetOffsetField = typeof(IK).GetField("_targetOffset", BindingFlags.Instance | BindingFlags.NonPublic);
        private static readonly FieldInfo IkChainLengthField = typeof(IK).GetField("_chainLength", BindingFlags.Instance | BindingFlags.NonPublic);
        private static readonly FieldInfo IkPoleField = typeof(IK).GetField("_pole", BindingFlags.Instance | BindingFlags.NonPublic);
        private static readonly FieldInfo IkEnableStretchField = typeof(IK).GetField("_enableStretch", BindingFlags.Instance | BindingFlags.NonPublic);
        private static readonly FieldInfo IkIterationsField = typeof(IK).GetField("_iterations", BindingFlags.Instance | BindingFlags.NonPublic);
        private static readonly FieldInfo IkDeltaField = typeof(IK).GetField("_delta", BindingFlags.Instance | BindingFlags.NonPublic);
        private static readonly FieldInfo IkSnapBackField = typeof(IK).GetField("_snapBackStrength", BindingFlags.Instance | BindingFlags.NonPublic);
        private static readonly FieldInfo IkStopResolvingField = typeof(IK).GetField("_stopResolving", BindingFlags.Instance | BindingFlags.NonPublic);
        private static readonly MethodInfo IkInitMethod = typeof(IK).GetMethod("Init", BindingFlags.Instance | BindingFlags.Public | BindingFlags.NonPublic);
        private static readonly MethodInfo IkResolveMethod = typeof(IK).GetMethod("ResolveIK", BindingFlags.Instance | BindingFlags.Public | BindingFlags.NonPublic);
        private static readonly FieldInfo TimeManagerPreTickField = typeof(FishNet.Managing.Timing.TimeManager).GetField("OnPreTick", BindingFlags.Instance | BindingFlags.NonPublic);

        private readonly List<OverlayEntry> _overlayEntries = new List<OverlayEntry>(DefaultMaxLabels);
        private readonly List<SpawnCatalogEntry> _catalog = new List<SpawnCatalogEntry>(256);
        private string[] _catalogExport = new string[0];
        private readonly List<GameObject> _rawClones = new List<GameObject>(MaxRawClones);
        private readonly Dictionary<int, AimMotionSample> _aimMotion = new Dictionary<int, AimMotionSample>();
        private readonly Dictionary<uint, ProjectileTrackingState> _projectileTracking = new Dictionary<uint, ProjectileTrackingState>();
        private readonly HashSet<uint> _projectilesSeen = new HashSet<uint>();
        private readonly HashSet<uint> _ignoredExistingProjectiles = new HashSet<uint>();
        private readonly List<InputAction> _blockedActions = new List<InputAction>(3);
        private readonly List<bool> _blockedActionStates = new List<bool>(3);
        private readonly Dictionary<Renderer, bool> _localBodyRendererStates = new Dictionary<Renderer, bool>();
        private readonly Dictionary<Renderer, bool> _localBodyForceRenderingStates = new Dictionary<Renderer, bool>();
        private readonly Dictionary<Renderer, bool> _localArmRendererStates = new Dictionary<Renderer, bool>();
        private readonly Dictionary<GameObject, bool> _localBodyObjectStates = new Dictionary<GameObject, bool>();
        private readonly List<AvatarTransformBinding> _avatarTransforms = new List<AvatarTransformBinding>(128);
        private readonly Dictionary<Transform, Transform> _avatarTransformMap = new Dictionary<Transform, Transform>();
        private readonly List<SkinnedMeshRenderer> _avatarSkinnedRenderers = new List<SkinnedMeshRenderer>(16);
        private readonly List<AvatarIkBinding> _avatarIkBindings = new List<AvatarIkBinding>(4);
        private readonly List<AvatarFieldRestore> _avatarFieldRestores = new List<AvatarFieldRestore>(32);
        private readonly Dictionary<Behaviour, bool> _avatarBehaviourStates = new Dictionary<Behaviour, bool>();
        private readonly HashSet<Transform> _avatarSourceBones = new HashSet<Transform>();
        private readonly HashSet<int> _aimCandidateIds = new HashSet<int>();
        private readonly RaycastHit[] _thirdPersonHits = new RaycastHit[32];

        private bool _aimEnabled, _espEnabled, _menuOpen, _privateLobbyConsent, _thirdPersonEnabled, _silentAimEnabled, _poseLookDown, _ignoreOcclusion, _highRiskEnabled;
        private bool _thirdPersonCrosshair, _thirdPersonSaved, _poseApplied, _firePointApplied, _silentTrackingWasActive;
        private bool _renderCallbacksInstalled, _renderOverrideApplied, _thirdPersonSnapshotValid, _savedSourceCameraEnabled, _savedObserverActive, _savedObserverEnabled;
        private AimTrackingMode _aimTrackingMode = AimTrackingMode.StableFirst;
        private SilentAimMode _silentAimMode = SilentAimMode.InitialCorrection;
        private AimTargetFlags _aimTargetMask = AimTargetFlags.Fish | AimTargetFlags.Bird;
        private AimTargetSpecies _lockedSpecies;
        private PoseMode _poseMode;
        private float _maxAimDistance = 120f, _smoothing = 18f, _maxYawSpeed = 240f, _maxPitchSpeed = 90f, _recoilCompensation = 1f, _maxEspDistance = 150f;
        private float _thirdPersonDistance = 3.5f, _thirdPersonHeight = 0.35f, _thirdPersonShoulder = 0.45f, _poseSpinSpeed = 720f, _poseSpinYaw;
        private int _maxLabels = DefaultMaxLabels, _fontSize = 14, _occlusionCursor, _tab, _catalogFilter = -1;
        private float _nextEntityRefreshAt, _nextProjectionAt, _nextTargetRefreshAt, _nextCatalogCheckAt, _avatarNextSourceSearchAt;
        private float _lastNativeSpawnAt = float.NegativeInfinity, _lastRawSpawnAt = float.NegativeInfinity;
        private object _lockedTarget;
        private RuntimeTargetKind _lockedKind;
        private Vector3 _lockedPosition;
        private float _lockedDistance = float.MaxValue;
        private GUIStyle _labelStyle, _shadowStyle;
        private Rect _windowRect = new Rect(24f, 70f, 700f, 620f);
        private Vector2 _spawnScroll;
        private string _catalogSearch = string.Empty;
        private int _catalogAnchor;
        private ulong _activeSceneHandle;
        private SpawnCatalogEntry _selectedSpawn;
        private bool _selectionConfirmed, _spawnRequestPending, _cursorStateSaved, _previousMouseLocked;
        private float _selectionConfirmedAt, _clientSpawnStartedAt;
        private int _previousHeldItemId;
        private Player _thirdPersonPlayer;
        private GameObject _avatarSourceRoot, _avatarMirrorRoot;
        private PlayerSkin _avatarTemplateSkin;
        private PlayerBody _avatarTemplateBody;
        private PlayerHands _avatarTemplateHands;
        private PlayerLegs _avatarTemplateLegs;
        private PlayerBody _avatarNativeBody;
        private PlayerHands _avatarNativeHands;
        private PlayerLegs _avatarNativeLegs;
        private OtherPlayer _avatarNativeOther;
        private Transform _avatarCamProxy;
        private Transform _avatarHeadMirror, _avatarModelRoot;
        private ThirdPersonAvatarBackend _thirdPersonAvatarBackend, _resolvedAvatarBackend;
        private AvatarMirrorState _avatarMirrorState;
        private int _avatarSourceRendererCount, _avatarHeldItemId, _avatarVisualSignature;
        private Camera _thirdPersonSourceCamera, _thirdPersonObserverCamera;
        private ThirdPersonBackend _thirdPersonBackend;
        private Vector3 _thirdPersonPivot, _thirdPersonDesiredPosition, _renderSavedPosition, _observerSavedPosition;
        private Quaternion _thirdPersonDesiredRotation, _renderSavedRotation, _observerSavedRotation, _poseSavedLocalRotation, _firePointSavedRotation;
        private int _savedSourceCullingMask, _savedObserverCullingMask, _thirdPersonWaitFrames, _thirdPersonLastObservedRenderCount, _thirdPersonSourceCameraId;
        private float _savedSourceNearClip, _savedObserverNearClip, _savedObserverFov;
        private Transform _poseCameraTransform, _firePointTransform;
        private CanvasGroup _sniperUi;
        private float _savedSniperAlpha;
        private bool _savedSniperInteractable, _savedSniperBlocksRaycasts, _sniperUiSaved;
        private FishNet.Managing.Timing.TimeManager _timeManager;
        private bool _tickHooksInstalled, _poseOrderingReady;

        public int EspCount { get; private set; }
        public int AimTargetKind { get { return (int)_lockedKind; } }
        public int AimTargetSpeciesValue { get { return (int)_lockedSpecies; } }
        public int LastErrorCode { get; private set; }
        public int ClientSpawnState { get; internal set; }
        public int SelectedSpawnId { get { return _selectedSpawn != null ? _selectedSpawn.Id : -1; } }
        public int SelectedSpawnMode { get { return _selectedSpawn == null ? 0 : (_selectedSpawn.IsNative ? 1 : 2); } }
        public int SelectedSpawnState { get; private set; }
        public int CatalogCount { get { return _catalogExport.Length; } }
        public int LastSpawnStage { get; private set; }
        public int LastSpawnRendererCount { get; private set; }
        public int SpawnRequestSequence { get; private set; }
        public int PoseState { get; private set; }
        public int PoseSentPitchMilliDegrees { get; private set; }
        public int PoseSentYawMilliDegrees { get; private set; }
        public int PoseRestoreCount { get; private set; }
        public int ThirdPersonState { get; private set; }
        public int ThirdPersonBackendValue { get { return (int)_thirdPersonBackend; } }
        public int ThirdPersonSourceCameraId { get { return _thirdPersonSourceCameraId; } }
        public int ThirdPersonRenderCount { get; private set; }
        public int ThirdPersonRequestedDistanceMm { get; private set; }
        public int ThirdPersonCollisionDistanceMm { get; private set; }
        public int ThirdPersonAppliedDistanceMm { get; private set; }
        public int ThirdPersonHeadOffsetMm { get; private set; }
        public int ThirdPersonBodyRendererCount { get; private set; }
        public int ThirdPersonBodyVisibleCount { get; private set; }
        public int ThirdPersonRestoreReason { get; private set; }
        public int ThirdPersonAvatarBackendValue { get { return (int)_thirdPersonAvatarBackend; } }
        public int AvatarMirrorStateValue { get { return (int)_avatarMirrorState; } }
        public int AvatarSourceRootId { get; private set; }
        public int AvatarMeshCount { get; private set; }
        public int AvatarSkinnedMeshCount { get; private set; }
        public int AvatarBoneCount { get; private set; }
        public int AvatarBoundsDistanceMm { get; private set; }
        public int AvatarRebuildReason { get; private set; }
        public int AvatarTemplateCandidateCount { get; private set; }
        public int AvatarAppearanceApplyState { get; private set; }
        public int AvatarIkCount { get; private set; }
        public int AvatarAnimationState { get; private set; }
        public int AvatarAnimationFrameCount { get; private set; }
        public int AvatarNativeStage { get; private set; }
        public int AvatarNativeFailureCount { get; private set; }
        public int BirdAliveCandidateCount { get; private set; }
        public int BirdFlyingCandidateCount { get; private set; }
        public int PlayerCandidateCount { get; private set; }
        public int SilentAimState { get; private set; }
        public int TrackedProjectileCount { get { return _projectileTracking.Count; } }

        internal string GetCatalogEntry(int index)
        {
            var snapshot = _catalogExport;
            return index >= 0 && index < snapshot.Length ? snapshot[index] : string.Empty;
        }

        internal void ApplyControlState(bool aim, bool esp, bool menu, bool consent, bool thirdPerson, bool silentAim, int trackingMode, int silentAimMode, int aimTargetMask, int poseMode, int poseSpinSpeed, bool poseLookDown)
        {
            _aimEnabled = aim;
            _espEnabled = esp;
            _privateLobbyConsent = consent;
            _thirdPersonEnabled = thirdPerson;
            _silentAimEnabled = silentAim;
            _aimTrackingMode = trackingMode == 1 ? AimTrackingMode.Continuous : AimTrackingMode.StableFirst;
            _silentAimMode = silentAimMode == 2 ? SilentAimMode.ProjectileTracking : SilentAimMode.InitialCorrection;
            var previousTargetMask = _aimTargetMask;
            _aimTargetMask = (AimTargetFlags)(aimTargetMask & 0x0F);
            if (!_privateLobbyConsent) _aimTargetMask &= ~AimTargetFlags.Player;
            var requestedPoseMode = _privateLobbyConsent && poseMode >= 0 && poseMode <= 2 ? (PoseMode)poseMode : PoseMode.Off;
            if (_poseMode != requestedPoseMode && requestedPoseMode == PoseMode.HighSpeedSpin)
            {
                try
                {
                    var local = Player.LocalPlayer;
                    var camTransform = local != null && local.Camera != null ? local.Camera.CamTransform : null;
                    _poseSpinYaw = camTransform != null ? camTransform.localEulerAngles.y : 0f;
                }
                catch { _poseSpinYaw = 0f; }
            }
            _poseMode = requestedPoseMode;
            _poseSpinSpeed = Mathf.Clamp(poseSpinSpeed, 90f, 1440f);
            _poseLookDown = _privateLobbyConsent && poseLookDown;
            if (_lockedSpecies == AimTargetSpecies.Player && (_aimTargetMask & AimTargetFlags.Player) == 0) ClearTarget(true);
            if ((previousTargetMask & AimTargetFlags.Player) != 0 && (_aimTargetMask & AimTargetFlags.Player) == 0) _projectileTracking.Clear();
            if (_menuOpen != menu)
            {
                _menuOpen = menu;
                UpdateInputCapture();
            }
        }

        private void OnEnable()
        {
            InstallRenderCallbacks();
        }

        private void OnDisable()
        {
            RestoreOutboundPose();
            RemoveTickHooks();
            RestoreThirdPerson(7);
            RemoveRenderCallbacks();
        }

        private void Update()
        {
            RestoreRenderOverride();
            Bootstrap.Tick();
            RestorePreWeaponDirection();
            EnsureTickHooks();
            ProcessClientSpawnRequest();
            ProcessSelectedSpawnRequest();
            TrackScene();
            if (Time.unscaledTime >= _nextCatalogCheckAt)
            {
                _nextCatalogCheckAt = Time.unscaledTime + 1f;
                EnsureCatalog();
            }
            if (_menuOpen) KeepMenuInputCaptured();
            if (_espEnabled && Time.unscaledTime >= _nextEntityRefreshAt)
            {
                _nextEntityRefreshAt = Time.unscaledTime + EntityRefreshInterval;
                RefreshOverlayEntities();
            }
            else if (!_espEnabled && _overlayEntries.Count != 0)
            {
                _overlayEntries.Clear();
                EspCount = 0;
            }
            if (_poseMode == PoseMode.HighSpeedSpin && _privateLobbyConsent && !_menuOpen)
                _poseSpinYaw = Mathf.Repeat(_poseSpinYaw + _poseSpinSpeed * Time.unscaledDeltaTime, 360f);
        }

        private void LateUpdate()
        {
            RestoreOutboundPose();
            if (_espEnabled && Time.unscaledTime >= _nextProjectionAt)
            {
                _nextProjectionAt = Time.unscaledTime + ProjectionInterval;
                UpdateOverlayProjection();
            }
            if ((!_aimEnabled && !_silentAimEnabled) || _menuOpen) ClearTarget(true);
            else UpdateAim();
            UpdateThirdPersonCamera();
        }

        private void FixedUpdate()
        {
            UpdateTrackedProjectiles();
        }

        private void OnDestroy()
        {
            ClearTarget(true);
            _aimMotion.Clear();
            RestorePreWeaponDirection();
            RestoreOutboundPose();
            RestoreThirdPerson(7);
            RemoveRenderCallbacks();
            RemoveTickHooks();
            _projectileTracking.Clear();
            _ignoredExistingProjectiles.Clear(); _silentTrackingWasActive = false;
            RestoreInputCapture();
            DestroyRawClones();
            _overlayEntries.Clear();
            _catalog.Clear();
        }

        internal void PrepareShutdown()
        {
            _spawnRequestPending = false;
            _selectedSpawn = null;
            _selectionConfirmed = false;
            _highRiskEnabled = false;
            ClearTarget(true);
            _aimMotion.Clear();
            RestorePreWeaponDirection();
            RestoreOutboundPose();
            RestoreThirdPerson(7);
            RemoveTickHooks();
            _projectileTracking.Clear();
            _ignoredExistingProjectiles.Clear(); _silentTrackingWasActive = false;
            RestoreInputCapture();
            DestroyRawClones();
        }

        private void TrackScene()
        {
            var handle = SceneManager.GetActiveScene().handle.GetRawData();
            if (_activeSceneHandle == 0) { _activeSceneHandle = handle; return; }
            if (handle == _activeSceneHandle) return;
            _activeSceneHandle = handle;
            DestroyRawClones();
            ClearTarget(true);
            _aimMotion.Clear();
            RestorePreWeaponDirection();
            RestoreOutboundPose();
            RestoreThirdPerson(5);
            _projectileTracking.Clear();
            _ignoredExistingProjectiles.Clear(); _silentTrackingWasActive = false;
            _catalogAnchor = 0;
            _selectedSpawn = null;
            _selectionConfirmed = false;
            _catalog.Clear();
        }

        private void EnsureTickHooks()
        {
            try
            {
                var current = FishNet.InstanceFinder.TimeManager;
                if (_tickHooksInstalled && _timeManager == current) return;
                RemoveTickHooks();
                if (current == null) return;
                _timeManager = current;
                _timeManager.OnPreTick += ApplyOutboundPose;
                _timeManager.OnPostTick += RestoreOutboundPose;
                _poseOrderingReady = PutPoseHandlerFirst();
                _tickHooksInstalled = true;
            }
            catch { RemoveTickHooks(); PoseState = -4; LastErrorCode = 605; }
        }

        private bool PutPoseHandlerFirst()
        {
            if (_timeManager == null || TimeManagerPreTickField == null) return false;
            try
            {
                var chain = TimeManagerPreTickField.GetValue(_timeManager) as Delegate;
                var handler = (Delegate)(Action)ApplyOutboundPose;
                var withoutHandler = Delegate.Remove(chain, handler);
                TimeManagerPreTickField.SetValue(_timeManager, Delegate.Combine(handler, withoutHandler));
                return true;
            }
            catch { PoseState = -5; LastErrorCode = 606; return false; }
        }

        private void RemoveTickHooks()
        {
            if (_tickHooksInstalled && _timeManager != null)
            {
                try { _timeManager.OnPreTick -= ApplyOutboundPose; } catch { }
                try { _timeManager.OnPostTick -= RestoreOutboundPose; } catch { }
            }
            _tickHooksInstalled = false;
            _poseOrderingReady = false;
            _timeManager = null;
            RestoreOutboundPose();
        }

        private void UpdateAim()
        {
            try
            {
                var local = Player.LocalPlayer;
                var visibleRequested = _aimEnabled && Input.GetMouseButton(1);
                var silentRequested = _silentAimEnabled;
                if (local == null || local.BlockInputs || (!visibleRequested && !silentRequested)) { ClearTarget(true); return; }
                var held = local.Holding != null ? local.Holding.HeldItem : null;
                var weapon = held != null ? held.Weapon : null;
                if (weapon == null || local.CurCam == null || (visibleRequested && !silentRequested && !weapon.IsAds)) { ClearTarget(true); return; }
                var camera = local.CurCam;
                bool lockedStable;
                var lockedValid = TryGetLockedTargetPosition(camera, out _lockedPosition, out _lockedDistance, out lockedStable);
                if (Time.unscaledTime >= _nextTargetRefreshAt || !lockedValid || (_aimTrackingMode == AimTrackingMode.StableFirst && !lockedStable))
                {
                    _nextTargetRefreshAt = Time.unscaledTime + TargetRefreshInterval;
                    object candidate; RuntimeTargetKind kind; AimTargetSpecies species; Vector3 position; float distance;
                    if (FindBestTarget(camera, out candidate, out kind, out species, out position, out distance))
                    {
                        if (_lockedTarget == null || candidate == _lockedTarget || !lockedStable || distance < _lockedDistance * 0.9f)
                        {
                            _lockedTarget = candidate; _lockedKind = kind; _lockedSpecies = species; _lockedPosition = position; _lockedDistance = distance;
                        }
                    }
                    else if (!lockedValid || !CanHoldUnstableTarget(_lockedTarget))
                    {
                        ClearTarget(true); return;
                    }
                }
                if (!TryGetLockedTargetPosition(camera, out _lockedPosition, out _lockedDistance, out lockedStable)) { ClearTarget(true); return; }
                if (_aimTrackingMode == AimTrackingMode.StableFirst && !lockedStable && !CanHoldUnstableTarget(_lockedTarget)) { ClearTarget(true); return; }
                var direction = _lockedPosition - camera.transform.position;
                if (!IsFinite(direction) || direction.sqrMagnitude < 0.001f) { ClearTarget(true); return; }
                if (!visibleRequested || !weapon.IsAds) { LastErrorCode = 0; return; }
                ApplyRecoilCompensation(local);
                var desired = Quaternion.LookRotation(direction.normalized, Vector3.up).eulerAngles;
                var current = camera.transform.rotation.eulerAngles;
                var blend = 1f - Mathf.Exp(-_smoothing * Time.unscaledDeltaTime);
                var maxPitchStep = (_aimTrackingMode == AimTrackingMode.Continuous ? 120f : _maxPitchSpeed) * Time.unscaledDeltaTime;
                var maxYawStep = _maxYawSpeed * Time.unscaledDeltaTime;
                var pitch = Mathf.Clamp(Mathf.DeltaAngle(current.x, desired.x) * blend, -maxPitchStep, maxPitchStep);
                var yaw = Mathf.Clamp(Mathf.DeltaAngle(current.y, desired.y) * blend, -maxYawStep, maxYawStep);
                var next = new Vector3(current.x + pitch, current.y + yaw, 0f);
                if (CameraRotationField != null) CameraRotationField.SetValue(local.Camera, next);
                camera.transform.rotation = Quaternion.Euler(next);
                LastErrorCode = 0;
            }
            catch { LastErrorCode = 101; ClearTarget(true); }
        }

        private void ApplyRecoilCompensation(Player local)
        {
            if (_recoilCompensation > 0f)
            {
                if (CameraRecoilCurField != null)
                {
                    var value = (Vector2)CameraRecoilCurField.GetValue(local.Camera);
                    CameraRecoilCurField.SetValue(local.Camera, Vector2.Lerp(value, Vector2.zero, _recoilCompensation));
                }
                if (CameraRecoilTarField != null)
                {
                    var value = (Vector2)CameraRecoilTarField.GetValue(local.Camera);
                    CameraRecoilTarField.SetValue(local.Camera, Vector2.Lerp(value, Vector2.zero, _recoilCompensation));
                }
            }
        }

        internal void ApplyPreWeaponDirection()
        {
            RestorePreWeaponDirection();
            try
            {
                if (_menuOpen || (!_aimEnabled && !_silentAimEnabled) || _lockedTarget == null || (!_silentAimEnabled && !Input.GetMouseButton(1))) return;
                var local = Player.LocalPlayer;
                if (local == null || local.BlockInputs || local.Vitals == null || local.Vitals.Health <= 0) return;
                if (_silentAimEnabled && !local.IsServerInitialized && !_privateLobbyConsent) { SilentAimState = -1; return; }
                var held = local.Holding != null ? local.Holding.HeldItem : null;
                var weapon = held != null ? held.Weapon : null;
                if (weapon == null || (!_silentAimEnabled && !weapon.IsAds)) return;
                var firePoint = weapon.Attachments != null ? weapon.Attachments.FirePoint : null;
                if (firePoint == null) { if (_silentAimEnabled) SilentAimState = -2; return; }
                Vector3 targetPosition; Transform targetTransform;
                if (!TryGetBoundTargetPosition(_lockedTarget, _lockedKind, out targetPosition, out targetTransform)) return;
                var direction = targetPosition - firePoint.position;
                if (!IsFinite(direction) || direction.sqrMagnitude < 0.001f || (!_ignoreOcclusion && IsObstructed(firePoint.position, targetPosition, targetTransform))) return;
                _firePointTransform = firePoint;
                _firePointSavedRotation = firePoint.rotation;
                _firePointApplied = true;
                firePoint.rotation = Quaternion.LookRotation(direction.normalized, Vector3.up);
                if (_silentAimEnabled) SilentAimState = _silentAimMode == SilentAimMode.ProjectileTracking ? (local.IsServerInitialized ? 2 : 3) : 1;
            }
            catch
            {
                RestorePreWeaponDirection();
                SilentAimState = -3;
                _silentAimEnabled = false;
                Bootstrap.SetSilentAimEnabled(false);
                LastErrorCode = 601;
            }
        }

        private void RestorePreWeaponDirection()
        {
            if (!_firePointApplied) return;
            try { if (_firePointTransform != null) _firePointTransform.rotation = _firePointSavedRotation; } catch { }
            _firePointApplied = false;
            _firePointTransform = null;
        }

        internal void ApplyOutboundPose()
        {
            RestoreOutboundPose();
            if (!_poseOrderingReady) { PoseState = -5; return; }
            if (_poseMode == PoseMode.Off && !_poseLookDown) { PoseState = 0; return; }
            if (!_privateLobbyConsent || _menuOpen) { PoseState = _privateLobbyConsent ? 1 : -1; return; }
            try
            {
                var local = Player.LocalPlayer;
                var cameraTransform = local != null && local.Camera != null ? local.Camera.CamTransform : null;
                if (cameraTransform == null || local.Vitals == null || local.Vitals.Health <= 0) { PoseState = -2; return; }
                _poseCameraTransform = cameraTransform;
                _poseSavedLocalRotation = cameraTransform.localRotation;
                var view = _poseSavedLocalRotation.eulerAngles;
                var pitch = _poseLookDown ? 89f : view.x;
                var yaw = _poseMode == PoseMode.HideHeadBackwards ? Mathf.Repeat(view.y + 180f, 360f) : (_poseMode == PoseMode.HighSpeedSpin ? _poseSpinYaw : view.y);
                cameraTransform.localRotation = Quaternion.Euler(pitch, yaw, 0f);
                _poseApplied = true;
                PoseSentPitchMilliDegrees = Mathf.RoundToInt(pitch * 1000f);
                PoseSentYawMilliDegrees = Mathf.RoundToInt(yaw * 1000f);
                PoseState = 2;
            }
            catch { RestoreOutboundPose(); PoseState = -3; LastErrorCode = 602; }
        }

        private void RestoreOutboundPose()
        {
            if (!_poseApplied) return;
            try { if (_poseCameraTransform != null) _poseCameraTransform.localRotation = _poseSavedLocalRotation; } catch { }
            PoseRestoreCount++;
            _poseApplied = false;
            _poseCameraTransform = null;
        }

        private void UpdateThirdPersonCamera()
        {
            if (!_thirdPersonEnabled)
            {
                RestoreThirdPerson();
                ThirdPersonState = 0;
                return;
            }
            try
            {
                var local = Player.LocalPlayer;
                if (local == null) { RestoreThirdPerson(1); ThirdPersonState = -1; return; }
                if (local.Vitals == null || local.Vitals.Health <= 0) { RestoreThirdPerson(3, true); ThirdPersonState = -3; return; }
                if (_thirdPersonSaved && _thirdPersonPlayer != local) RestoreThirdPerson(4);

                var source = _thirdPersonSaved ? _thirdPersonSourceCamera : local.CurCam;
                if (source == null) { RestoreThirdPerson(2); ThirdPersonState = -2; return; }
                if (!_thirdPersonSaved) BeginThirdPerson(local, source);
                if (_thirdPersonSourceCamera == null) { RestoreThirdPerson(2); ThirdPersonState = -2; return; }
                MaintainAvatarMirror(local);

                Vector3 pivot;
                ResolveThirdPersonPivot(local, _thirdPersonSourceCamera, out pivot);
                var rotation = _thirdPersonSourceCamera.transform.rotation;
                var requested = pivot - rotation * Vector3.forward * _thirdPersonDistance + rotation * Vector3.right * _thirdPersonShoulder + Vector3.up * _thirdPersonHeight;
                var ray = requested - pivot;
                var requestedDistance = ray.magnitude;
                var appliedDistance = requestedDistance;
                if (requestedDistance > 0.001f)
                {
                    var localTransform = local.Transform != null ? local.Transform : local.transform;
                    var hitCount = Physics.SphereCastNonAlloc(pivot, 0.2f, ray / requestedDistance, _thirdPersonHits, requestedDistance, Physics.DefaultRaycastLayers, QueryTriggerInteraction.Ignore);
                    for (var i = 0; i < hitCount; i++)
                    {
                        var hitTransform = _thirdPersonHits[i].transform;
                        if (hitTransform == null || hitTransform == localTransform || (localTransform != null && hitTransform.IsChildOf(localTransform))) continue;
                        appliedDistance = Mathf.Min(appliedDistance, Mathf.Max(0.1f, _thirdPersonHits[i].distance - 0.15f));
                    }
                }
                _thirdPersonPivot = pivot;
                _thirdPersonDesiredPosition = requestedDistance > 0.001f ? pivot + ray.normalized * appliedDistance : requested;
                _thirdPersonDesiredRotation = rotation;
                var sourceDisplacement = Vector3.Distance(_thirdPersonSourceCamera.transform.position, _thirdPersonDesiredPosition);
                _thirdPersonSnapshotValid = IsFinite(_thirdPersonDesiredPosition)
                    && IsFinite(_thirdPersonSourceCamera.transform.position)
                    && sourceDisplacement <= Mathf.Min(12f, requestedDistance + 1f);
                ThirdPersonRequestedDistanceMm = Mathf.RoundToInt(requestedDistance * 1000f);
                ThirdPersonCollisionDistanceMm = Mathf.RoundToInt(appliedDistance * 1000f);
                if (!_thirdPersonSnapshotValid)
                {
                    ThirdPersonAppliedDistanceMm = Mathf.RoundToInt(sourceDisplacement * 1000f);
                    ThirdPersonState = -10;
                    LastErrorCode = 610;
                    return;
                }

                if (_thirdPersonBackend == ThirdPersonBackend.RenderCallback)
                {
                    if (ThirdPersonRenderCount != _thirdPersonLastObservedRenderCount)
                    {
                        _thirdPersonLastObservedRenderCount = ThirdPersonRenderCount;
                        _thirdPersonWaitFrames = 0;
                        ThirdPersonState = 1;
                    }
                    else if (Application.isFocused && _thirdPersonSourceCamera.gameObject.activeInHierarchy)
                    {
                        _thirdPersonWaitFrames++;
                        ThirdPersonState = 10;
                        if (_thirdPersonWaitFrames >= 30 && !TryActivateNativeObserver(local))
                        {
                            RestoreThirdPerson(9);
                            ThirdPersonState = -9;
                            _thirdPersonEnabled = false;
                            Bootstrap.SetThirdPersonEnabled(false);
                            LastErrorCode = 609;
                            return;
                        }
                    }
                }
                else if (_thirdPersonBackend == ThirdPersonBackend.NativeObserverCamera)
                {
                    if (_thirdPersonObserverCamera == null)
                    {
                        RestoreThirdPerson(9);
                        ThirdPersonState = -9;
                        _thirdPersonEnabled = false;
                        Bootstrap.SetThirdPersonEnabled(false);
                        LastErrorCode = 609;
                        return;
                    }
                    _thirdPersonObserverCamera.transform.position = _thirdPersonDesiredPosition;
                    _thirdPersonObserverCamera.transform.rotation = _thirdPersonDesiredRotation;
                    ThirdPersonAppliedDistanceMm = Mathf.RoundToInt(Vector3.Distance(_thirdPersonSourceCamera.transform.position, _thirdPersonDesiredPosition) * 1000f);
                    if (ThirdPersonRenderCount != _thirdPersonLastObservedRenderCount)
                    {
                        _thirdPersonLastObservedRenderCount = ThirdPersonRenderCount;
                        _thirdPersonWaitFrames = 0;
                        ThirdPersonState = 2;
                    }
                    else if (Application.isFocused && _thirdPersonObserverCamera.gameObject.activeInHierarchy)
                    {
                        _thirdPersonWaitFrames++;
                        ThirdPersonState = 11;
                        if (_thirdPersonWaitFrames >= 30)
                        {
                            RestoreThirdPerson(9);
                            ThirdPersonState = -9;
                            _thirdPersonEnabled = false;
                            Bootstrap.SetThirdPersonEnabled(false);
                            LastErrorCode = 609;
                            return;
                        }
                    }
                }
                UpdateThirdPersonCrosshair();
            }
            catch
            {
                RestoreThirdPerson(6);
                ThirdPersonState = -9;
                _thirdPersonEnabled = false;
                Bootstrap.SetThirdPersonEnabled(false);
                LastErrorCode = 603;
            }
        }

        private void BeginThirdPerson(Player local, Camera source)
        {
            RestoreThirdPerson();
            InstallRenderCallbacks();
            _thirdPersonPlayer = local;
            _thirdPersonSourceCamera = source;
            _thirdPersonSourceCameraId = source.GetInstanceID();
            _savedSourceCameraEnabled = source.enabled;
            _savedSourceCullingMask = source.cullingMask;
            _savedSourceNearClip = source.nearClipPlane;
            SaveAndShowLocalBody(local);
            BuildAvatarMirror(local, 1);
            source.cullingMask |= GetLocalBodyLayerMask(local);
            source.nearClipPlane = Mathf.Min(source.nearClipPlane, 0.05f);
            _thirdPersonBackend = ThirdPersonBackend.RenderCallback;
            _thirdPersonWaitFrames = 0;
            _thirdPersonLastObservedRenderCount = ThirdPersonRenderCount;
            _thirdPersonSnapshotValid = false;
            ThirdPersonAppliedDistanceMm = 0;
            ThirdPersonRestoreReason = 0;
            ThirdPersonState = 10;
            _thirdPersonSaved = true;
        }

        private void ResolveThirdPersonPivot(Player local, Camera source, out Vector3 pivot)
        {
            // CurCam is the only coordinate that is proven to match the rendered local world.
            // The local PlayerBody rig can be a remote/network presentation located hundreds
            // of metres away, so bones and renderer bounds are diagnostics only, never anchors.
            if (source != null && IsFinite(source.transform.position))
            {
                pivot = source.transform.position;
                ThirdPersonHeadOffsetMm = -1;
                try
                {
                    if (local.Body != null && local.Body.Head != null && IsFinite(local.Body.Head.position))
                        ThirdPersonHeadOffsetMm = Mathf.RoundToInt(Vector3.Distance(pivot, local.Body.Head.position) * 1000f);
                }
                catch { ThirdPersonHeadOffsetMm = -1; }
                return;
            }
            var localTransform = local.Transform != null ? local.Transform : local.transform;
            pivot = localTransform != null ? localTransform.position + Vector3.up * 1.5f : Vector3.zero;
            ThirdPersonHeadOffsetMm = -1;
        }

        private void SaveAndShowLocalBody(Player local)
        {
            _localBodyRendererStates.Clear();
            _localBodyForceRenderingStates.Clear();
            _localArmRendererStates.Clear();
            _localBodyObjectStates.Clear();
            try
            {
                if (local.Body != null)
                {
                    var useOld = BodyIsOldModelField != null && (bool)BodyIsOldModelField.GetValue(local.Body);
                    var bodyObjectField = useOld ? BodyOldCharacterField : BodyNewCharacterField;
                    var bodyObject = bodyObjectField != null ? bodyObjectField.GetValue(local.Body) as GameObject : null;
                    if (bodyObject != null)
                    {
                        _localBodyObjectStates[bodyObject] = bodyObject.activeSelf;
                        bodyObject.SetActive(true);
                    }
                    var renderers = local.Body.GetComponentsInChildren<Renderer>(true);
                    for (var i = 0; i < renderers.Length; i++)
                    {
                        if (renderers[i] == null || _localBodyRendererStates.ContainsKey(renderers[i])) continue;
                        _localBodyRendererStates.Add(renderers[i], renderers[i].enabled);
                        _localBodyForceRenderingStates.Add(renderers[i], renderers[i].forceRenderingOff);
                        renderers[i].enabled = true;
                        renderers[i].forceRenderingOff = false;
                    }
                }
                if (local.Arms != null)
                {
                    var arms = local.Arms.GetComponentsInChildren<Renderer>(true);
                    for (var i = 0; i < arms.Length; i++)
                    {
                        if (arms[i] == null || _localArmRendererStates.ContainsKey(arms[i])) continue;
                        _localArmRendererStates.Add(arms[i], arms[i].enabled);
                        arms[i].enabled = false;
                    }
                }
            }
            catch { }
            MaintainLocalBodyVisibility();
        }

        private GameObject ResolveAvatarSourceRoot(Player local)
        {
            _resolvedAvatarBackend = ThirdPersonAvatarBackend.None;
            _avatarTemplateSkin = null;
            _avatarTemplateBody = null;
            _avatarTemplateHands = null;
            _avatarTemplateLegs = null;
            AvatarTemplateCandidateCount = 0;
            try
            {
                if (local == null || local.Body == null) return null;
                var useOld = BodyIsOldModelField != null && (bool)BodyIsOldModelField.GetValue(local.Body);
                var root = GetCharacterRoot(local.Body, useOld);
                if (CountRenderableAvatarMeshes(root) > 0)
                {
                    _resolvedAvatarBackend = ThirdPersonAvatarBackend.MirroredNetworkPresentation;
                    _avatarTemplateSkin = PlayerSkinField != null ? PlayerSkinField.GetValue(local) as PlayerSkin : null;
                    _avatarTemplateBody = local.Body;
                    _avatarTemplateHands = local.Hands;
                    _avatarTemplateLegs = local.Legs;
                    return root;
                }

                // Player.InitializePlayer destroys the owner's remote/world presentation. The
                // FishNet player prefab remains loaded, so use that inert asset as the visual
                // template and apply the owner's retained PlayerSkin SyncVars to the copy.
                var bodies = Resources.FindObjectsOfTypeAll<PlayerBody>();
                AvatarTemplateCandidateCount = bodies != null ? bodies.Length : 0;
                GameObject bestRoot = null;
                PlayerSkin bestSkin = null;
                PlayerBody bestBody = null;
                var bestScore = int.MinValue;
                if (bodies != null)
                {
                    for (var i = 0; i < bodies.Length; i++)
                    {
                        var body = bodies[i];
                        if (body == null || body == local.Body) continue;
                        var candidate = GetCharacterRoot(body, useOld);
                        var renderable = CountRenderableAvatarMeshes(candidate);
                        if (candidate == null || renderable == 0) continue;
                        var isPrefabAsset = !body.gameObject.scene.IsValid();
                        var score = renderable * 10 + (isPrefabAsset ? 100000 : 1000);
                        if (score <= bestScore) continue;
                        bestScore = score;
                        bestRoot = candidate;
                        bestSkin = body.GetComponentInParent<PlayerSkin>(true);
                        bestBody = body;
                    }
                }
                if (bestRoot != null)
                {
                    _resolvedAvatarBackend = ThirdPersonAvatarBackend.LoadedPlayerTemplate;
                    _avatarTemplateSkin = bestSkin;
                    _avatarTemplateBody = bestBody;
                    _avatarTemplateHands = bestBody != null ? bestBody.GetComponent<PlayerHands>() : null;
                    _avatarTemplateLegs = bestBody != null ? bestBody.GetComponent<PlayerLegs>() : null;
                    return bestRoot;
                }

                // Last resort: the owner body still contains first-person-safe render data in
                // some game builds even though both network character fields are destroyed.
                var bodyRoot = local.Body.gameObject;
                if (CountRenderableAvatarMeshes(bodyRoot) > 0)
                {
                    _resolvedAvatarBackend = ThirdPersonAvatarBackend.LocalBodyFallback;
                    _avatarTemplateSkin = PlayerSkinField != null ? PlayerSkinField.GetValue(local) as PlayerSkin : null;
                    _avatarTemplateBody = local.Body;
                    _avatarTemplateHands = local.Hands;
                    _avatarTemplateLegs = local.Legs;
                    return bodyRoot;
                }
                return null;
            }
            catch { return null; }
        }

        private static GameObject GetCharacterRoot(PlayerBody body, bool useOld)
        {
            if (body == null) return null;
            try
            {
                var preferred = useOld ? BodyOldCharacterField : BodyNewCharacterField;
                var fallback = useOld ? BodyNewCharacterField : BodyOldCharacterField;
                var root = preferred != null ? preferred.GetValue(body) as GameObject : null;
                if (root == null && fallback != null) root = fallback.GetValue(body) as GameObject;
                return root;
            }
            catch { return null; }
        }

        private static int CountRenderableAvatarMeshes(GameObject root)
        {
            if (root == null) return 0;
            try
            {
                var renderers = root.GetComponentsInChildren<Renderer>(true);
                var count = 0;
                for (var i = 0; i < renderers.Length; i++)
                {
                    var renderer = renderers[i];
                    if (renderer == null) continue;
                    var skinned = renderer as SkinnedMeshRenderer;
                    if (skinned != null && skinned.sharedMesh != null) { count++; continue; }
                    var filter = renderer.GetComponent<MeshFilter>();
                    if (renderer is MeshRenderer && filter != null && filter.sharedMesh != null) count++;
                }
                return count;
            }
            catch { return 0; }
        }

        private void BuildAvatarMirror(Player local, int reason)
        {
            DestroyAvatarMirror(reason);
            _avatarMirrorState = AvatarMirrorState.Building;
            AvatarRebuildReason = reason;
            var sourceRoot = ResolveAvatarSourceRoot(local);
            if (sourceRoot == null)
            {
                _avatarMirrorState = AvatarMirrorState.NoSource;
                _avatarNextSourceSearchAt = Time.unscaledTime + 1f;
                LastErrorCode = 611;
                return;
            }
            try
            {
                _avatarSourceRoot = sourceRoot;
                AvatarSourceRootId = sourceRoot.GetInstanceID();
                var sourceRenderers = sourceRoot.GetComponentsInChildren<Renderer>(true);
                _avatarSourceRendererCount = sourceRenderers.Length;
                _avatarVisualSignature = CalculateAvatarVisualSignature(sourceRenderers);
                var held = local.Holding != null ? local.Holding.HeldItem : null;
                _avatarHeldItemId = held != null ? held.GetInstanceID() : 0;

                _avatarMirrorRoot = new GameObject("HowToFishTrainer.AvatarMirror");
                _avatarMirrorRoot.transform.SetParent(transform, false);
                _avatarMirrorRoot.SetActive(false);
                _avatarTransformMap.Clear();
                _avatarTransforms.Clear();
                _avatarSkinnedRenderers.Clear();
                _avatarIkBindings.Clear();
                _avatarSourceBones.Clear();
                _avatarHeadMirror = null;
                _avatarModelRoot = CreateAvatarTransformHierarchy(sourceRoot.transform, _avatarMirrorRoot.transform, true);
                if (_avatarModelRoot == null) throw new InvalidOperationException("avatar transform hierarchy");

                var renderCount = 0;
                for (var i = 0; i < sourceRenderers.Length; i++)
                {
                    var sourceRenderer = sourceRenderers[i];
                    if (sourceRenderer == null) continue;
                    Transform mirrorTransform;
                    if (!_avatarTransformMap.TryGetValue(sourceRenderer.transform, out mirrorTransform) || mirrorTransform == null) continue;
                    if (CopyAvatarRenderer(sourceRenderer, mirrorTransform.gameObject)) renderCount++;
                }
                BuildAvatarIkRig(sourceRoot);
                AvatarBoneCount = _avatarSourceBones.Count;
                if (renderCount == 0)
                {
                    DestroyAvatarMirror(reason);
                    _avatarMirrorState = AvatarMirrorState.NoRenderableContent;
                    LastErrorCode = 612;
                    return;
                }
                if (!BindNativeAvatarControllers(local))
                {
                    DestroyAvatarMirror(reason);
                    _avatarMirrorState = AvatarMirrorState.Failed;
                    _avatarNextSourceSearchAt = Time.unscaledTime + 1f;
                    LastErrorCode = 614;
                    return;
                }
                ApplyLocalAvatarAppearance(local);
                foreach (var pair in _localBodyRendererStates)
                {
                    try { if (pair.Key != null) { pair.Key.enabled = false; pair.Key.forceRenderingOff = true; } } catch { }
                }
                _avatarMirrorRoot.SetActive(true);
                _thirdPersonAvatarBackend = _resolvedAvatarBackend;
                _avatarMirrorState = AvatarMirrorState.Active;
                _avatarNextSourceSearchAt = 0f;
                LastErrorCode = 0;
                SyncAvatarMirror(local);
            }
            catch
            {
                DestroyAvatarMirror(reason);
                _avatarMirrorState = AvatarMirrorState.Failed;
                LastErrorCode = 613;
            }
        }

        private Transform CreateAvatarTransformHierarchy(Transform source, Transform parent, bool isRoot)
        {
            if (source == null || parent == null) return null;
            var mirrorObject = new GameObject(source.name);
            // Player presentation prefabs commonly live on an owner-hidden layer. The mirror
            // contains render data only, so Default is the safest camera-visible layer.
            mirrorObject.layer = 0;
            var mirror = mirrorObject.transform;
            mirror.SetParent(parent, false);
            var localPosition = source.localPosition;
            if (isRoot && (!IsFinite(localPosition) || localPosition.sqrMagnitude > 25f)) localPosition = Vector3.zero;
            mirror.localPosition = localPosition;
            mirror.localRotation = source.localRotation;
            mirror.localScale = source.localScale;
            _avatarTransformMap[source] = mirror;
            _avatarTransforms.Add(new AvatarTransformBinding { Source = source, Mirror = mirror });
            var lowered = source.name != null ? source.name.ToLowerInvariant() : string.Empty;
            if (_avatarHeadMirror == null && (lowered == "head" || lowered.Contains("head"))) _avatarHeadMirror = mirror;
            for (var i = 0; i < source.childCount; i++) CreateAvatarTransformHierarchy(source.GetChild(i), mirror, false);
            return mirror;
        }

        private bool CopyAvatarRenderer(Renderer source, GameObject destination)
        {
            var sourceSkinned = source as SkinnedMeshRenderer;
            if (sourceSkinned != null)
            {
                if (sourceSkinned.sharedMesh == null) return false;
                var mirror = destination.AddComponent<SkinnedMeshRenderer>();
                mirror.sharedMesh = sourceSkinned.sharedMesh;
                mirror.sharedMaterials = sourceSkinned.sharedMaterials;
                mirror.localBounds = sourceSkinned.localBounds;
                mirror.quality = sourceSkinned.quality;
                mirror.updateWhenOffscreen = true;
                mirror.shadowCastingMode = sourceSkinned.shadowCastingMode == ShadowCastingMode.ShadowsOnly ? ShadowCastingMode.On : sourceSkinned.shadowCastingMode;
                mirror.receiveShadows = sourceSkinned.receiveShadows;
                var sourceBones = sourceSkinned.bones;
                var mirrorBones = new Transform[sourceBones.Length];
                for (var i = 0; i < sourceBones.Length; i++)
                {
                    Transform mapped;
                    mirrorBones[i] = sourceBones[i] != null && _avatarTransformMap.TryGetValue(sourceBones[i], out mapped) ? mapped : null;
                    if (sourceBones[i] != null) _avatarSourceBones.Add(sourceBones[i]);
                }
                mirror.bones = mirrorBones;
                Transform mirrorRootBone;
                if (sourceSkinned.rootBone != null && _avatarTransformMap.TryGetValue(sourceSkinned.rootBone, out mirrorRootBone)) mirror.rootBone = mirrorRootBone;
                var blendShapeCount = sourceSkinned.sharedMesh.blendShapeCount;
                for (var i = 0; i < blendShapeCount; i++) mirror.SetBlendShapeWeight(i, sourceSkinned.GetBlendShapeWeight(i));
                mirror.enabled = true;
                mirror.forceRenderingOff = false;
                _avatarSkinnedRenderers.Add(mirror);
                AvatarSkinnedMeshCount++;
                return true;
            }
            var sourceMesh = source as MeshRenderer;
            if (sourceMesh != null)
            {
                var sourceFilter = source.GetComponent<MeshFilter>();
                if (sourceFilter == null || sourceFilter.sharedMesh == null) return false;
                destination.AddComponent<MeshFilter>().sharedMesh = sourceFilter.sharedMesh;
                var mirror = destination.AddComponent<MeshRenderer>();
                mirror.sharedMaterials = sourceMesh.sharedMaterials;
                mirror.shadowCastingMode = sourceMesh.shadowCastingMode == ShadowCastingMode.ShadowsOnly ? ShadowCastingMode.On : sourceMesh.shadowCastingMode;
                mirror.receiveShadows = sourceMesh.receiveShadows;
                mirror.enabled = true;
                mirror.forceRenderingOff = false;
                AvatarMeshCount++;
                return true;
            }
            return false;
        }

        private void BuildAvatarIkRig(GameObject sourceRoot)
        {
            AvatarIkCount = 0;
            AvatarAnimationState = 1;
            if (sourceRoot == null || _avatarMirrorRoot == null) return;
            // The game method is ResolveIK(bool), not the zero-argument signature used by
            // post7. The external gate and this managed reflection check both validate the
            // real contract before any copied solver is allowed to render.
            if (IkResolveMethod == null) { AvatarAnimationState = -3; return; }
            var sourceSolvers = sourceRoot.GetComponentsInChildren<IK>(true);
            for (var i = 0; i < sourceSolvers.Length; i++)
            {
                var sourceSolver = sourceSolvers[i];
                Transform mirrorBone;
                if (sourceSolver == null || !_avatarTransformMap.TryGetValue(sourceSolver.transform, out mirrorBone) || mirrorBone == null) continue;
                var target = CreateAvatarIkProxy(sourceSolver.Target, sourceRoot.transform, "Target");
                var sourcePole = IkPoleField != null ? IkPoleField.GetValue(sourceSolver) as Transform : null;
                var pole = CreateAvatarIkProxy(sourcePole, sourceRoot.transform, "Pole");
                if (target == null) continue;
                var solver = mirrorBone.gameObject.AddComponent<IK>();
                solver.Target = target;
                CopyAvatarIkField(IkTargetOffsetField, sourceSolver, solver);
                CopyAvatarIkField(IkChainLengthField, sourceSolver, solver);
                CopyAvatarIkField(IkEnableStretchField, sourceSolver, solver);
                CopyAvatarIkField(IkIterationsField, sourceSolver, solver);
                CopyAvatarIkField(IkDeltaField, sourceSolver, solver);
                CopyAvatarIkField(IkSnapBackField, sourceSolver, solver);
                CopyAvatarIkField(IkStopResolvingField, sourceSolver, solver);
                if (IkPoleField != null) IkPoleField.SetValue(solver, pole);
                if (IkInitMethod != null) IkInitMethod.Invoke(solver, null);
                var lowered = (sourceSolver.transform.name ?? string.Empty).ToLowerInvariant();
                _avatarIkBindings.Add(new AvatarIkBinding
                {
                    Solver = solver,
                    Target = target,
                    Pole = pole,
                    DefaultTargetLocalPosition = target.localPosition,
                    DefaultTargetLocalRotation = target.localRotation,
                    DefaultPoleLocalPosition = pole != null ? pole.localPosition : Vector3.zero,
                    DefaultPoleLocalRotation = pole != null ? pole.localRotation : Quaternion.identity,
                    IsHand = lowered.Contains("hand"),
                    IsFoot = lowered.Contains("foot"),
                    IsLeft = lowered.EndsWith("_l") || lowered.Contains("left")
                });
                AvatarIkCount++;
            }
            AvatarAnimationState = AvatarIkCount > 0 ? 2 : 1;
        }

        private Transform CreateAvatarIkProxy(Transform source, Transform sourceRoot, string suffix)
        {
            if (source == null || sourceRoot == null || _avatarMirrorRoot == null) return null;
            Transform mapped;
            if (_avatarTransformMap.TryGetValue(source, out mapped) && mapped != null) return mapped;
            var proxy = new GameObject("HTF.Avatar" + suffix + "." + (source.name ?? "Transform")).transform;
            proxy.gameObject.layer = 0;
            proxy.SetParent(_avatarMirrorRoot.transform, false);
            proxy.localPosition = sourceRoot.InverseTransformPoint(source.position);
            proxy.localRotation = Quaternion.Inverse(sourceRoot.rotation) * source.rotation;
            proxy.localScale = Vector3.one;
            _avatarTransformMap[source] = proxy;
            return proxy;
        }

        private static void CopyAvatarIkField(FieldInfo field, IK source, IK destination)
        {
            try { if (field != null && source != null && destination != null) field.SetValue(destination, field.GetValue(source)); } catch { }
        }

        private bool BindNativeAvatarControllers(Player local)
        {
            if (local == null || _avatarMirrorRoot == null || _avatarModelRoot == null) return false;
            _avatarNativeBody = local.Body;
            _avatarNativeHands = local.Hands;
            _avatarNativeLegs = local.Legs;
            _avatarNativeOther = local.Other;
            if (_avatarNativeBody == null || _avatarNativeHands == null || _avatarNativeLegs == null || _avatarNativeOther == null ||
                _avatarTemplateBody == null || _avatarTemplateHands == null || _avatarTemplateLegs == null ||
                BodyAwakeMethod == null || BodyApplyMethod == null || HandsAwakeMethod == null || HandsLateUpdateMethod == null ||
                LegsAwakeMethod == null || LegsUpdateMethod == null || IkResolveMethod == null || IkResolveMethod.GetParameters().Length != 1)
            {
                AvatarAnimationState = -4;
                return false;
            }
            try
            {
                SaveAndDisableAvatarBehaviour(_avatarNativeBody);
                SaveAndDisableAvatarBehaviour(_avatarNativeHands);
                SaveAndDisableAvatarBehaviour(_avatarNativeLegs);
                SaveAndDisableAvatarBehaviour(_avatarNativeOther);

                if (!CopyMappedAvatarFields(_avatarTemplateBody, _avatarNativeBody, new[] { "_lowerBody", "_head", "_eyes", "_oldHead" })) return false;
                if (!CopyMappedAvatarFields(_avatarTemplateHands, _avatarNativeHands, new[]
                {
                    "_handModelRight", "_handBoneRight", "_handModelLeft", "_handBoneLeft",
                    "_fingerTransformsRight", "_fingerTransformsLeft"
                })) return false;
                if (!CopyMappedAvatarFields(_avatarTemplateLegs, _avatarNativeLegs, new[] { "_legTargets", "_ikPoles", "_footModels" })) return false;

                var useOld = BodyIsOldModelField != null && (bool)BodyIsOldModelField.GetValue(local.Body);
                SaveAndSetAvatarField(_avatarNativeBody, useOld ? BodyOldCharacterField : BodyNewCharacterField, _avatarModelRoot.gameObject);
                SaveAndSetAvatarField(_avatarNativeBody, useOld ? BodyNewCharacterField : BodyOldCharacterField, null);

                _avatarCamProxy = new GameObject("HTF.AvatarCamProxy").transform;
                _avatarCamProxy.gameObject.layer = 0;
                _avatarCamProxy.SetParent(_avatarMirrorRoot.transform, false);
                SaveAndSetAvatarField(_avatarNativeOther, OtherTransformField, _avatarMirrorRoot.transform);
                SaveAndSetAvatarField(_avatarNativeOther, OtherCamProxyField, _avatarCamProxy);
                SaveAndSetAvatarField(_avatarNativeOther, OtherVelocityField, Vector3.zero);
                SaveAndSetAvatarField(_avatarNativeOther, OtherFlatVelocityField, Vector3.zero);
                SaveAndSetAvatarField(_avatarNativeOther, OtherFlatLocalVelocityField, Vector3.zero);
                SaveAndSetAvatarField(_avatarNativeOther, OtherVelMagField, 0f);
                SaveAndSetAvatarField(_avatarNativeOther, OtherOnBoatField, false);
                SaveAndSetAvatarField(_avatarNativeOther, OtherGroundedField, true);

                BodyAwakeMethod.Invoke(_avatarNativeBody, null);
                HandsAwakeMethod.Invoke(_avatarNativeHands, null);
                LegsAwakeMethod.Invoke(_avatarNativeLegs, null);
                AvatarAnimationState = 3;
                return true;
            }
            catch
            {
                AvatarAnimationState = -5;
                RestoreNativeAvatarControllers();
                return false;
            }
        }

        private void SaveAndDisableAvatarBehaviour(Behaviour behaviour)
        {
            if (behaviour == null || _avatarBehaviourStates.ContainsKey(behaviour)) return;
            _avatarBehaviourStates[behaviour] = behaviour.enabled;
            behaviour.enabled = false;
        }

        private bool CopyMappedAvatarFields(object source, object destination, string[] names)
        {
            if (source == null || destination == null) return false;
            var copied = 0;
            var flags = BindingFlags.Instance | BindingFlags.Public | BindingFlags.NonPublic;
            for (var i = 0; i < names.Length; i++)
            {
                var sourceField = source.GetType().GetField(names[i], flags);
                var destinationField = destination.GetType().GetField(names[i], flags);
                if (sourceField == null || destinationField == null) continue;
                var mapped = RemapAvatarPresentationValue(sourceField.GetValue(source), sourceField.FieldType);
                if (mapped == null && sourceField.GetValue(source) != null) continue;
                SaveAndSetAvatarField(destination, destinationField, mapped);
                copied++;
            }
            return copied > 0;
        }

        private object RemapAvatarPresentationValue(object value, Type declaredType)
        {
            if (value == null) return null;
            var transform = value as Transform;
            if (transform != null) return GetOrCreateAvatarMappedTransform(transform);
            var gameObject = value as GameObject;
            if (gameObject != null)
            {
                var mapped = GetOrCreateAvatarMappedTransform(gameObject.transform);
                return mapped != null ? mapped.gameObject : null;
            }
            var renderer = value as Renderer;
            if (renderer != null)
            {
                var mapped = GetOrCreateAvatarMappedTransform(renderer.transform);
                return mapped != null ? mapped.GetComponent(renderer.GetType()) : null;
            }
            var array = value as Array;
            if (array != null)
            {
                var elementType = declaredType.GetElementType();
                if (elementType == null) return null;
                var mappedArray = Array.CreateInstance(elementType, array.Length);
                for (var i = 0; i < array.Length; i++)
                {
                    var element = RemapAvatarPresentationValue(array.GetValue(i), elementType);
                    if (array.GetValue(i) != null && element == null) return null;
                    mappedArray.SetValue(element, i);
                }
                return mappedArray;
            }
            return null;
        }

        private Transform GetOrCreateAvatarMappedTransform(Transform source)
        {
            if (source == null || _avatarMirrorRoot == null) return null;
            Transform mapped;
            if (_avatarTransformMap.TryGetValue(source, out mapped) && mapped != null) return mapped;
            var proxy = new GameObject("HTF.NativeRef." + (source.name ?? "Transform")).transform;
            proxy.gameObject.layer = 0;
            proxy.SetParent(_avatarMirrorRoot.transform, false);
            var referenceRoot = _avatarSourceRoot != null ? _avatarSourceRoot.transform : source.root;
            proxy.localPosition = referenceRoot != null ? referenceRoot.InverseTransformPoint(source.position) : source.position;
            proxy.localRotation = referenceRoot != null ? Quaternion.Inverse(referenceRoot.rotation) * source.rotation : source.rotation;
            proxy.localScale = source.lossyScale;
            _avatarTransformMap[source] = proxy;
            return proxy;
        }

        private void SaveAndSetAvatarField(object target, FieldInfo field, object value)
        {
            if (target == null || field == null) return;
            var saved = false;
            for (var i = 0; i < _avatarFieldRestores.Count; i++)
                if (ReferenceEquals(_avatarFieldRestores[i].Target, target) && _avatarFieldRestores[i].Field == field) { saved = true; break; }
            if (!saved) _avatarFieldRestores.Add(new AvatarFieldRestore { Target = target, Field = field, OriginalValue = field.GetValue(target) });
            field.SetValue(target, value);
        }

        private void RestoreNativeAvatarControllers()
        {
            for (var i = _avatarFieldRestores.Count - 1; i >= 0; i--)
            {
                var restore = _avatarFieldRestores[i];
                try { if (restore != null && restore.Target != null && restore.Field != null) restore.Field.SetValue(restore.Target, restore.OriginalValue); } catch { }
            }
            _avatarFieldRestores.Clear();
            foreach (var pair in _avatarBehaviourStates)
            {
                try { if (pair.Key != null) pair.Key.enabled = pair.Value; } catch { }
            }
            _avatarBehaviourStates.Clear();
            _avatarNativeBody = null;
            _avatarNativeHands = null;
            _avatarNativeLegs = null;
            _avatarNativeOther = null;
            _avatarCamProxy = null;
        }

        private void ApplyLocalAvatarAppearance(Player local)
        {
            AvatarAppearanceApplyState = 0;
            if (local == null || PlayerSkinField == null) { AvatarAppearanceApplyState = -1; return; }
            var localSkin = PlayerSkinField.GetValue(local) as PlayerSkin;
            if (localSkin == null) { AvatarAppearanceApplyState = -1; return; }
            if (_avatarTemplateSkin == null || _avatarTemplateSkin == localSkin)
            {
                // A direct/local source already carries the owner's materials.
                AvatarAppearanceApplyState = 1;
                return;
            }
            var fields = new[]
            {
                SkinBodyRendererField, SkinLeftHandRendererField, SkinRightHandRendererField,
                SkinOutfitRendererField, SkinHatRendererField, SkinAccessoryRendererField
            };
            var originals = new object[fields.Length];
            var replaced = 0;
            try
            {
                for (var i = 0; i < fields.Length; i++)
                {
                    var field = fields[i];
                    if (field == null) continue;
                    originals[i] = field.GetValue(localSkin);
                    var sourceRenderer = field.GetValue(_avatarTemplateSkin) as Renderer;
                    Transform mirrorTransform;
                    if (sourceRenderer == null || !_avatarTransformMap.TryGetValue(sourceRenderer.transform, out mirrorTransform) || mirrorTransform == null) continue;
                    var mirrorRenderer = mirrorTransform.GetComponent(sourceRenderer.GetType()) as Renderer;
                    if (mirrorRenderer == null) continue;
                    field.SetValue(localSkin, mirrorRenderer);
                    replaced++;
                }
                if (replaced == 0 || SkinInitializeOtherMethod == null) { AvatarAppearanceApplyState = -2; return; }
                SkinInitializeOtherMethod.Invoke(localSkin, null);
                AvatarAppearanceApplyState = 2;
            }
            catch { AvatarAppearanceApplyState = -3; }
            finally
            {
                for (var i = 0; i < fields.Length; i++)
                {
                    try { if (fields[i] != null) fields[i].SetValue(localSkin, originals[i]); } catch { }
                }
            }
        }

        private void MaintainAvatarMirror(Player local)
        {
            if (_avatarMirrorRoot == null && Time.unscaledTime < _avatarNextSourceSearchAt) return;
            // While the native body controller is rebound, its character field deliberately
            // points at the mirror. Re-running source discovery would therefore select the
            // mirror as its own template and rebuild forever. Keep the immutable prefab
            // source captured at build time; scene/death cleanup invalidates it explicitly.
            var source = _avatarMirrorRoot != null ? _avatarSourceRoot : ResolveAvatarSourceRoot(local);
            var held = local != null && local.Holding != null ? local.Holding.HeldItem : null;
            var heldId = held != null ? held.GetInstanceID() : 0;
            var sourceRenderers = source != null ? source.GetComponentsInChildren<Renderer>(true) : new Renderer[0];
            var rendererCount = sourceRenderers.Length;
            var visualSignature = CalculateAvatarVisualSignature(sourceRenderers);
            if (_avatarMirrorRoot == null || source != _avatarSourceRoot || rendererCount != _avatarSourceRendererCount || heldId != _avatarHeldItemId || visualSignature != _avatarVisualSignature)
            {
                BuildAvatarMirror(local, source != _avatarSourceRoot ? 2 : (heldId != _avatarHeldItemId ? 3 : (visualSignature != _avatarVisualSignature ? 5 : 4)));
                return;
            }
            SyncAvatarMirror(local);
        }

        private static int CalculateAvatarVisualSignature(Renderer[] renderers)
        {
            unchecked
            {
                var signature = 17;
                for (var i = 0; i < renderers.Length; i++)
                {
                    var renderer = renderers[i];
                    if (renderer == null) continue;
                    signature = signature * 31 + renderer.GetInstanceID();
                    var skinned = renderer as SkinnedMeshRenderer;
                    var filter = renderer.GetComponent<MeshFilter>();
                    var mesh = skinned != null ? skinned.sharedMesh : (filter != null ? filter.sharedMesh : null);
                    signature = signature * 31 + (mesh != null ? mesh.GetInstanceID() : 0);
                    var materials = renderer.sharedMaterials;
                    for (var j = 0; j < materials.Length; j++) signature = signature * 31 + (materials[j] != null ? materials[j].GetInstanceID() : 0);
                }
                return signature;
            }
        }

        private void SyncAvatarMirror(Player local)
        {
            if (_avatarMirrorRoot == null || _avatarMirrorState != AvatarMirrorState.Active || local == null) return;
            var localTransform = local.Transform != null ? local.Transform : local.transform;
            if (localTransform == null) return;
            _avatarMirrorRoot.transform.position = localTransform.position;
            _avatarMirrorRoot.transform.rotation = Quaternion.Euler(0f, ResolveMirrorYaw(local, localTransform.eulerAngles.y), 0f);
            _avatarMirrorRoot.transform.localScale = Vector3.one;
            for (var i = 0; i < _avatarTransforms.Count; i++)
            {
                var binding = _avatarTransforms[i];
                if (binding.Source == null || binding.Mirror == null) continue;
                if (binding.Source != _avatarSourceRoot.transform)
                {
                    binding.Mirror.localPosition = binding.Source.localPosition;
                    binding.Mirror.localRotation = binding.Source.localRotation;
                }
                binding.Mirror.localScale = binding.Source.localScale;
            }
            for (var i = 0; i < _avatarSkinnedRenderers.Count; i++)
            {
                var mirror = _avatarSkinnedRenderers[i];
                if (mirror == null || mirror.sharedMesh == null) continue;
                Transform sourceTransform = null;
                for (var j = 0; j < _avatarTransforms.Count; j++)
                    if (_avatarTransforms[j].Mirror == mirror.transform) { sourceTransform = _avatarTransforms[j].Source; break; }
                var sourceRenderer = sourceTransform != null ? sourceTransform.GetComponent<SkinnedMeshRenderer>() : null;
                if (sourceRenderer == null) continue;
                var count = Mathf.Min(mirror.sharedMesh.blendShapeCount, sourceRenderer.sharedMesh != null ? sourceRenderer.sharedMesh.blendShapeCount : 0);
                for (var j = 0; j < count; j++) mirror.SetBlendShapeWeight(j, sourceRenderer.GetBlendShapeWeight(j));
            }
            ApplyNativeAvatarAnimation(local, localTransform);
            ApplyMirrorPose(local);
            UpdateAvatarMirrorBounds(localTransform.position);
        }

        private float ResolveMirrorYaw(Player local, float fallbackYaw)
        {
            var viewYaw = local != null && local.CurCam != null ? local.CurCam.transform.eulerAngles.y : fallbackYaw;
            if (!_privateLobbyConsent || _menuOpen) return fallbackYaw;
            if (_poseMode == PoseMode.HighSpeedSpin) return _poseSpinYaw;
            if (_poseMode == PoseMode.HideHeadBackwards) return Mathf.Repeat(viewYaw + 180f, 360f);
            return fallbackYaw;
        }

        private void ApplyNativeAvatarAnimation(Player local, Transform localTransform)
        {
            if (_avatarMirrorRoot == null || local == null || localTransform == null || _avatarNativeBody == null ||
                _avatarNativeHands == null || _avatarNativeLegs == null || _avatarNativeOther == null) return;
            try
            {
                var velocity = local.Movement != null ? local.Movement.Velocity : Vector3.zero;
                var flatVelocity = new Vector3(velocity.x, 0f, velocity.z);
                var flatLocalVelocity = Quaternion.Inverse(_avatarMirrorRoot.transform.rotation) * flatVelocity;
                var grounded = local.Movement == null || local.Movement.Grounded;
                var onBoat = local.Movement != null && local.Movement.OnBoat;
                if (OtherVelocityField != null) OtherVelocityField.SetValue(_avatarNativeOther, velocity);
                if (OtherFlatVelocityField != null) OtherFlatVelocityField.SetValue(_avatarNativeOther, flatVelocity);
                if (OtherFlatLocalVelocityField != null) OtherFlatLocalVelocityField.SetValue(_avatarNativeOther, flatLocalVelocity);
                if (OtherVelMagField != null) OtherVelMagField.SetValue(_avatarNativeOther, flatVelocity.magnitude);
                if (OtherOnBoatField != null) OtherOnBoatField.SetValue(_avatarNativeOther, onBoat);
                if (OtherGroundedField != null) OtherGroundedField.SetValue(_avatarNativeOther, grounded);
                if (_avatarCamProxy != null)
                {
                    var cameraTransform = local.CurCam != null ? local.CurCam.transform : localTransform;
                    _avatarCamProxy.position = cameraTransform.position;
                    _avatarCamProxy.rotation = cameraTransform.rotation;
                }

                // This is the game's own remote-avatar order. It consumes the real local
                // movement, held item, camera, breathing and world raycast data; no sine
                // gait, position accumulation or invented animation state is used here.
                LegsUpdateMethod.Invoke(_avatarNativeLegs, null);
                AvatarNativeStage = 1;
                HandsLateUpdateMethod.Invoke(_avatarNativeHands, null);
                AvatarNativeStage = 2;
                BodyApplyMethod.Invoke(_avatarNativeBody, null);
                AvatarNativeStage = 3;
                var solved = 0;
                for (var i = 0; i < _avatarIkBindings.Count; i++)
                {
                    var binding = _avatarIkBindings[i];
                    if (binding == null || binding.Solver == null || binding.Target == null) continue;
                    IkResolveMethod.Invoke(binding.Solver, new object[] { false });
                    solved++;
                }
                AvatarNativeStage = 4;
                AvatarAnimationFrameCount++;
                AvatarAnimationState = solved == _avatarIkBindings.Count && solved > 0 ? 4 : 3;
            }
            catch
            {
                AvatarAnimationState = -6;
                AvatarNativeFailureCount++;
                LastErrorCode = 615;
                _avatarMirrorState = AvatarMirrorState.Failed;
                try { _avatarMirrorRoot.SetActive(false); } catch { }
            }
        }

        private void ApplyMirrorPose(Player local)
        {
            if (_avatarMirrorRoot == null || (_poseMode == PoseMode.Off && !_poseLookDown) || !_privateLobbyConsent || _menuOpen) return;
            var view = local.CurCam != null ? local.CurCam.transform.eulerAngles : _avatarMirrorRoot.transform.eulerAngles;
            var sentYaw = ResolveMirrorYaw(local, _avatarMirrorRoot.transform.eulerAngles.y);
            if (_avatarHeadMirror != null) _avatarHeadMirror.rotation = Quaternion.Euler(_poseLookDown ? 89f : view.x, sentYaw, 0f);
        }

        private void UpdateAvatarMirrorBounds(Vector3 playerPosition)
        {
            AvatarBoundsDistanceMm = -1;
            if (_avatarMirrorRoot == null) return;
            var renderers = _avatarMirrorRoot.GetComponentsInChildren<Renderer>(true);
            var found = false;
            var bounds = new Bounds();
            for (var i = 0; i < renderers.Length; i++)
            {
                if (renderers[i] == null || !renderers[i].enabled) continue;
                if (!found) { bounds = renderers[i].bounds; found = true; }
                else bounds.Encapsulate(renderers[i].bounds);
            }
            if (found && IsFinite(bounds.center)) AvatarBoundsDistanceMm = Mathf.RoundToInt(Vector3.Distance(playerPosition, bounds.center) * 1000f);
        }

        private void DestroyAvatarMirror(int reason)
        {
            RestoreNativeAvatarControllers();
            if (_avatarMirrorRoot != null)
            {
                try { _avatarMirrorRoot.SetActive(false); UnityEngine.Object.Destroy(_avatarMirrorRoot); } catch { }
            }
            _avatarMirrorRoot = null;
            _avatarSourceRoot = null;
            _avatarTemplateSkin = null;
            _avatarTemplateBody = null;
            _avatarTemplateHands = null;
            _avatarTemplateLegs = null;
            _avatarHeadMirror = null;
            _avatarModelRoot = null;
            _avatarTransforms.Clear();
            _avatarTransformMap.Clear();
            _avatarSkinnedRenderers.Clear();
            _avatarIkBindings.Clear();
            _avatarSourceBones.Clear();
            _thirdPersonAvatarBackend = ThirdPersonAvatarBackend.None;
            _resolvedAvatarBackend = ThirdPersonAvatarBackend.None;
            _avatarMirrorState = AvatarMirrorState.Off;
            AvatarSourceRootId = 0;
            AvatarMeshCount = 0;
            AvatarSkinnedMeshCount = 0;
            AvatarBoneCount = 0;
            AvatarBoundsDistanceMm = -1;
            AvatarAppearanceApplyState = 0;
            AvatarIkCount = 0;
            AvatarAnimationState = 0;
            AvatarAnimationFrameCount = 0;
            AvatarNativeStage = 0;
            AvatarNativeFailureCount = 0;
            _avatarSourceRendererCount = 0;
            _avatarHeldItemId = 0;
            _avatarVisualSignature = 0;
            if (reason != 0) AvatarRebuildReason = reason;
        }

        private void MaintainLocalBodyVisibility()
        {
            if (_avatarMirrorState == AvatarMirrorState.Active && _avatarMirrorRoot != null)
            {
                foreach (var pair in _localBodyRendererStates)
                {
                    try { if (pair.Key != null) { pair.Key.enabled = false; pair.Key.forceRenderingOff = true; } } catch { }
                }
                foreach (var pair in _localArmRendererStates) try { if (pair.Key != null) pair.Key.enabled = false; } catch { }
                var mirrorRenderers = _avatarMirrorRoot.GetComponentsInChildren<Renderer>(true);
                var visible = 0;
                for (var i = 0; i < mirrorRenderers.Length; i++) if (mirrorRenderers[i] != null && mirrorRenderers[i].enabled && mirrorRenderers[i].gameObject.activeInHierarchy) visible++;
                ThirdPersonBodyRendererCount = mirrorRenderers.Length;
                ThirdPersonBodyVisibleCount = visible;
                return;
            }
            var rendererCount = 0;
            var visibleCount = 0;
            foreach (var pair in _localBodyObjectStates)
            {
                try { if (pair.Key != null && !pair.Key.activeSelf) pair.Key.SetActive(true); } catch { }
            }
            foreach (var pair in _localBodyRendererStates)
            {
                try
                {
                    if (pair.Key == null) continue;
                    rendererCount++;
                    pair.Key.enabled = true;
                    pair.Key.forceRenderingOff = false;
                    if (pair.Key.gameObject.activeInHierarchy) visibleCount++;
                }
                catch { }
            }
            foreach (var pair in _localArmRendererStates)
            {
                try { if (pair.Key != null) pair.Key.enabled = false; } catch { }
            }
            ThirdPersonBodyRendererCount = rendererCount;
            ThirdPersonBodyVisibleCount = visibleCount;
        }

        private static int GetLocalBodyLayerMask(Player local)
        {
            var mask = 0;
            try
            {
                if (local.Body == null) return mask;
                var renderers = local.Body.GetComponentsInChildren<Renderer>(true);
                for (var i = 0; i < renderers.Length; i++)
                    if (renderers[i] != null) mask |= 1 << renderers[i].gameObject.layer;
            }
            catch { }
            return mask;
        }

        private void UpdateThirdPersonCrosshair()
        {
            try
            {
                if (_sniperUi == null)
                {
                    var playerUis = Resources.FindObjectsOfTypeAll<PlayerUI>();
                    for (var i = 0; i < playerUis.Length && _sniperUi == null; i++)
                    {
                        var weaponUi = playerUis[i] != null && PlayerUiWeaponField != null ? PlayerUiWeaponField.GetValue(playerUis[i]) as WeaponUI : null;
                        if (weaponUi != null && SniperUiField != null) _sniperUi = SniperUiField.GetValue(weaponUi) as CanvasGroup;
                    }
                }
                if (_sniperUi == null) return;
                if (!_sniperUiSaved)
                {
                    _savedSniperAlpha = _sniperUi.alpha; _savedSniperInteractable = _sniperUi.interactable; _savedSniperBlocksRaycasts = _sniperUi.blocksRaycasts; _sniperUiSaved = true;
                }
                if (!_thirdPersonCrosshair) { _sniperUi.alpha = 0f; _sniperUi.interactable = false; _sniperUi.blocksRaycasts = false; }
                else { _sniperUi.alpha = _savedSniperAlpha; _sniperUi.interactable = _savedSniperInteractable; _sniperUi.blocksRaycasts = _savedSniperBlocksRaycasts; }
            }
            catch { }
        }

        private void InstallRenderCallbacks()
        {
            if (_renderCallbacksInstalled) return;
            RenderPipelineManager.beginCameraRendering += OnBeginCameraRendering;
            RenderPipelineManager.endCameraRendering += OnEndCameraRendering;
            Camera.onPreCull += OnBuiltinCameraPreCull;
            Camera.onPostRender += OnBuiltinCameraPostRender;
            _renderCallbacksInstalled = true;
        }

        private void RemoveRenderCallbacks()
        {
            if (!_renderCallbacksInstalled) return;
            RenderPipelineManager.beginCameraRendering -= OnBeginCameraRendering;
            RenderPipelineManager.endCameraRendering -= OnEndCameraRendering;
            Camera.onPreCull -= OnBuiltinCameraPreCull;
            Camera.onPostRender -= OnBuiltinCameraPostRender;
            _renderCallbacksInstalled = false;
        }

        private void OnBeginCameraRendering(ScriptableRenderContext context, Camera camera)
        {
            HandleCameraBeforeRender(camera);
        }

        private void OnEndCameraRendering(ScriptableRenderContext context, Camera camera)
        {
            HandleCameraAfterRender(camera);
        }

        private void OnBuiltinCameraPreCull(Camera camera)
        {
            HandleCameraBeforeRender(camera);
        }

        private void OnBuiltinCameraPostRender(Camera camera)
        {
            HandleCameraAfterRender(camera);
        }

        private void HandleCameraBeforeRender(Camera camera)
        {
            if (!_thirdPersonEnabled || !_thirdPersonSaved || camera == null) return;
            if (_thirdPersonBackend == ThirdPersonBackend.NativeObserverCamera)
            {
                if (camera == _thirdPersonObserverCamera)
                {
                    SyncAvatarMirror(_thirdPersonPlayer);
                    MaintainLocalBodyVisibility();
                    ThirdPersonRenderCount++;
                    ThirdPersonAppliedDistanceMm = _thirdPersonSourceCamera != null
                        ? Mathf.RoundToInt(Vector3.Distance(_thirdPersonSourceCamera.transform.position, camera.transform.position) * 1000f)
                        : 0;
                    ThirdPersonState = 2;
                }
                return;
            }
            if (_thirdPersonBackend != ThirdPersonBackend.RenderCallback || camera != _thirdPersonSourceCamera || !_thirdPersonSnapshotValid || _renderOverrideApplied) return;
            SyncAvatarMirror(_thirdPersonPlayer);
            MaintainLocalBodyVisibility();
            _renderSavedPosition = camera.transform.position;
            _renderSavedRotation = camera.transform.rotation;
            var actualDisplacement = Vector3.Distance(_renderSavedPosition, _thirdPersonDesiredPosition);
            if (!IsFinite(_renderSavedPosition) || actualDisplacement > 12f)
            {
                _thirdPersonSnapshotValid = false;
                ThirdPersonAppliedDistanceMm = Mathf.RoundToInt(actualDisplacement * 1000f);
                ThirdPersonState = -10;
                LastErrorCode = 610;
                return;
            }
            camera.transform.position = _thirdPersonDesiredPosition;
            camera.transform.rotation = _thirdPersonDesiredRotation;
            _renderOverrideApplied = true;
            ThirdPersonRenderCount++;
            ThirdPersonAppliedDistanceMm = Mathf.RoundToInt(actualDisplacement * 1000f);
            ThirdPersonState = 1;
        }

        private void HandleCameraAfterRender(Camera camera)
        {
            if (_renderOverrideApplied && camera == _thirdPersonSourceCamera) RestoreRenderOverride();
        }

        private void RestoreRenderOverride()
        {
            if (!_renderOverrideApplied) return;
            try
            {
                if (_thirdPersonSourceCamera != null)
                {
                    _thirdPersonSourceCamera.transform.position = _renderSavedPosition;
                    _thirdPersonSourceCamera.transform.rotation = _renderSavedRotation;
                }
            }
            catch { }
            _renderOverrideApplied = false;
        }

        private bool TryActivateNativeObserver(Player local)
        {
            try
            {
                RestoreRenderOverride();
                var deathController = local != null ? local.DeathCam : null;
                var observer = deathController != null && DeathCameraField != null ? DeathCameraField.GetValue(deathController) as Camera : null;
                if (observer == null || observer == _thirdPersonSourceCamera) return false;
                _thirdPersonObserverCamera = observer;
                _savedObserverActive = observer.gameObject.activeSelf;
                _savedObserverEnabled = observer.enabled;
                _savedObserverCullingMask = observer.cullingMask;
                _savedObserverNearClip = observer.nearClipPlane;
                _savedObserverFov = observer.fieldOfView;
                _observerSavedPosition = observer.transform.position;
                _observerSavedRotation = observer.transform.rotation;
                observer.transform.position = _thirdPersonDesiredPosition;
                observer.transform.rotation = _thirdPersonDesiredRotation;
                observer.gameObject.SetActive(true);
                observer.enabled = true;
                observer.cullingMask = _savedSourceCullingMask | GetLocalBodyLayerMask(local);
                observer.nearClipPlane = Mathf.Min(_savedSourceNearClip, 0.05f);
                observer.fieldOfView = _thirdPersonSourceCamera.fieldOfView;
                _thirdPersonSourceCamera.enabled = false;
                local.SetCurCam(observer);
                if (local.CurCam != observer)
                {
                    return false;
                }
                _thirdPersonBackend = ThirdPersonBackend.NativeObserverCamera;
                _thirdPersonWaitFrames = 0;
                _thirdPersonLastObservedRenderCount = ThirdPersonRenderCount;
                ThirdPersonState = 11;
                return true;
            }
            catch
            {
                LastErrorCode = 608;
                return false;
            }
        }

        private void RestoreThirdPerson(int reason = 0, bool preserveNativeObserverForDeath = false)
        {
            RestoreRenderOverride();
            DestroyAvatarMirror(reason);
            if (_thirdPersonSaved)
            {
                try
                {
                    if (_thirdPersonSourceCamera != null)
                    {
                        _thirdPersonSourceCamera.cullingMask = _savedSourceCullingMask;
                        _thirdPersonSourceCamera.nearClipPlane = _savedSourceNearClip;
                        _thirdPersonSourceCamera.enabled = _savedSourceCameraEnabled;
                    }
                    if (_thirdPersonObserverCamera != null)
                    {
                        _thirdPersonObserverCamera.cullingMask = _savedObserverCullingMask;
                        _thirdPersonObserverCamera.nearClipPlane = _savedObserverNearClip;
                        _thirdPersonObserverCamera.fieldOfView = _savedObserverFov;
                        if (!preserveNativeObserverForDeath)
                        {
                            if (_thirdPersonPlayer != null && _thirdPersonSourceCamera != null) _thirdPersonPlayer.SetCurCam(_thirdPersonSourceCamera);
                            _thirdPersonObserverCamera.transform.position = _observerSavedPosition;
                            _thirdPersonObserverCamera.transform.rotation = _observerSavedRotation;
                            _thirdPersonObserverCamera.enabled = _savedObserverEnabled;
                            _thirdPersonObserverCamera.gameObject.SetActive(_savedObserverActive);
                        }
                    }
                }
                catch { }
            }
            foreach (var pair in _localArmRendererStates) try { if (pair.Key != null) pair.Key.enabled = pair.Value; } catch { }
            foreach (var pair in _localBodyForceRenderingStates) try { if (pair.Key != null) pair.Key.forceRenderingOff = pair.Value; } catch { }
            foreach (var pair in _localBodyRendererStates) try { if (pair.Key != null) pair.Key.enabled = pair.Value; } catch { }
            foreach (var pair in _localBodyObjectStates) try { if (pair.Key != null) pair.Key.SetActive(pair.Value); } catch { }
            _localArmRendererStates.Clear();
            _localBodyForceRenderingStates.Clear();
            _localBodyRendererStates.Clear();
            _localBodyObjectStates.Clear();
            if (_sniperUiSaved && _sniperUi != null)
            {
                try { _sniperUi.alpha = _savedSniperAlpha; _sniperUi.interactable = _savedSniperInteractable; _sniperUi.blocksRaycasts = _savedSniperBlocksRaycasts; } catch { }
            }
            _sniperUiSaved = false;
            _sniperUi = null;
            _thirdPersonPlayer = null;
            _thirdPersonSourceCamera = null;
            _thirdPersonSourceCameraId = 0;
            _thirdPersonObserverCamera = null;
            _thirdPersonBackend = ThirdPersonBackend.None;
            _thirdPersonSnapshotValid = false;
            _thirdPersonWaitFrames = 0;
            _thirdPersonLastObservedRenderCount = ThirdPersonRenderCount;
            ThirdPersonRequestedDistanceMm = 0;
            ThirdPersonCollisionDistanceMm = 0;
            ThirdPersonAppliedDistanceMm = 0;
            ThirdPersonHeadOffsetMm = -1;
            ThirdPersonBodyRendererCount = 0;
            ThirdPersonBodyVisibleCount = 0;
            if (reason != 0) ThirdPersonRestoreReason = reason;
            _thirdPersonSaved = false;
        }

        private void UpdateTrackedProjectiles()
        {
            if (!_silentAimEnabled || _menuOpen)
            {
                _projectileTracking.Clear();
                _ignoredExistingProjectiles.Clear();
                _silentTrackingWasActive = false;
                if (!_silentAimEnabled) SilentAimState = 0;
                return;
            }
            try
            {
                var local = Player.LocalPlayer;
                if (local == null || (!local.IsServerInitialized && !_privateLobbyConsent)) { _projectileTracking.Clear(); _ignoredExistingProjectiles.Clear(); _silentTrackingWasActive = false; SilentAimState = -1; return; }
                var manager = ProjectileManager.Instance;
                var outer = manager != null && PlayerProjectilesField != null ? PlayerProjectilesField.GetValue(manager) as IDictionary : null;
                if (outer == null) { _projectileTracking.Clear(); _ignoredExistingProjectiles.Clear(); _silentTrackingWasActive = false; SilentAimState = -4; return; }
                _projectilesSeen.Clear();
                if (!_silentTrackingWasActive)
                {
                    foreach (DictionaryEntry outerEntry in outer)
                    {
                        var existing = outerEntry.Value as IDictionary; if (existing == null) continue;
                        foreach (DictionaryEntry existingEntry in existing)
                        {
                            var existingProjectile = existingEntry.Value as Projectile;
                            if (existingProjectile != null && existingProjectile.Owner == local && existingProjectile.IsLocal) _ignoredExistingProjectiles.Add(existingProjectile.Id);
                        }
                    }
                    _silentTrackingWasActive = true;
                }
                foreach (DictionaryEntry outerEntry in outer)
                {
                    var inner = outerEntry.Value as IDictionary; if (inner == null) continue;
                    foreach (DictionaryEntry innerEntry in inner)
                    {
                        var projectile = innerEntry.Value as Projectile;
                        if (projectile == null || projectile.Owner != local || !projectile.IsLocal) continue;
                        var id = projectile.Id; _projectilesSeen.Add(id);
                        if (_ignoredExistingProjectiles.Contains(id)) continue;
                        ProjectileTrackingState state;
                        if (!_projectileTracking.TryGetValue(id, out state))
                        {
                            state = new ProjectileTrackingState { Id = id, Target = _lockedTarget, TargetKind = _lockedKind, TargetSpecies = _lockedSpecies, BoundAt = Time.unscaledTime };
                            _projectileTracking[id] = state;
                        }
                        Vector3 targetPosition; Transform targetTransform;
                        if (state.Occluded || state.TrackingStopped || state.Target == null || !IsSpeciesEnabled(state.TargetSpecies) || !TryGetBoundTargetPosition(state.Target, state.TargetKind, out targetPosition, out targetTransform)) continue;
                        if (IsObstructed(projectile.Position, targetPosition, targetTransform)) { state.Occluded = true; continue; }
                        var velocity = projectile.Velocity; var speed = velocity.magnitude; var desired = targetPosition - projectile.Position;
                        if (speed <= 0.001f || desired.sqrMagnitude <= 0.001f || !IsFinite(desired)) continue;
                        var next = !state.InitialCorrected
                            ? desired.normalized * speed
                            : Vector3.RotateTowards(velocity, desired.normalized * speed, 180f * Mathf.Deg2Rad * Time.fixedUnscaledDeltaTime, 0f);
                        projectile.PreviousVelocity = next; projectile.Velocity = next;
                        state.InitialCorrected = true;
                        if (_silentAimMode == SilentAimMode.InitialCorrection) state.TrackingStopped = true;
                    }
                }
                var stale = new List<uint>();
                foreach (var pair in _projectileTracking) if (!_projectilesSeen.Contains(pair.Key)) stale.Add(pair.Key);
                for (var i = 0; i < stale.Count; i++) _projectileTracking.Remove(stale[i]);
                stale.Clear(); foreach (var id in _ignoredExistingProjectiles) if (!_projectilesSeen.Contains(id)) stale.Add(id);
                for (var i = 0; i < stale.Count; i++) _ignoredExistingProjectiles.Remove(stale[i]);
                SilentAimState = _silentAimMode == SilentAimMode.InitialCorrection ? 1 : (local.IsServerInitialized ? 2 : 3);
            }
            catch
            {
                _projectileTracking.Clear(); _ignoredExistingProjectiles.Clear(); _silentTrackingWasActive = false; SilentAimState = -3; _silentAimEnabled = false; Bootstrap.SetSilentAimEnabled(false); LastErrorCode = 604;
            }
        }

        private static bool TryGetBoundTargetPosition(object target, RuntimeTargetKind kind, out Vector3 position, out Transform targetTransform)
        {
            position = Vector3.zero; targetTransform = null;
            if (kind == RuntimeTargetKind.Creature)
            {
                var creature = target as Creature;
                if (creature == null || creature.IsDead) return false;
                targetTransform = creature.transform; position = CreatureHeadPosition(creature); return IsFinite(position);
            }
            if (kind == RuntimeTargetKind.Player)
            {
                var player = target as Player;
                return TryGetPlayerTargetPosition(player, out position, out targetTransform);
            }
            return false;
        }

        private bool FindBestTarget(Camera camera, out object bestTarget, out RuntimeTargetKind bestKind, out AimTargetSpecies bestSpecies, out Vector3 bestPosition, out float bestDistance)
        {
            bestTarget = null; bestKind = RuntimeTargetKind.None; bestSpecies = AimTargetSpecies.None; bestPosition = Vector3.zero; bestDistance = float.MaxValue;
            BirdAliveCandidateCount = 0; BirdFlyingCandidateCount = 0; PlayerCandidateCount = 0;
            _aimCandidateIds.Clear();
            var origin = camera.transform.position;
            var manager = CreatureManager.Instance;
            var creatures = manager != null && AliveCreaturesField != null ? AliveCreaturesField.GetValue(manager) as List<Creature> : null;
            if (creatures != null)
                for (var i = 0; i < creatures.Count; i++)
                {
                    var creature = creatures[i];
                    if (creature == null || creature.IsDead) continue;
                    var id = creature.GetInstanceID();
                    if (id != 0) _aimCandidateIds.Add(id);
                    var species = SpeciesForCreature(creature);
                    if (species == AimTargetSpecies.Bird) BirdAliveCandidateCount++;
                    if (!IsSpeciesEnabled(species)) continue;
                    ConsiderTarget(creature, RuntimeTargetKind.Creature, species, CreatureHeadPosition(creature), creature.transform, origin, ref bestTarget, ref bestKind, ref bestSpecies, ref bestPosition, ref bestDistance);
                }
            var birdManagers = Resources.FindObjectsOfTypeAll<BirdManager>();
            for (var managerIndex = 0; managerIndex < birdManagers.Length; managerIndex++)
            {
                var flying = birdManagers[managerIndex] != null && FlyingBirdsField != null ? FlyingBirdsField.GetValue(birdManagers[managerIndex]) as IList : null;
                if (flying == null) continue;
                for (var i = 0; i < flying.Count; i++)
                {
                    var bird = flying[i] as Creature;
                    if (bird == null || bird.IsDead) continue;
                    BirdFlyingCandidateCount++;
                    var id = bird.GetInstanceID();
                    if (id != 0 && !_aimCandidateIds.Add(id)) continue;
                    if (!IsSpeciesEnabled(AimTargetSpecies.Bird)) continue;
                    ConsiderTarget(bird, RuntimeTargetKind.Creature, AimTargetSpecies.Bird, CreatureHeadPosition(bird), bird.transform, origin, ref bestTarget, ref bestKind, ref bestSpecies, ref bestPosition, ref bestDistance);
                }
            }
            if (_privateLobbyConsent && (_aimTargetMask & AimTargetFlags.Player) != 0)
                for (var i = 0; i < PlayerManager.OtherPlayers.Count; i++)
                {
                    var player = PlayerManager.OtherPlayers[i];
                    if (player == null || player == Player.LocalPlayer || player.Vitals == null || player.Vitals.Health <= 0) continue;
                    Vector3 playerPosition; Transform playerTransform;
                    if (!TryGetPlayerTargetPosition(player, out playerPosition, out playerTransform)) continue;
                    PlayerCandidateCount++;
                    ConsiderTarget(player, RuntimeTargetKind.Player, AimTargetSpecies.Player, playerPosition, playerTransform, origin, ref bestTarget, ref bestKind, ref bestSpecies, ref bestPosition, ref bestDistance);
                }
            return bestTarget != null;
        }

        private void ConsiderTarget(object target, RuntimeTargetKind kind, AimTargetSpecies species, Vector3 position, Transform targetTransform, Vector3 origin, ref object bestTarget, ref RuntimeTargetKind bestKind, ref AimTargetSpecies bestSpecies, ref Vector3 bestPosition, ref float bestDistance)
        {
            if (!IsFinite(position)) return;
            var sample = ObserveTargetMotion(target, position, origin);
            if (_aimTrackingMode == AimTrackingMode.StableFirst && !sample.Stable) return;
            position = sample.FilteredPosition;
            var distance = Vector3.Distance(position, origin);
            if (distance <= 0.01f || distance > _maxAimDistance || distance >= bestDistance) return;
            if (!_ignoreOcclusion && IsObstructed(origin, position, targetTransform)) return;
            bestTarget = target; bestKind = kind; bestSpecies = species; bestPosition = position; bestDistance = distance;
        }

        private bool TryGetLockedTargetPosition(Camera camera, out Vector3 position, out float distance, out bool stable)
        {
            position = Vector3.zero; distance = float.MaxValue; stable = false; Transform targetTransform; Vector3 rawPosition;
            if (_lockedKind == RuntimeTargetKind.Creature)
            {
                var creature = _lockedTarget as Creature;
                if (creature == null || creature.IsDead || !IsSpeciesEnabled(_lockedSpecies)) return false;
                rawPosition = CreatureHeadPosition(creature); targetTransform = creature.transform;
            }
            else if (_lockedKind == RuntimeTargetKind.Player)
            {
                var player = _lockedTarget as Player;
                if (!_privateLobbyConsent || (_aimTargetMask & AimTargetFlags.Player) == 0 || !TryGetPlayerTargetPosition(player, out rawPosition, out targetTransform)) return false;
            }
            else return false;
            if (!IsFinite(rawPosition)) return false;
            var sample = ObserveTargetMotion(_lockedTarget, rawPosition, camera.transform.position);
            position = sample.FilteredPosition; stable = sample.Stable;
            distance = Vector3.Distance(camera.transform.position, position);
            return distance <= _maxAimDistance && (_ignoreOcclusion || !IsObstructed(camera.transform.position, position, targetTransform));
        }

        private AimMotionSample ObserveTargetMotion(object target, Vector3 rawPosition, Vector3 origin)
        {
            var id = TargetInstanceId(target); AimMotionSample sample;
            var now = Time.unscaledTime;
            if (id == 0 || !_aimMotion.TryGetValue(id, out sample) || now - sample.SampledAt > 0.5f)
            {
                sample = new AimMotionSample { RawPosition = rawPosition, FilteredPosition = rawPosition, SampledAt = now, Stable = true, UnstableUntil = now };
                if (id != 0) _aimMotion[id] = sample;
                return sample;
            }
            var dt = now - sample.SampledAt;
            if (dt < 0.015f) return sample;
            var delta = rawPosition - sample.RawPosition;
            sample.Speed = delta.magnitude / dt;
            sample.VerticalSpeed = Mathf.Abs(delta.y) / dt;
            var previousDirection = sample.RawPosition - origin;
            var currentDirection = rawPosition - origin;
            var angularSpeed = previousDirection.sqrMagnitude > 0.001f && currentDirection.sqrMagnitude > 0.001f ? Vector3.Angle(previousDirection, currentDirection) / dt : 0f;
            sample.Stable = delta.magnitude <= AimTeleportDistance && sample.Speed <= AimMaxTargetSpeed && sample.VerticalSpeed <= AimMaxVerticalSpeed && angularSpeed <= AimMaxAngularSpeed;
            if (!sample.Stable) sample.UnstableUntil = now + AimUnstableGrace;
            if (_aimTrackingMode == AimTrackingMode.Continuous)
            {
                var limited = Vector3.MoveTowards(sample.FilteredPosition, rawPosition, ContinuousTargetSpeed * dt);
                sample.FilteredPosition = Vector3.Lerp(sample.FilteredPosition, limited, 1f - Mathf.Exp(-10f * dt));
            }
            else if (sample.Stable)
            {
                sample.FilteredPosition = Vector3.Lerp(sample.FilteredPosition, rawPosition, 1f - Mathf.Exp(-14f * dt));
            }
            sample.RawPosition = rawPosition; sample.SampledAt = now;
            return sample;
        }

        private bool CanHoldUnstableTarget(object target)
        {
            AimMotionSample sample; var id = TargetInstanceId(target);
            return id != 0 && _aimMotion.TryGetValue(id, out sample) && Time.unscaledTime <= sample.UnstableUntil;
        }

        private static int TargetInstanceId(object target)
        {
            var unityObject = target as UnityEngine.Object;
            return unityObject != null ? unityObject.GetInstanceID() : 0;
        }

        private static AimTargetSpecies SpeciesForCreature(Creature creature)
        {
            if (creature is Bird) return AimTargetSpecies.Bird;
            if (creature is Fish) return AimTargetSpecies.Fish;
            return AimTargetSpecies.OtherCreature;
        }

        private bool IsSpeciesEnabled(AimTargetSpecies species)
        {
            if (species == AimTargetSpecies.Fish) return (_aimTargetMask & AimTargetFlags.Fish) != 0;
            if (species == AimTargetSpecies.Bird) return (_aimTargetMask & AimTargetFlags.Bird) != 0;
            if (species == AimTargetSpecies.OtherCreature) return (_aimTargetMask & AimTargetFlags.OtherCreature) != 0;
            if (species == AimTargetSpecies.Player) return _privateLobbyConsent && (_aimTargetMask & AimTargetFlags.Player) != 0;
            return false;
        }

        private static bool TryGetPlayerTargetPosition(Player player, out Vector3 position, out Transform targetTransform)
        {
            position = Vector3.zero; targetTransform = null;
            if (player == null || player.Vitals == null || player.Vitals.Health <= 0) return false;
            try
            {
                if (player.Body != null && player.Body.Head != null && IsFinite(player.Body.Head.position))
                {
                    targetTransform = player.Body.Head;
                    position = targetTransform.position;
                    return true;
                }
                if (player.Body != null)
                {
                    var renderers = player.Body.GetComponentsInChildren<Renderer>(true);
                    var found = false;
                    var bounds = new Bounds();
                    for (var i = 0; i < renderers.Length; i++)
                    {
                        if (renderers[i] == null) continue;
                        if (!found) { bounds = renderers[i].bounds; found = true; }
                        else bounds.Encapsulate(renderers[i].bounds);
                    }
                    if (found && IsFinite(bounds.center))
                    {
                        targetTransform = player.Transform != null ? player.Transform : player.transform;
                        position = bounds.center + Vector3.up * bounds.extents.y * 0.65f;
                        return IsFinite(position);
                    }
                }
                targetTransform = player.Transform != null ? player.Transform : player.transform;
                if (targetTransform == null) return false;
                position = targetTransform.position + Vector3.up * 1.6f;
                return IsFinite(position);
            }
            catch { position = Vector3.zero; targetTransform = null; return false; }
        }

        private static Vector3 CreatureHeadPosition(Creature creature)
        {
            var position = creature.transform.position + creature.transform.up * creature.HeadPos;
            try
            {
                var renderers = creature.GetComponentsInChildren<Renderer>();
                if (renderers.Length > 0)
                {
                    var bounds = renderers[0].bounds;
                    for (var i = 1; i < renderers.Length; i++) if (renderers[i] != null) bounds.Encapsulate(renderers[i].bounds);
                    if ((bounds.ClosestPoint(position) - position).sqrMagnitude > 1f)
                        position = creature is Bird ? bounds.center + Vector3.up * bounds.extents.y * 0.65f : bounds.center;
                }
            }
            catch { }
            return position;
        }

        private static bool IsFinite(Vector3 v)
        {
            return !float.IsNaN(v.x) && !float.IsNaN(v.y) && !float.IsNaN(v.z) && !float.IsInfinity(v.x) && !float.IsInfinity(v.y) && !float.IsInfinity(v.z);
        }

        private static bool IsObstructed(Vector3 origin, Vector3 target, Transform targetTransform)
        {
            RaycastHit hit;
            if (!Physics.Linecast(origin, target, out hit, Physics.DefaultRaycastLayers, QueryTriggerInteraction.Ignore)) return false;
            if (hit.transform == null || targetTransform == null) return true;
            return hit.transform != targetTransform && !hit.transform.IsChildOf(targetTransform) && !targetTransform.IsChildOf(hit.transform);
        }

        private void ClearTarget(bool resetTool)
        {
            _lockedTarget = null; _lockedKind = RuntimeTargetKind.None; _lockedSpecies = AimTargetSpecies.None; _lockedDistance = float.MaxValue; _lockedPosition = Vector3.zero;
        }

        private void RefreshOverlayEntities()
        {
            _overlayEntries.Clear();
            try
            {
                foreach (var pair in ItemManager.Items)
                {
                    var transform = pair.Key; var item = pair.Value;
                    if (transform == null || item == null || item.DeadPlayer != null || item.HasPlayerHolder || item.IsInInventory || !item.gameObject.activeInHierarchy) continue;
                    var kind = OverlayKind.Item;
                    if (item.IsQuestItem) kind = OverlayKind.Quest;
                    else if (item.Explosive != null) kind = OverlayKind.Dangerous;
                    else if (item.Weapon != null) kind = OverlayKind.Weapon;
                    else if (item is Creature || item.Fish != null) kind = OverlayKind.Fish;
                    string name; try { name = item.GetName(); } catch { name = item.name; }
                    _overlayEntries.Add(new OverlayEntry { InstanceId = item.GetInstanceID(), Name = string.IsNullOrEmpty(name) ? item.name : name, Transform = transform, TargetTransform = transform, Item = item, Kind = kind });
                }
                EspCount = _overlayEntries.Count; LastErrorCode = 0;
            }
            catch { LastErrorCode = 201; _overlayEntries.Clear(); EspCount = 0; }
        }

        private void UpdateOverlayProjection()
        {
            try
            {
                var local = Player.LocalPlayer;
                var camera = local != null ? local.CurCam : GameInfo.CurCamera;
                if (camera == null) { EspCount = 0; return; }
                var origin = camera.transform.position;
                for (var i = 0; i < _overlayEntries.Count; i++)
                {
                    var entry = _overlayEntries[i]; entry.Valid = false;
                    if (entry.Transform == null || entry.Item == null || !entry.Item.gameObject.activeInHierarchy) continue;
                    var distance = Vector3.Distance(origin, entry.Transform.position);
                    if (distance > _maxEspDistance) continue;
                    var screen = camera.WorldToScreenPoint(entry.Transform.position);
                    if (screen.z <= 0f) continue;
                    entry.Screen = screen; entry.Distance = distance; entry.Valid = true;
                }
                if (_overlayEntries.Count > 0)
                {
                    var budget = Math.Max(1, (_overlayEntries.Count + 3) / 4);
                    for (var count = 0; count < budget; count++)
                    {
                        if (_occlusionCursor >= _overlayEntries.Count) _occlusionCursor = 0;
                        var entry = _overlayEntries[_occlusionCursor++];
                        if (entry.Valid) entry.Obstructed = IsObstructed(origin, entry.Transform.position, entry.TargetTransform);
                    }
                }
                _overlayEntries.Sort(delegate(OverlayEntry a, OverlayEntry b) { return a.Distance.CompareTo(b.Distance); });
                if (_overlayEntries.Count > _maxLabels) _overlayEntries.RemoveRange(_maxLabels, _overlayEntries.Count - _maxLabels);
                EspCount = 0; for (var i = 0; i < _overlayEntries.Count; i++) if (_overlayEntries[i].Valid) EspCount++;
            }
            catch { LastErrorCode = 202; }
        }

        private void EnsureCatalog()
        {
            try
            {
                var anchor = GameInfo.GetSpawnable((byte)0);
                var next = anchor != null ? anchor.GetInstanceID() : 0;
                if (next == 0 || (next == _catalogAnchor && _catalog.Count != 0)) return;
                _catalogAnchor = next; BuildCatalog();
            }
            catch { LastErrorCode = 401; }
        }

        private void BuildCatalog()
        {
            _catalog.Clear(); var seen = new HashSet<int>();
            for (var id = 0; id <= 255; id++)
            {
                var item = GameInfo.GetSpawnable((byte)id);
                if (item != null) AddNativeEntry(item, id, SpawnCatalogSource.Game, seen);
            }
            try
            {
                var named = NameSpawnablesField != null ? NameSpawnablesField.GetValue(null) as Dictionary<string, Item> : null;
                if (named != null) foreach (var pair in named) AddNativeEntry(pair.Value, pair.Value != null ? pair.Value.ID : -1, SpawnCatalogSource.Named, seen);
            }
            catch { }
            try
            {
                var skins = GameInfo.ItemWithSkinsforCommands;
                if (skins != null) for (var i = 0; i < skins.Length; i++) AddNativeEntry(skins[i], skins[i] != null ? skins[i].ID : -1, SpawnCatalogSource.Named, seen);
                AddNativeEntry(GameInfo.CheatQuestItem, GameInfo.CheatQuestItem != null ? GameInfo.CheatQuestItem.ID : -1, SpawnCatalogSource.Named, seen);
            }
            catch { }
            try
            {
                var resources = Resources.LoadAll<Item>("Items");
                for (var i = 0; i < resources.Length; i++) AddNativeEntry(resources[i], resources[i] != null ? resources[i].ID : -1, SpawnCatalogSource.Resource, seen);
            }
            catch { }
            AddEngineEntries(seen);
            _catalog.Sort(delegate(SpawnCatalogEntry a, SpawnCatalogEntry b)
            {
                var source = a.Source.CompareTo(b.Source); if (source != 0) return source;
                var category = a.Category.CompareTo(b.Category); if (category != 0) return category;
                var id = a.Id.CompareTo(b.Id); return id != 0 ? id : string.Compare(a.DisplayName, b.DisplayName, StringComparison.OrdinalIgnoreCase);
            });
            BuildCatalogExport();
            if (_selectedSpawn != null && _selectedSpawn.Id >= 0) SelectSpawnById(_selectedSpawn.Id, _selectionConfirmed);
        }

        private static string ExportText(string value)
        {
            return (value ?? string.Empty).Replace('\t', ' ').Replace('\r', ' ').Replace('\n', ' ');
        }

        private void BuildCatalogExport()
        {
            var snapshot = new string[_catalog.Count];
            for (var i = 0; i < _catalog.Count; i++)
            {
                var entry = _catalog[i];
                snapshot[i] = string.Join("\t", new[]
                {
                    i.ToString(), entry.Id.ToString(), ExportText(entry.DisplayName), ExportText(entry.SpawnKey),
                    ((int)entry.Source).ToString(), ((int)entry.Category).ToString(), ((int)entry.Safety).ToString(), ExportText(entry.SafetyReason),
                    ((int)entry.EngineCapability).ToString(), entry.RendererCount.ToString()
                });
            }
            _catalogExport = snapshot;
        }

        private void AddNativeEntry(Item item, int id, SpawnCatalogSource source, HashSet<int> seen)
        {
            if (item == null || !seen.Add(item.GetInstanceID())) return;
            string display; try { display = item.GetName(); } catch { display = item.name; }
            var key = (item.name ?? string.Empty).Replace(" ", string.Empty).ToLowerInvariant();
            var category = SpawnCatalogCategory.Item;
            if (item.IsQuestItem) category = SpawnCatalogCategory.Quest;
            else if (item.Explosive != null) category = SpawnCatalogCategory.Explosive;
            else if (item.Weapon != null) category = SpawnCatalogCategory.Weapon;
            else if (item.FishingRod != null) category = SpawnCatalogCategory.Fishing;
            else if (item is Creature || item.Fish != null) category = SpawnCatalogCategory.Fish;
            var safety = RuntimeSpawnSafety.Safe; var reason = string.Empty;
            if (item is DeadPlayer || item.DeadPlayer != null || id == 53 || key == "deadplayer") { safety = RuntimeSpawnSafety.Blocked; reason = "角色/死亡玩家依赖网络玩家初始化"; }
            else if (item.IsQuestItem) { safety = RuntimeSpawnSafety.Confirm; reason = "真实任务物品"; }
            else if (item.Explosive != null) { safety = RuntimeSpawnSafety.Confirm; reason = "爆炸物"; }
            _catalog.Add(new SpawnCatalogEntry { Id = id, DisplayName = string.IsNullOrEmpty(display) ? item.name : display, SpawnKey = key, Item = item, Prefab = item.gameObject, Source = source, Category = category, Safety = safety, SafetyReason = reason, EngineCapability = EngineObjectCapability.NotEngine, InstanceId = item.GetInstanceID() });
        }

        private void AddEngineEntries(HashSet<int> seen)
        {
            try
            {
                var objects = Resources.FindObjectsOfTypeAll<GameObject>(); var added = 0;
                for (var i = 0; i < objects.Length && added < MaxEngineEntries; i++)
                {
                    var prefab = objects[i];
                    try
                    {
                        if (prefab == null || prefab.scene.IsValid() || prefab.GetComponent<Item>() != null || !seen.Add(prefab.GetInstanceID())) continue;
                        string blockedReason; var blocked = IsHardBlockedEngineObject(prefab, out blockedReason);
                        var rendererCount = blocked ? 0 : CountPreviewRenderers(prefab);
                        var capability = !blocked && rendererCount > 0 ? EngineObjectCapability.VisualPreview : EngineObjectCapability.DiagnosticOnly;
                        var reason = blocked ? blockedReason : (rendererCount > 0 ? "无脚本本地模型预览，不可拾取且不同步" : "没有可安全复制的静态 Mesh 或 Sprite，仅供诊断");
                        _catalog.Add(new SpawnCatalogEntry { Id = -1, DisplayName = string.IsNullOrEmpty(prefab.name) ? "<unnamed>" : prefab.name, SpawnKey = prefab.name ?? string.Empty, Prefab = prefab, Source = SpawnCatalogSource.Engine, Category = SpawnCatalogCategory.Engine, Safety = capability == EngineObjectCapability.VisualPreview ? RuntimeSpawnSafety.HighRiskLocal : RuntimeSpawnSafety.Blocked, SafetyReason = reason, EngineCapability = capability, RendererCount = rendererCount, InstanceId = prefab.GetInstanceID() });
                        added++;
                    }
                    catch { LastErrorCode = 402; }
                }
            }
            catch { LastErrorCode = 402; }
        }

        private static int CountPreviewRenderers(GameObject prefab)
        {
            var count = 0;
            try
            {
                var meshes = prefab.GetComponentsInChildren<MeshRenderer>(true);
                for (var i = 0; i < meshes.Length; i++)
                {
                    var filter = meshes[i] != null ? meshes[i].GetComponent<MeshFilter>() : null;
                    if (filter != null && filter.sharedMesh != null) count++;
                }
                var sprites = prefab.GetComponentsInChildren<SpriteRenderer>(true);
                for (var i = 0; i < sprites.Length; i++) if (sprites[i] != null && sprites[i].sprite != null) count++;
            }
            catch { return 0; }
            return count;
        }

        private static bool IsHardBlockedEngineObject(GameObject prefab, out string reason)
        {
            reason = string.Empty;
            if (prefab == null) { reason = "资源指针无效"; return true; }
            var objectName = (prefab.name ?? string.Empty).ToLowerInvariant();
            if (objectName.Contains("player") || objectName.Contains("server") || objectName.Contains("manager") || objectName.Contains("camera") || objectName.Contains("canvas")) { reason = "名称表明它是角色、服务器、管理器、相机或 UI 对象"; return true; }
            var components = prefab.GetComponentsInChildren<Component>(true);
            for (var i = 0; i < components.Length; i++)
            {
                if (components[i] == null) continue;
                var name = components[i].GetType().Name.ToLowerInvariant();
                if (components[i] is Camera || name.Contains("player") || name.Contains("server") || name.Contains("network") || name.Contains("manager") || name.Contains("eventsystem") || name == "canvas" || name == "recttransform" || name == "gameinfo") { reason = "包含角色、服务器、网络、管理器、相机或 UI 组件"; return true; }
            }
            return false;
        }

        private static bool IsHardBlockedEngineObject(GameObject prefab)
        {
            string reason; return IsHardBlockedEngineObject(prefab, out reason);
        }

        internal void SelectSpawnById(int id, bool externallyConfirmed = false)
        {
            EnsureCatalog();
            for (var i = 0; i < _catalog.Count; i++)
                if (_catalog[i].Id == id && _catalog[i].Source == SpawnCatalogSource.Game)
                {
                    SelectEntry(_catalog[i]);
                    if (externallyConfirmed && _selectedSpawn != null && _selectedSpawn.Safety != RuntimeSpawnSafety.Blocked)
                    {
                        _selectionConfirmed = true;
                        _selectionConfirmedAt = Time.unscaledTime;
                        SelectedSpawnState = 1;
                    }
                    return;
                }
            SelectedSpawnState = -2;
        }

        internal void SelectSpawnByCatalogIndex(int index, bool externallyConfirmed = false)
        {
            EnsureCatalog();
            if (index < 0 || index >= _catalog.Count) { SelectedSpawnState = -2; return; }
            SelectEntry(_catalog[index]);
            if (externallyConfirmed && _selectedSpawn != null && _selectedSpawn.Safety != RuntimeSpawnSafety.Blocked)
            {
                _selectionConfirmed = true;
                _selectionConfirmedAt = Time.unscaledTime;
                SelectedSpawnState = 1;
            }
        }

        private void SelectEntry(SpawnCatalogEntry entry)
        {
            if (entry == null || entry.Safety == RuntimeSpawnSafety.Blocked) { SelectedSpawnState = -3; return; }
            _selectedSpawn = entry;
            _selectionConfirmed = entry.Safety == RuntimeSpawnSafety.Safe;
            _selectionConfirmedAt = _selectionConfirmed ? Time.unscaledTime : 0f;
            SelectedSpawnState = _selectionConfirmed ? 1 : 2;
        }

        private void ConfirmSelection()
        {
            if (_selectedSpawn == null || _selectedSpawn.Safety == RuntimeSpawnSafety.Blocked) return;
            if (_selectedSpawn.Safety == RuntimeSpawnSafety.HighRiskLocal && !_highRiskEnabled) { SelectedSpawnState = -4; return; }
            _selectionConfirmed = true; _selectionConfirmedAt = Time.unscaledTime; SelectedSpawnState = 1;
        }

        internal void QueueSelectedSpawn()
        {
            if (_selectedSpawn == null) { SelectedSpawnState = -1; return; }
            if (_menuOpen && _tab != 2) { SelectedSpawnState = -5; return; }
            if (!_selectionConfirmed || (_selectedSpawn.Safety != RuntimeSpawnSafety.Safe && Time.unscaledTime - _selectionConfirmedAt > ConfirmationLifetime)) { _selectionConfirmed = false; SelectedSpawnState = -6; return; }
            if (_selectedSpawn.Safety == RuntimeSpawnSafety.HighRiskLocal && !_highRiskEnabled) { SelectedSpawnState = -4; return; }
            if (_spawnRequestPending) return;
            SpawnRequestSequence++; LastSpawnStage = 1; LastSpawnRendererCount = 0;
            _spawnRequestPending = true; SelectedSpawnState = 3;
        }

        private void ProcessSelectedSpawnRequest()
        {
            if (!_spawnRequestPending) return;
            _spawnRequestPending = false; var entry = _selectedSpawn;
            if (entry == null) { SelectedSpawnState = -1; return; }
            try
            {
                if (entry.IsNative)
                {
                    if (Time.unscaledTime - _lastNativeSpawnAt < NativeSpawnCooldown) { SelectedSpawnState = -7; return; }
                    var local = Player.LocalPlayer;
                    if (local == null) { SelectedSpawnState = -8; return; }
                    if (local.IsServerInitialized)
                    {
                        if (UseSpawnCommandMethod == null) { SelectedSpawnState = -13; return; }
                        UseSpawnCommandMethod.Invoke(null, new object[] { entry.SpawnKey, false }); _lastNativeSpawnAt = Time.unscaledTime; LastSpawnStage = 2; SelectedSpawnState = 4; return;
                    }
                    if (_privateLobbyConsent && entry.Id >= 0 && entry.Id <= 255 && entry.Safety == RuntimeSpawnSafety.Safe && (entry.Category == SpawnCatalogCategory.Item || entry.Category == SpawnCatalogCategory.Fishing || entry.Category == SpawnCatalogCategory.Weapon))
                    {
                        var server = Server.Instance; if (server == null) { SelectedSpawnState = -9; return; }
                        var camera = local.CurCam; var position = camera != null ? camera.transform.position + camera.transform.forward * 2f : local.Transform.position; var rotation = camera != null ? camera.transform.rotation : local.Transform.rotation;
                        server.BuyItem((byte)entry.Id, local, null, position, rotation, true); _lastNativeSpawnAt = Time.unscaledTime; LastSpawnStage = 2; SelectedSpawnState = 4; return;
                    }
                    SelectedSpawnState = -10; return;
                }
                if (Time.unscaledTime - _lastRawSpawnAt < RawSpawnCooldown || _rawClones.Count >= MaxRawClones) { SelectedSpawnState = -11; return; }
                if (!_highRiskEnabled || entry.Safety != RuntimeSpawnSafety.HighRiskLocal || entry.EngineCapability != EngineObjectCapability.VisualPreview || entry.Prefab == null || IsHardBlockedEngineObject(entry.Prefab)) { SelectedSpawnState = -12; return; }
                var camera2 = Player.LocalPlayer != null ? Player.LocalPlayer.CurCam : GameInfo.CurCamera;
                if (camera2 == null) { SelectedSpawnState = -8; return; }
                int rendererCount; string previewReason;
                var clone = CreateVisualPreview(entry.Prefab, camera2, out rendererCount, out previewReason);
                LastSpawnRendererCount = rendererCount;
                if (clone == null) { SelectedSpawnState = rendererCount == 0 ? -14 : -15; entry.SafetyReason = previewReason; BuildCatalogExport(); return; }
                _rawClones.Add(clone); _lastRawSpawnAt = Time.unscaledTime; LastSpawnStage = 3; SelectedSpawnState = 5;
            }
            catch { SelectedSpawnState = -20; LastErrorCode = 403; }
        }

        private GameObject CreateVisualPreview(GameObject prefab, Camera camera, out int rendererCount, out string reason)
        {
            rendererCount = 0; reason = string.Empty;
            if (prefab == null || camera == null) { reason = "资源或相机不可用"; return null; }
            var root = new GameObject("HTF.Preview." + (prefab.name ?? "Object"));
            LastSpawnStage = 2;
            try
            {
                root.transform.position = camera.transform.position + camera.transform.forward * 4f;
                root.transform.rotation = camera.transform.rotation;
                CopyPreviewHierarchy(prefab.transform, root.transform, true, ref rendererCount);
                if (rendererCount <= 0) { reason = "没有可安全复制的静态 Mesh 或 Sprite"; UnityEngine.Object.Destroy(root); return null; }
                root.SetActive(true);
                var renderers = root.GetComponentsInChildren<Renderer>(true);
                Bounds bounds = new Bounds(); var hasBounds = false;
                for (var i = 0; i < renderers.Length; i++)
                {
                    if (renderers[i] == null) continue;
                    renderers[i].enabled = true;
                    if (!hasBounds) { bounds = renderers[i].bounds; hasBounds = true; } else bounds.Encapsulate(renderers[i].bounds);
                }
                if (!hasBounds || !IsFinite(bounds.center) || !IsFinite(bounds.size) || bounds.size.sqrMagnitude < 0.000001f) { reason = "预览已创建但渲染边界为空"; UnityEngine.Object.Destroy(root); return null; }
                var largest = Mathf.Max(bounds.size.x, Mathf.Max(bounds.size.y, bounds.size.z));
                if (largest <= 0.0001f || float.IsNaN(largest) || float.IsInfinity(largest)) { reason = "预览尺寸无效"; UnityEngine.Object.Destroy(root); return null; }
                root.transform.localScale = Vector3.one * Mathf.Clamp(1.5f / largest, 0.05f, 20f);
                hasBounds = false;
                for (var i = 0; i < renderers.Length; i++) if (renderers[i] != null) { if (!hasBounds) { bounds = renderers[i].bounds; hasBounds = true; } else bounds.Encapsulate(renderers[i].bounds); }
                var desiredCenter = camera.transform.position + camera.transform.forward * 4f;
                root.transform.position += desiredCenter - bounds.center;
                var screen = camera.WorldToScreenPoint(desiredCenter);
                if (screen.z <= 0f || screen.x < 0f || screen.y < 0f || screen.x > Screen.width || screen.y > Screen.height) { reason = "预览创建后不在当前相机画面内"; UnityEngine.Object.Destroy(root); return null; }
                reason = "本地可见模型预览，不可拾取且不同步";
                return root;
            }
            catch
            {
                if (root != null) UnityEngine.Object.Destroy(root);
                reason = "复制渲染组件时发生异常";
                return null;
            }
        }

        private static void CopyPreviewHierarchy(Transform source, Transform destination, bool isRoot, ref int rendererCount)
        {
            if (source == null || destination == null) return;
            var target = destination;
            if (!isRoot)
            {
                var child = new GameObject(source.name ?? "PreviewPart");
                target = child.transform; target.SetParent(destination, false);
                target.localPosition = source.localPosition; target.localRotation = source.localRotation; target.localScale = source.localScale;
            }
            var sourceMeshRenderer = source.GetComponent<MeshRenderer>();
            var sourceMeshFilter = source.GetComponent<MeshFilter>();
            if (sourceMeshRenderer != null && sourceMeshFilter != null && sourceMeshFilter.sharedMesh != null)
            {
                var targetFilter = target.gameObject.AddComponent<MeshFilter>(); targetFilter.sharedMesh = sourceMeshFilter.sharedMesh;
                var targetRenderer = target.gameObject.AddComponent<MeshRenderer>(); targetRenderer.sharedMaterials = sourceMeshRenderer.sharedMaterials; targetRenderer.enabled = true; rendererCount++;
            }
            var sourceSprite = source.GetComponent<SpriteRenderer>();
            if (sourceSprite != null && sourceSprite.sprite != null)
            {
                var targetSprite = target.gameObject.AddComponent<SpriteRenderer>(); targetSprite.sprite = sourceSprite.sprite; targetSprite.color = sourceSprite.color; targetSprite.flipX = sourceSprite.flipX; targetSprite.flipY = sourceSprite.flipY; targetSprite.sortingLayerID = sourceSprite.sortingLayerID; targetSprite.sortingOrder = sourceSprite.sortingOrder; targetSprite.enabled = true; rendererCount++;
            }
            for (var i = 0; i < source.childCount; i++) CopyPreviewHierarchy(source.GetChild(i), target, false, ref rendererCount);
        }

        private void DestroyRawClones()
        {
            for (var i = 0; i < _rawClones.Count; i++) if (_rawClones[i] != null) UnityEngine.Object.Destroy(_rawClones[i]);
            _rawClones.Clear();
        }

        private void ProcessClientSpawnRequest()
        {
            if (ClientSpawnState == 1)
            {
                var id = Bootstrap.TakeClientSpawnRequest(); if (id < 0) return;
                try
                {
                    var local = Player.LocalPlayer; var server = Server.Instance; var prefab = GameInfo.GetSpawnable((byte)id);
                    if (!_privateLobbyConsent || local == null || server == null || prefab == null) { ClientSpawnState = -1; return; }
                    var key = (prefab.name ?? string.Empty).Replace(" ", string.Empty).ToLowerInvariant();
                    if (prefab.DeadPlayer != null || prefab.IsQuestItem || prefab.Explosive != null || key == "deadplayer") { ClientSpawnState = -2; return; }
                    var holding = local.Holding; if (holding == null || holding.UninitializedHeldItem != null) { ClientSpawnState = -3; return; }
                    var previous = holding.HeldItem; _previousHeldItemId = previous != null ? previous.GetInstanceID() : 0;
                    var camera = local.CurCam; var position = camera != null ? camera.transform.position + camera.transform.forward * 2f : local.Transform.position; var rotation = camera != null ? camera.transform.rotation : local.Transform.rotation;
                    server.BuyItem((byte)id, local, null, position, rotation, true); _clientSpawnStartedAt = Time.unscaledTime; ClientSpawnState = 2;
                }
                catch { ClientSpawnState = -5; LastErrorCode = 301; }
            }
            else if (ClientSpawnState == 2)
            {
                var local = Player.LocalPlayer; var held = local != null && local.Holding != null ? local.Holding.HeldItem : null;
                if (held != null && held.GetInstanceID() != _previousHeldItemId) ClientSpawnState = 3;
                else if (Time.unscaledTime - _clientSpawnStartedAt > 3f) ClientSpawnState = -4;
            }
        }

        private void OnGUI()
        {
            EnsureStyles();
            if (_espEnabled) for (var i = 0; i < _overlayEntries.Count; i++) if (_overlayEntries[i].Valid) DrawOverlayEntry(_overlayEntries[i]);
            if (_menuOpen)
            {
                _windowRect.width = Mathf.Clamp(Screen.width * 0.55f, 560f, 900f); _windowRect.height = Mathf.Clamp(Screen.height * 0.72f, 440f, 760f);
                _windowRect.x = Mathf.Clamp(_windowRect.x, 0f, Mathf.Max(0f, Screen.width - _windowRect.width)); _windowRect.y = Mathf.Clamp(_windowRect.y, 0f, Mathf.Max(0f, Screen.height - _windowRect.height));
                _windowRect = GUI.Window(0x485446, _windowRect, DrawWindow, "How to Fish Trainer v0.3.0");
            }
        }

        private void DrawOverlayEntry(OverlayEntry entry)
        {
            var color = Color.white;
            if (entry.Kind == OverlayKind.Fish) color = new Color(0.3f, 0.9f, 1f); else if (entry.Kind == OverlayKind.Weapon) color = new Color(1f, 0.75f, 0.2f); else if (entry.Kind == OverlayKind.Quest) color = new Color(1f, 0.35f, 0.75f); else if (entry.Kind == OverlayKind.Dangerous) color = new Color(1f, 0.25f, 0.25f);
            if (entry.Obstructed) color = Color.Lerp(color, Color.gray, 0.65f);
            _labelStyle.normal.textColor = color;
            var text = string.Format("{0}  {1:0}m", entry.Name, entry.Distance); var position = new Vector2(entry.Screen.x, Screen.height - entry.Screen.y); var size = _labelStyle.CalcSize(new GUIContent(text)); var rect = new Rect(position.x - size.x * 0.5f, position.y - size.y, size.x + 8f, size.y + 4f);
            GUI.Label(new Rect(rect.x + 1f, rect.y + 1f, rect.width, rect.height), text, _shadowStyle); GUI.Label(rect, text, _labelStyle);
        }

        private void DrawWindow(int id)
        {
            GUILayout.BeginHorizontal();
            if (GUILayout.Toggle(_tab == 0, "战斗", GUI.skin.button)) _tab = 0; if (GUILayout.Toggle(_tab == 1, "透视", GUI.skin.button)) _tab = 1; if (GUILayout.Toggle(_tab == 2, "生成器", GUI.skin.button)) _tab = 2; if (GUILayout.Toggle(_tab == 3, "实验", GUI.skin.button)) _tab = 3; if (GUILayout.Toggle(_tab == 4, "诊断", GUI.skin.button)) _tab = 4;
            GUILayout.EndHorizontal(); GUILayout.Space(8f);
            if (_tab == 0) DrawCombatTab(); else if (_tab == 1) DrawEspTab(); else if (_tab == 2) DrawSpawnerTab(); else if (_tab == 3) DrawExperimentTab(); else DrawDiagnosticsTab();
            GUILayout.FlexibleSpace(); GUILayout.Label("Home 第三人称 | End 静默自瞄 | Insert 关闭 | F10 安全退出"); GUI.DragWindow(new Rect(0f, 0f, 10000f, 24f));
        }

        private void DrawCombatTab()
        {
            var next = GUILayout.Toggle(_aimEnabled, "F9 360° 最近目标锁定"); if (next != _aimEnabled) Bootstrap.SetAimEnabled(next); _aimEnabled = next;
            GUILayout.BeginHorizontal();
            if (GUILayout.Toggle(_aimTrackingMode == AimTrackingMode.StableFirst, "稳定优先", GUI.skin.button)) { _aimTrackingMode = AimTrackingMode.StableFirst; Bootstrap.SetAimTrackingMode(0); }
            if (GUILayout.Toggle(_aimTrackingMode == AimTrackingMode.Continuous, "持续追踪", GUI.skin.button)) { _aimTrackingMode = AimTrackingMode.Continuous; Bootstrap.SetAimTrackingMode(1); }
            GUILayout.EndHorizontal();
            GUILayout.Label("目标类别（F9 与 End 共用）");
            GUILayout.BeginHorizontal();
            DrawAimTargetToggle(AimTargetFlags.Fish, "鱼", true);
            DrawAimTargetToggle(AimTargetFlags.Bird, "鸟", true);
            DrawAimTargetToggle(AimTargetFlags.OtherCreature, "其他生物", true);
            DrawAimTargetToggle(AimTargetFlags.Player, "玩家（私房）", _privateLobbyConsent);
            GUILayout.EndHorizontal();
            _ignoreOcclusion = GUILayout.Toggle(_ignoreOcclusion, "忽略墙体遮挡");
            GUILayout.Label(string.Format("最大距离: {0:0}m", _maxAimDistance)); _maxAimDistance = GUILayout.HorizontalSlider(_maxAimDistance, 10f, 300f);
            GUILayout.Label(string.Format("平滑速度: {0:0}", _smoothing)); _smoothing = GUILayout.HorizontalSlider(_smoothing, 1f, 60f);
            GUILayout.Label(string.Format("后坐力补偿: {0:0}%", _recoilCompensation * 100f)); _recoilCompensation = GUILayout.HorizontalSlider(_recoilCompensation, 0f, 1f);
            GUILayout.Label(_aimTrackingMode == AimTrackingMode.StableFirst ? "异常跃起时冻结 200ms，并优先切换到稳定目标。" : "允许追踪跃起目标，但限制目标点与镜头转速。");
            GUILayout.Label("持枪 ADS + 按住右键；360°获取不代表镜头瞬间旋转。");
            GUILayout.Space(8f);
            var third = GUILayout.Toggle(_thirdPersonEnabled, "Home 第三人称"); if (third != _thirdPersonEnabled) Bootstrap.SetThirdPersonEnabled(third); _thirdPersonEnabled = third;
            if (_thirdPersonEnabled)
            {
                GUILayout.Label(string.Format("距离 {0:0.0}m | 高度 {1:0.0}m | 肩位 {2:0.0}m", _thirdPersonDistance, _thirdPersonHeight, _thirdPersonShoulder));
                _thirdPersonDistance = GUILayout.HorizontalSlider(_thirdPersonDistance, 1.5f, 8f); _thirdPersonHeight = GUILayout.HorizontalSlider(_thirdPersonHeight, -0.5f, 2f); _thirdPersonShoulder = GUILayout.HorizontalSlider(_thirdPersonShoulder, -1.5f, 1.5f);
                _thirdPersonCrosshair = GUILayout.Toggle(_thirdPersonCrosshair, "显示狙击准星（默认隐藏）");
                GUILayout.Label(string.Format("状态: {0} | 后端: {1} | 渲染次数: {2}", ThirdPersonStateText(ThirdPersonState), ThirdPersonBackendText(_thirdPersonBackend), ThirdPersonRenderCount));
                GUILayout.Label(string.Format("原生本体: {0} / {1} | Mesh {2}+{3} | 骨骼 {4} | IK {5} | 动作 {6} / 阶段 {7}", AvatarMirrorStateText(_avatarMirrorState), _thirdPersonAvatarBackend, AvatarMeshCount, AvatarSkinnedMeshCount, AvatarBoneCount, AvatarIkCount, AvatarAnimationState, AvatarNativeStage));
            }
            var silent = GUILayout.Toggle(_silentAimEnabled, "End 静默自瞄（镜头不跟随）"); if (silent != _silentAimEnabled) Bootstrap.SetSilentAimEnabled(silent); _silentAimEnabled = silent;
            GUILayout.BeginHorizontal();
            if (GUILayout.Toggle(_silentAimMode == SilentAimMode.InitialCorrection, "开火瞬间修正", GUI.skin.button)) { _silentAimMode = SilentAimMode.InitialCorrection; Bootstrap.SetSilentAimMode(1); }
            if (GUILayout.Toggle(_silentAimMode == SilentAimMode.ProjectileTracking, "实体弹丸追踪", GUI.skin.button)) { _silentAimMode = SilentAimMode.ProjectileTracking; Bootstrap.SetSilentAimMode(2); }
            GUILayout.EndHorizontal();
            GUILayout.Label("静默模式无需右键，持枪时预锁目标；保持伤害、射速、弹速和霰弹散布。普通客户端仅限已确认私房测试。");
        }

        private void DrawEspTab()
        {
            var next = GUILayout.Toggle(_espEnabled, "F11 物品与生物标签"); if (next != _espEnabled) Bootstrap.SetEspEnabled(next); _espEnabled = next;
            GUILayout.Label(string.Format("最大距离: {0:0}m", _maxEspDistance)); _maxEspDistance = GUILayout.HorizontalSlider(_maxEspDistance, 10f, 500f);
            GUILayout.Label(string.Format("字体大小: {0}", _fontSize)); var font = Mathf.RoundToInt(GUILayout.HorizontalSlider(_fontSize, 10f, 36f));
            if (font != _fontSize) { _fontSize = font; _labelStyle.fontSize = font; _shadowStyle.fontSize = font; }
            GUILayout.Label(string.Format("当前标签: {0} / {1} | 投影上限 60 FPS", EspCount, _maxLabels));
        }

        private void DrawSpawnerTab()
        {
            EnsureCatalog(); GUILayout.BeginHorizontal(); GUILayout.Label("搜索", GUILayout.Width(40f)); _catalogSearch = GUILayout.TextField(_catalogSearch ?? string.Empty); GUILayout.EndHorizontal();
            GUILayout.BeginHorizontal();
            if (GUILayout.Toggle(_catalogFilter == -1, "全部", GUI.skin.button)) _catalogFilter = -1; if (GUILayout.Toggle(_catalogFilter == 0, "物品", GUI.skin.button)) _catalogFilter = 0; if (GUILayout.Toggle(_catalogFilter == 2, "武器", GUI.skin.button)) _catalogFilter = 2; if (GUILayout.Toggle(_catalogFilter == 3, "鱼/生物", GUI.skin.button)) _catalogFilter = 3; if (GUILayout.Toggle(_catalogFilter == 6, "引擎", GUI.skin.button)) _catalogFilter = 6;
            GUILayout.EndHorizontal();
            _highRiskEnabled = GUILayout.Toggle(_highRiskEnabled, "允许无脚本本地模型预览（不可拾取/不同步，最多 20 个）");
            if (_selectedSpawn != null)
            {
                GUILayout.Label(string.Format("当前: {0} | {1} | {2}", _selectedSpawn.DisplayName, CapabilityText(_selectedSpawn), SafetyText(_selectedSpawn)));
                if (!_selectionConfirmed && _selectedSpawn.Safety != RuntimeSpawnSafety.Blocked && GUILayout.Button("确认选择（10 秒内按 F8）")) ConfirmSelection();
            }
            GUILayout.Label(string.Format("目录: {0} 项 | 状态: {1} | 阶段: {2}", _catalog.Count, SpawnStateText(SelectedSpawnState), SpawnStageText(LastSpawnStage)));
            _spawnScroll = GUILayout.BeginScrollView(_spawnScroll); var lastSource = (SpawnCatalogSource)(-1); var lastCategory = (SpawnCatalogCategory)(-1); var search = (_catalogSearch ?? string.Empty).Trim().ToLowerInvariant();
            for (var i = 0; i < _catalog.Count; i++)
            {
                var entry = _catalog[i]; if (_catalogFilter >= 0 && (int)entry.Category != _catalogFilter) continue;
                if (search.Length != 0 && !(entry.DisplayName ?? string.Empty).ToLowerInvariant().Contains(search) && !(entry.SpawnKey ?? string.Empty).ToLowerInvariant().Contains(search) && !entry.Id.ToString().Contains(search)) continue;
                if (entry.Source != lastSource || entry.Category != lastCategory) { GUILayout.Space(5f); GUILayout.Label(string.Format("{0} / {1}", SourceText(entry.Source), CategoryText(entry.Category))); lastSource = entry.Source; lastCategory = entry.Category; }
                GUI.enabled = entry.Safety != RuntimeSpawnSafety.Blocked; var idText = entry.Id >= 0 ? entry.Id.ToString() : "--"; var marker = entry == _selectedSpawn ? "> " : string.Empty;
                if (GUILayout.Button(string.Format("{0}[{1}] {2}  {3}  {4}", marker, idText, entry.DisplayName, CapabilityText(entry), SafetyText(entry)))) SelectEntry(entry); GUI.enabled = true;
            }
            GUILayout.EndScrollView();
        }

        private void DrawExperimentTab()
        {
            var next = GUILayout.Toggle(_privateLobbyConsent, "好友/私有测试房（允许玩家锁定和客户端物品请求）"); if (next != _privateLobbyConsent) Bootstrap.SetPrivateLobbyConsent(next); _privateLobbyConsent = next;
            if (!_privateLobbyConsent && (_poseMode != PoseMode.Off || _poseLookDown)) { _poseMode = PoseMode.Off; _poseLookDown = false; Bootstrap.SetPoseMode(0); Bootstrap.SetPoseLookDown(false); }
            GUILayout.Label("身体方向（互斥）与低头（可组合；面板打开时自动暂停）");
            GUI.enabled = _privateLobbyConsent;
            GUILayout.BeginHorizontal();
            if (GUILayout.Toggle(_poseMode == PoseMode.Off, "关闭", GUI.skin.button)) { _poseMode = PoseMode.Off; Bootstrap.SetPoseMode(0); }
            if (GUILayout.Toggle(_poseMode == PoseMode.HideHeadBackwards, "身体朝后", GUI.skin.button)) { _poseMode = PoseMode.HideHeadBackwards; Bootstrap.SetPoseMode(1); }
            if (GUILayout.Toggle(_poseMode == PoseMode.HighSpeedSpin, "高速身体转圈", GUI.skin.button)) { _poseMode = PoseMode.HighSpeedSpin; Bootstrap.SetPoseMode(2); }
            GUILayout.EndHorizontal();
            var lookDown = GUILayout.Toggle(_poseLookDown, "同时低头（可单独使用，也可配合身体朝后/高速转圈）");
            if (lookDown != _poseLookDown) { _poseLookDown = lookDown; Bootstrap.SetPoseLookDown(lookDown); }
            GUILayout.Label(string.Format("转圈速度: {0:0}°/s", _poseSpinSpeed));
            var spinSpeed = Mathf.RoundToInt(GUILayout.HorizontalSlider(_poseSpinSpeed, 90f, 1440f));
            if (spinSpeed != Mathf.RoundToInt(_poseSpinSpeed)) { _poseSpinSpeed = spinSpeed; Bootstrap.SetPoseSpinSpeed(spinSpeed); }
            GUI.enabled = true;
            GUILayout.Label(string.Format("发送路径状态: {0} | 远端视觉: 待双客户端验证", PoseStateText(PoseState)));
            GUILayout.Label("本机本体复用游戏原生 Body/Hands/Legs/IK 数据链；远端姿态和命中箱仍需第二客户端验证。");
            GUILayout.Label("不会伪造房主或服务器权限；原始引擎对象始终仅本机显示。"); GUILayout.Label(string.Format("客户端物品请求状态: {0}", ClientSpawnState));
        }

        private void DrawDiagnosticsTab()
        {
            GUILayout.Label(string.Format("瞄准策略: {0} | 目标类型/种类: {1}/{2} | 掩码: {3}", _aimTrackingMode, _lockedKind, _lockedSpecies, _aimTargetMask)); GUILayout.Label(string.Format("锁定距离: {0:0.0}m", _lockedDistance));
            GUILayout.Label(string.Format("鸟候选 alive/flying: {0}/{1} | 玩家候选: {2}", BirdAliveCandidateCount, BirdFlyingCandidateCount, PlayerCandidateCount));
            GUILayout.Label(string.Format("第三人称: {0} | 后端: {1}", ThirdPersonStateText(ThirdPersonState), ThirdPersonBackendText(_thirdPersonBackend)));
            GUILayout.Label(string.Format("相机 ID: {0} | 渲染: {1} | 请求/碰撞/实际位移: {2}/{3}/{4} mm | 恢复原因: {5}", ThirdPersonSourceCameraId, ThirdPersonRenderCount, ThirdPersonRequestedDistanceMm, ThirdPersonCollisionDistanceMm, ThirdPersonAppliedDistanceMm, ThirdPersonRestoreReason));
            GUILayout.Label(string.Format("头骨与真实相机偏差: {0} mm | 本地身体 Renderer: {1}/{2}", ThirdPersonHeadOffsetMm, ThirdPersonBodyVisibleCount, ThirdPersonBodyRendererCount));
            GUILayout.Label(string.Format("本体: {0}/{1} | 源 ID {2} | Mesh {3}+{4} | 骨骼 {5} | IK {6} | 原生阶段 {7} | 帧/失败 {8}/{9} | Bounds {10} mm | 模板 {11} | 外观 {12}", _thirdPersonAvatarBackend, _avatarMirrorState, AvatarSourceRootId, AvatarMeshCount, AvatarSkinnedMeshCount, AvatarBoneCount, AvatarIkCount, AvatarNativeStage, AvatarAnimationFrameCount, AvatarNativeFailureCount, AvatarBoundsDistanceMm, AvatarTemplateCandidateCount, AvatarAppearanceApplyState));
            GUILayout.Label(string.Format("姿态: {0}+低头{1}/{2} | 发送 pitch/yaw {3}/{4} mdeg | 恢复 {5} 次 | 远端待验证", _poseMode, _poseLookDown ? "开" : "关", PoseStateText(PoseState), PoseSentPitchMilliDegrees, PoseSentYawMilliDegrees, PoseRestoreCount));
            GUILayout.Label(string.Format("静默自瞄: {0} | 状态: {1} | 跟踪弹丸: {2}", _silentAimMode, SilentAimStateText(SilentAimState), TrackedProjectileCount));
            GUILayout.Label(string.Format("ESP 对象数: {0}", EspCount)); GUILayout.Label(string.Format("目录对象数: {0}", _catalog.Count)); GUILayout.Label(string.Format("本地模型预览: {0}/{1}", _rawClones.Count, MaxRawClones)); GUILayout.Label(string.Format("生成请求 #{0} | 阶段 {1} | Renderer {2}", SpawnRequestSequence, SpawnStageText(LastSpawnStage), LastSpawnRendererCount)); GUILayout.Label(string.Format("最后错误码: {0}", LastErrorCode));
        }

        private static string PoseStateText(int state)
        {
            if (state == 2) return "原有发送路径已替换/远端命中箱待验证"; if (state == 1) return "面板打开，已暂停"; if (state == -1) return "需要私房确认"; if (state < 0) return "失败关闭 " + state; return "关闭";
        }

        private void DrawAimTargetToggle(AimTargetFlags flag, string label, bool allowed)
        {
            var current = (_aimTargetMask & flag) != 0;
            GUI.enabled = allowed;
            var next = GUILayout.Toggle(current, label, GUI.skin.button);
            GUI.enabled = true;
            if (!allowed || next == current) return;
            if (next) _aimTargetMask |= flag; else _aimTargetMask &= ~flag;
            Bootstrap.SetAimTargetMask((int)_aimTargetMask);
            if (!next && _lockedSpecies == AimTargetSpecies.Player && flag == AimTargetFlags.Player) ClearTarget(true);
        }

        private static string AvatarMirrorStateText(AvatarMirrorState state)
        {
            if (state == AvatarMirrorState.Active) return "原生本体链已应用";
            if (state == AvatarMirrorState.Building) return "正在建立";
            if (state == AvatarMirrorState.NoSource) return "没有当前角色源";
            if (state == AvatarMirrorState.NoRenderableContent) return "没有可复制网格";
            if (state == AvatarMirrorState.Failed) return "建立失败";
            return "关闭";
        }

        private static string ThirdPersonStateText(int state)
        {
            if (state == 1) return "渲染回调已生效"; if (state == 2) return "原生观察相机已生效"; if (state == 10) return "等待渲染回调"; if (state == 11) return "观察相机等待首帧"; if (state == -1) return "等待本地玩家"; if (state == -2) return "等待当前相机"; if (state == -3) return "玩家死亡，已恢复"; if (state == -9) return "全部相机后端失败"; if (state == -10) return "异常坐标已阻止"; return "关闭";
        }

        private static string ThirdPersonBackendText(ThirdPersonBackend backend)
        {
            if (backend == ThirdPersonBackend.RenderCallback) return "最终渲染覆盖"; if (backend == ThirdPersonBackend.NativeObserverCamera) return "游戏原生观察相机"; return "无";
        }

        private static string SilentAimStateText(int state)
        {
            if (state == 1) return "开火方向修正"; if (state == 2) return "本地实体弹丸追踪/服务器效果待验证"; if (state == 3) return "普通客户端网络认可待验证"; if (state == -1) return "需要私房确认"; if (state < 0) return "失败关闭 " + state; return "关闭或等待目标";
        }

        private static string SourceText(SpawnCatalogSource source)
        {
            if (source == SpawnCatalogSource.Game) return "游戏内官方物品"; if (source == SpawnCatalogSource.Named) return "名称/皮肤隐藏物品"; if (source == SpawnCatalogSource.Resource) return "资源 Item"; return "引擎底层对象";
        }

        private static string CategoryText(SpawnCatalogCategory category)
        {
            if (category == SpawnCatalogCategory.Fishing) return "钓鱼工具"; if (category == SpawnCatalogCategory.Weapon) return "武器"; if (category == SpawnCatalogCategory.Fish) return "鱼与其他生物"; if (category == SpawnCatalogCategory.Quest) return "任务物品"; if (category == SpawnCatalogCategory.Explosive) return "爆炸物"; if (category == SpawnCatalogCategory.Engine) return "引擎对象"; return "普通物品";
        }

        private static string SafetyText(SpawnCatalogEntry entry)
        {
            if (entry.Safety == RuntimeSpawnSafety.Safe) return "[安全]"; if (entry.Safety == RuntimeSpawnSafety.Confirm) return "[需确认: " + entry.SafetyReason + "]"; if (entry.Safety == RuntimeSpawnSafety.HighRiskLocal) return "[高风险/仅本机]"; return "[禁止: " + entry.SafetyReason + "]";
        }

        private static string CapabilityText(SpawnCatalogEntry entry)
        {
            if (entry.IsNative) return entry.Source == SpawnCatalogSource.Game ? "可拾取物" : "隐藏 Item";
            if (entry.EngineCapability == EngineObjectCapability.VisualPreview) return "可见模型预览";
            return "仅诊断资源";
        }

        private static string SpawnStageText(int stage)
        {
            if (stage == 1) return "请求已排队"; if (stage == 2) return "原生调用/预览已创建"; if (stage == 3) return "可见性验证成功"; return "未开始";
        }

        private static string SpawnStateText(int state)
        {
            if (state == 5) return "本地模型预览可见"; if (state == 4) return "原生生成调用完成"; if (state == 3) return "等待 Unity 主线程"; if (state == 2) return "需要确认"; if (state == 1) return "已选择";
            if (state == -1) return "尚未选择"; if (state == -2) return "ID/目录索引无效"; if (state == -3) return "对象已禁止"; if (state == -4) return "模型预览开关未启用"; if (state == -5) return "当前面板不允许生成"; if (state == -6) return "确认缺失或已过期"; if (state == -7) return "物品生成冷却中"; if (state == -8) return "本地玩家或相机不可用"; if (state == -9) return "服务器实例不可用"; if (state == -10) return "普通客户端无生成权限"; if (state == -11) return "预览冷却或数量已满"; if (state == -12) return "资源不允许预览"; if (state == -13) return "原生生成方法不可用"; if (state == -14) return "没有可复制的渲染内容"; if (state == -15) return "预览不可见，已自动清理"; if (state == -20) return "生成过程异常"; return state.ToString();
        }

        private void EnsureStyles()
        {
            if (_labelStyle != null) return;
            _labelStyle = new GUIStyle(GUI.skin.label) { fontSize = _fontSize, fontStyle = FontStyle.Bold, alignment = TextAnchor.MiddleCenter }; _shadowStyle = new GUIStyle(_labelStyle); _shadowStyle.normal.textColor = Color.black;
        }

        private void UpdateInputCapture()
        {
            if (_menuOpen)
            {
                if (!_cursorStateSaved) { var local = Player.LocalPlayer; _previousMouseLocked = local != null && local.Camera != null && local.Camera.MouseLocked; _cursorStateSaved = true; CaptureActions(); }
                KeepMenuInputCaptured();
            }
            else RestoreInputCapture();
        }

        private void CaptureActions()
        {
            _blockedActions.Clear(); _blockedActionStates.Clear();
            try
            {
                var input = GameInfo.Input; if (input == null || input.actions == null) return; var names = new[] { "PlayerLook", "PlayerLeftClick", "PlayerRightClick" };
                for (var i = 0; i < names.Length; i++)
                {
                    var action = input.actions.FindAction(names[i], false); if (action == null) continue; _blockedActions.Add(action); _blockedActionStates.Add(action.enabled); action.Disable();
                }
            }
            catch { LastErrorCode = 501; }
        }

        private void KeepMenuInputCaptured()
        {
            PlayerCamera.ToggleMouse(true);
            try
            {
                var local = Player.LocalPlayer;
                if (local != null && local.Camera != null) { if (LookInputField != null) LookInputField.SetValue(local.Camera, Vector2.zero); if (RawLookInputField != null) RawLookInputField.SetValue(local.Camera, Vector2.zero); if (ControllerLookInputField != null) ControllerLookInputField.SetValue(local.Camera, Vector2.zero); }
            }
            catch { }
        }

        private void RestoreInputCapture()
        {
            if (!_cursorStateSaved) return;
            for (var i = 0; i < _blockedActions.Count; i++) try { if (_blockedActionStates[i]) _blockedActions[i].Enable(); else _blockedActions[i].Disable(); } catch { }
            _blockedActions.Clear(); _blockedActionStates.Clear(); PlayerCamera.ToggleMouse(!_previousMouseLocked); _cursorStateSaved = false;
        }
    }
}
