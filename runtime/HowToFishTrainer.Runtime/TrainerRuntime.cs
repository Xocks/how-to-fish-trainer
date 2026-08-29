using System;
using System.Collections.Generic;
using System.Reflection;
using UnityEngine;
using UnityEngine.InputSystem;
using UnityEngine.SceneManagement;

namespace HowToFishTrainer.Runtime
{
    public static class Bootstrap
    {
        private static TrainerRuntimeBehaviour _instance;
        private static volatile bool _aimEnabled, _espEnabled, _menuOpen, _privateLobbyConsent, _shutdownRequested;
        private static volatile int _clientSpawnRequest = -1, _selectedSpawnIdRequest = -2, _selectedCatalogIndexRequest = -1;
        private static volatile bool _selectedSpawnRequested;

        public static bool Initialize()
        {
            if (!ReferenceEquals(_instance, null)) return true;
            var host = new GameObject("HowToFishTrainer.Runtime");
            UnityEngine.Object.DontDestroyOnLoad(host);
            _instance = host.AddComponent<TrainerRuntimeBehaviour>();
            _instance.ApplyControlState(_aimEnabled, _espEnabled, _menuOpen, _privateLobbyConsent);
            return true;
        }

        public static void SetAimEnabled(bool value) { _aimEnabled = value; }
        public static void SetEspEnabled(bool value) { _espEnabled = value; }
        public static void SetMenuOpen(bool value) { _menuOpen = value; }
        public static void SetPrivateLobbyConsent(bool value) { _privateLobbyConsent = value; }
        public static bool GetAimEnabled() { return _aimEnabled; }
        public static bool GetEspEnabled() { return _espEnabled; }
        public static bool GetMenuOpen() { return _menuOpen; }
        public static bool GetPrivateLobbyConsent() { return _privateLobbyConsent; }

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

        public static int GetStatusWord()
        {
            var value = 0;
            if (_aimEnabled) value |= 1;
            if (_espEnabled) value |= 2;
            if (_menuOpen) value |= 4;
            if (_privateLobbyConsent) value |= 8;
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
            _aimEnabled = _espEnabled = _menuOpen = _privateLobbyConsent = false;
            _clientSpawnRequest = -1;
            _selectedSpawnIdRequest = -2;
            _selectedCatalogIndexRequest = -1;
            _selectedSpawnRequested = false;
            _shutdownRequested = true;
        }

        internal static void Tick()
        {
            if (ReferenceEquals(_instance, null)) return;
            _instance.ApplyControlState(_aimEnabled, _espEnabled, _menuOpen, _privateLobbyConsent);
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
    internal enum OverlayKind { Item = 1, Fish, Weapon, Quest, Dangerous }
    internal enum SpawnCatalogSource { Game, Named, Resource, Engine }
    internal enum SpawnCatalogCategory { Item, Fishing, Weapon, Fish, Quest, Explosive, Engine }
    internal enum RuntimeSpawnSafety { Safe, Confirm, HighRiskLocal, Blocked }

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
        internal bool IsNative { get { return Item != null; } }
    }

    [DefaultExecutionOrder(10000)]
    public sealed class TrainerRuntimeBehaviour : MonoBehaviour
    {
        private const float EntityRefreshInterval = 0.1f, ProjectionInterval = 1f / 60f, TargetRefreshInterval = 0.05f;
        private const float NativeSpawnCooldown = 0.5f, RawSpawnCooldown = 2f, ConfirmationLifetime = 10f;
        private const int DefaultMaxLabels = 200, MaxEngineEntries = 500, MaxRawClones = 20;

        private static readonly FieldInfo AliveCreaturesField = typeof(CreatureManager).GetField("_aliveCreatures", BindingFlags.Instance | BindingFlags.NonPublic);
        private static readonly FieldInfo CameraRotationField = typeof(PlayerCamera).GetField("_rot", BindingFlags.Instance | BindingFlags.NonPublic);
        private static readonly FieldInfo CameraRecoilCurField = typeof(PlayerCamera).GetField("_recoilCur", BindingFlags.Instance | BindingFlags.NonPublic);
        private static readonly FieldInfo CameraRecoilTarField = typeof(PlayerCamera).GetField("_recoilTar", BindingFlags.Instance | BindingFlags.NonPublic);
        private static readonly FieldInfo RawLookInputField = typeof(PlayerCamera).GetField("_rawLookInput", BindingFlags.Instance | BindingFlags.NonPublic);
        private static readonly FieldInfo ControllerLookInputField = typeof(PlayerCamera).GetField("_controllerLookInput", BindingFlags.Instance | BindingFlags.NonPublic);
        private static readonly FieldInfo LookInputField = typeof(PlayerCamera).GetField("<LookInput>k__BackingField", BindingFlags.Instance | BindingFlags.NonPublic);
        private static readonly MethodInfo ResetToolRecoilMethod = typeof(PlayerToolMovement).GetMethod("ResetSwayRecoilPosRotVel", BindingFlags.Instance | BindingFlags.NonPublic);
        private static readonly FieldInfo NameSpawnablesField = typeof(GameInfo).GetField("_nameToSpawnable", BindingFlags.Static | BindingFlags.NonPublic);
        private static readonly MethodInfo UseSpawnCommandMethod = typeof(DazedCommands).GetMethod("UseSpawnCommand", BindingFlags.Static | BindingFlags.Public | BindingFlags.NonPublic);

        private readonly List<OverlayEntry> _overlayEntries = new List<OverlayEntry>(DefaultMaxLabels);
        private readonly List<SpawnCatalogEntry> _catalog = new List<SpawnCatalogEntry>(256);
        private string[] _catalogExport = new string[0];
        private readonly List<GameObject> _rawClones = new List<GameObject>(MaxRawClones);
        private readonly List<InputAction> _blockedActions = new List<InputAction>(3);
        private readonly List<bool> _blockedActionStates = new List<bool>(3);

        private bool _aimEnabled, _espEnabled, _menuOpen, _privateLobbyConsent, _allCreatures, _ignoreOcclusion, _highRiskEnabled;
        private float _maxAimDistance = 120f, _smoothing = 18f, _maxRotationSpeed = 720f, _recoilCompensation = 1f, _maxEspDistance = 150f;
        private int _maxLabels = DefaultMaxLabels, _fontSize = 14, _occlusionCursor, _tab, _catalogFilter = -1;
        private float _nextEntityRefreshAt, _nextProjectionAt, _nextTargetRefreshAt, _nextCatalogCheckAt;
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

        public int EspCount { get; private set; }
        public int AimTargetKind { get { return (int)_lockedKind; } }
        public int LastErrorCode { get; private set; }
        public int ClientSpawnState { get; internal set; }
        public int SelectedSpawnId { get { return _selectedSpawn != null ? _selectedSpawn.Id : -1; } }
        public int SelectedSpawnMode { get { return _selectedSpawn == null ? 0 : (_selectedSpawn.IsNative ? 1 : 2); } }
        public int SelectedSpawnState { get; private set; }
        public int CatalogCount { get { return _catalogExport.Length; } }

        internal string GetCatalogEntry(int index)
        {
            var snapshot = _catalogExport;
            return index >= 0 && index < snapshot.Length ? snapshot[index] : string.Empty;
        }

        internal void ApplyControlState(bool aim, bool esp, bool menu, bool consent)
        {
            _aimEnabled = aim;
            _espEnabled = esp;
            _privateLobbyConsent = consent;
            if (_menuOpen != menu)
            {
                _menuOpen = menu;
                UpdateInputCapture();
            }
        }

        private void Update()
        {
            Bootstrap.Tick();
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
        }

        private void LateUpdate()
        {
            if (_espEnabled && Time.unscaledTime >= _nextProjectionAt)
            {
                _nextProjectionAt = Time.unscaledTime + ProjectionInterval;
                UpdateOverlayProjection();
            }
            if (!_aimEnabled || _menuOpen) { ClearTarget(true); return; }
            UpdateAim();
        }

        private void OnDestroy()
        {
            ClearTarget(true);
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
            _catalogAnchor = 0;
            _selectedSpawn = null;
            _selectionConfirmed = false;
            _catalog.Clear();
        }

        private void UpdateAim()
        {
            try
            {
                var local = Player.LocalPlayer;
                if (local == null || local.BlockInputs || !Input.GetMouseButton(1)) { ClearTarget(true); return; }
                var held = local.Holding != null ? local.Holding.HeldItem : null;
                var weapon = held != null ? held.Weapon : null;
                if (weapon == null || !weapon.IsAds || local.CurCam == null) { ClearTarget(true); return; }
                var camera = local.CurCam;
                if (Time.unscaledTime >= _nextTargetRefreshAt || !TryGetLockedTargetPosition(camera, out _lockedPosition, out _lockedDistance))
                {
                    _nextTargetRefreshAt = Time.unscaledTime + TargetRefreshInterval;
                    object candidate; RuntimeTargetKind kind; Vector3 position; float distance; int priority;
                    if (!FindBestTarget(camera, out candidate, out kind, out position, out distance, out priority)) { ClearTarget(true); return; }
                    var currentPriority = TargetPriority(_lockedTarget, _lockedKind);
                    if (_lockedTarget == null || candidate == _lockedTarget || priority < currentPriority || distance < _lockedDistance * 0.9f)
                    {
                        _lockedTarget = candidate; _lockedKind = kind; _lockedPosition = position; _lockedDistance = distance;
                    }
                }
                if (!TryGetLockedTargetPosition(camera, out _lockedPosition, out _lockedDistance)) { ClearTarget(true); return; }
                var direction = _lockedPosition - camera.transform.position;
                if (!IsFinite(direction) || direction.sqrMagnitude < 0.001f) { ClearTarget(true); return; }
                ApplyRecoilCompensation(local, weapon, _lockedPosition);
                var desired = Quaternion.LookRotation(direction.normalized, Vector3.up).eulerAngles;
                var current = camera.transform.rotation.eulerAngles;
                var blend = 1f - Mathf.Exp(-_smoothing * Time.unscaledDeltaTime);
                var maxStep = _maxRotationSpeed * Time.unscaledDeltaTime;
                var pitch = Mathf.Clamp(Mathf.DeltaAngle(current.x, desired.x) * blend, -maxStep, maxStep);
                var yaw = Mathf.Clamp(Mathf.DeltaAngle(current.y, desired.y) * blend, -maxStep, maxStep);
                var next = new Vector3(current.x + pitch, current.y + yaw, 0f);
                if (CameraRotationField != null) CameraRotationField.SetValue(local.Camera, next);
                camera.transform.rotation = Quaternion.Euler(next);
                LastErrorCode = 0;
            }
            catch { LastErrorCode = 101; ClearTarget(true); }
        }

        private void ApplyRecoilCompensation(Player local, Weapon weapon, Vector3 targetPosition)
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
            if (ResetToolRecoilMethod != null && local.ToolMovement != null) ResetToolRecoilMethod.Invoke(local.ToolMovement, null);
            try
            {
                var firePoint = weapon.Attachments != null ? weapon.Attachments.FirePoint : null;
                if (firePoint != null)
                {
                    var delta = targetPosition - firePoint.position;
                    if (delta.sqrMagnitude > 0.001f) firePoint.rotation = Quaternion.LookRotation(delta.normalized, Vector3.up);
                }
            }
            catch { }
        }

        private bool FindBestTarget(Camera camera, out object bestTarget, out RuntimeTargetKind bestKind, out Vector3 bestPosition, out float bestDistance, out int bestPriority)
        {
            bestTarget = null; bestKind = RuntimeTargetKind.None; bestPosition = Vector3.zero; bestDistance = float.MaxValue; bestPriority = int.MaxValue;
            var origin = camera.transform.position;
            var manager = CreatureManager.Instance;
            var creatures = manager != null && AliveCreaturesField != null ? AliveCreaturesField.GetValue(manager) as List<Creature> : null;
            if (creatures != null)
                for (var i = 0; i < creatures.Count; i++)
                {
                    var creature = creatures[i];
                    if (creature == null || creature.IsDead) continue;
                    var fish = creature is Fish;
                    if (!_allCreatures && !fish) continue;
                    ConsiderTarget(creature, RuntimeTargetKind.Creature, CreatureHeadPosition(creature), creature.transform, fish ? 0 : 1, origin, ref bestTarget, ref bestKind, ref bestPosition, ref bestDistance, ref bestPriority);
                }
            if (_privateLobbyConsent)
                for (var i = 0; i < PlayerManager.OtherPlayers.Count; i++)
                {
                    var player = PlayerManager.OtherPlayers[i];
                    if (player == null || player == Player.LocalPlayer || player.Vitals == null || player.Vitals.Health <= 0 || player.Body == null || player.Body.Head == null) continue;
                    ConsiderTarget(player, RuntimeTargetKind.Player, player.Body.Head.position, player.Body.Head, 2, origin, ref bestTarget, ref bestKind, ref bestPosition, ref bestDistance, ref bestPriority);
                }
            return bestTarget != null;
        }

        private void ConsiderTarget(object target, RuntimeTargetKind kind, Vector3 position, Transform targetTransform, int priority, Vector3 origin, ref object bestTarget, ref RuntimeTargetKind bestKind, ref Vector3 bestPosition, ref float bestDistance, ref int bestPriority)
        {
            if (!IsFinite(position)) return;
            var distance = Vector3.Distance(position, origin);
            if (distance <= 0.01f || distance > _maxAimDistance || priority > bestPriority || (priority == bestPriority && distance >= bestDistance)) return;
            if (!_ignoreOcclusion && IsObstructed(origin, position, targetTransform)) return;
            bestTarget = target; bestKind = kind; bestPosition = position; bestDistance = distance; bestPriority = priority;
        }

        private bool TryGetLockedTargetPosition(Camera camera, out Vector3 position, out float distance)
        {
            position = Vector3.zero; distance = float.MaxValue; Transform targetTransform;
            if (_lockedKind == RuntimeTargetKind.Creature)
            {
                var creature = _lockedTarget as Creature;
                if (creature == null || creature.IsDead || (!_allCreatures && !(creature is Fish))) return false;
                position = CreatureHeadPosition(creature); targetTransform = creature.transform;
            }
            else if (_lockedKind == RuntimeTargetKind.Player)
            {
                var player = _lockedTarget as Player;
                if (!_privateLobbyConsent || player == null || player.Vitals == null || player.Vitals.Health <= 0 || player.Body == null || player.Body.Head == null) return false;
                targetTransform = player.Body.Head; position = targetTransform.position;
            }
            else return false;
            if (!IsFinite(position)) return false;
            distance = Vector3.Distance(camera.transform.position, position);
            return distance <= _maxAimDistance && (_ignoreOcclusion || !IsObstructed(camera.transform.position, position, targetTransform));
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
                    if ((bounds.ClosestPoint(position) - position).sqrMagnitude > 1f) position = bounds.center;
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

        private static int TargetPriority(object target, RuntimeTargetKind kind)
        {
            if (kind == RuntimeTargetKind.Creature) return target is Fish ? 0 : 1;
            return kind == RuntimeTargetKind.Player ? 2 : int.MaxValue;
        }

        private void ClearTarget(bool resetTool)
        {
            if (resetTool && _lockedTarget != null)
                try
                {
                    var local = Player.LocalPlayer;
                    if (local != null && local.ToolMovement != null && ResetToolRecoilMethod != null) ResetToolRecoilMethod.Invoke(local.ToolMovement, null);
                }
                catch { }
            _lockedTarget = null; _lockedKind = RuntimeTargetKind.None; _lockedDistance = float.MaxValue; _lockedPosition = Vector3.zero;
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
                    ((int)entry.Source).ToString(), ((int)entry.Category).ToString(), ((int)entry.Safety).ToString(), ExportText(entry.SafetyReason)
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
            _catalog.Add(new SpawnCatalogEntry { Id = id, DisplayName = string.IsNullOrEmpty(display) ? item.name : display, SpawnKey = key, Item = item, Prefab = item.gameObject, Source = source, Category = category, Safety = safety, SafetyReason = reason, InstanceId = item.GetInstanceID() });
        }

        private void AddEngineEntries(HashSet<int> seen)
        {
            try
            {
                var objects = Resources.FindObjectsOfTypeAll<GameObject>(); var added = 0;
                for (var i = 0; i < objects.Length && added < MaxEngineEntries; i++)
                {
                    var prefab = objects[i];
                    if (prefab == null || prefab.scene.IsValid() || prefab.GetComponent<Item>() != null || !seen.Add(prefab.GetInstanceID())) continue;
                    var blocked = IsHardBlockedEngineObject(prefab);
                    _catalog.Add(new SpawnCatalogEntry { Id = -1, DisplayName = string.IsNullOrEmpty(prefab.name) ? "<unnamed>" : prefab.name, SpawnKey = prefab.name ?? string.Empty, Prefab = prefab, Source = SpawnCatalogSource.Engine, Category = SpawnCatalogCategory.Engine, Safety = blocked ? RuntimeSpawnSafety.Blocked : RuntimeSpawnSafety.HighRiskLocal, SafetyReason = blocked ? "角色、服务器、相机、UI 或网络管理对象" : "仅本机实例化，不通过物品或网络系统", InstanceId = prefab.GetInstanceID() });
                    added++;
                }
            }
            catch { LastErrorCode = 402; }
        }

        private static bool IsHardBlockedEngineObject(GameObject prefab)
        {
            if (prefab.GetComponent<Camera>() != null) return true;
            var components = prefab.GetComponents<Component>();
            for (var i = 0; i < components.Length; i++)
            {
                if (components[i] == null) continue;
                var name = components[i].GetType().Name.ToLowerInvariant();
                if (name.Contains("player") || name.Contains("server") || name.Contains("network") || name.Contains("eventsystem") || name == "canvas" || name == "gameinfo") return true;
            }
            return false;
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
                        UseSpawnCommandMethod.Invoke(null, new object[] { entry.SpawnKey, false }); _lastNativeSpawnAt = Time.unscaledTime; SelectedSpawnState = 4; return;
                    }
                    if (_privateLobbyConsent && entry.Id >= 0 && entry.Id <= 255 && entry.Safety == RuntimeSpawnSafety.Safe && (entry.Category == SpawnCatalogCategory.Item || entry.Category == SpawnCatalogCategory.Fishing || entry.Category == SpawnCatalogCategory.Weapon))
                    {
                        var server = Server.Instance; if (server == null) { SelectedSpawnState = -9; return; }
                        var camera = local.CurCam; var position = camera != null ? camera.transform.position + camera.transform.forward * 2f : local.Transform.position; var rotation = camera != null ? camera.transform.rotation : local.Transform.rotation;
                        server.BuyItem((byte)entry.Id, local, null, position, rotation, true); _lastNativeSpawnAt = Time.unscaledTime; SelectedSpawnState = 4; return;
                    }
                    SelectedSpawnState = -10; return;
                }
                if (Time.unscaledTime - _lastRawSpawnAt < RawSpawnCooldown || _rawClones.Count >= MaxRawClones) { SelectedSpawnState = -11; return; }
                if (!_highRiskEnabled || entry.Safety != RuntimeSpawnSafety.HighRiskLocal || entry.Prefab == null || IsHardBlockedEngineObject(entry.Prefab)) { SelectedSpawnState = -12; return; }
                var camera2 = Player.LocalPlayer != null ? Player.LocalPlayer.CurCam : GameInfo.CurCamera;
                if (camera2 == null) { SelectedSpawnState = -8; return; }
                var clone = UnityEngine.Object.Instantiate(entry.Prefab, camera2.transform.position + camera2.transform.forward * 2f, camera2.transform.rotation);
                clone.name = "HTF.Local." + entry.Prefab.name; _rawClones.Add(clone); _lastRawSpawnAt = Time.unscaledTime; SelectedSpawnState = 5;
            }
            catch { SelectedSpawnState = -20; LastErrorCode = 403; }
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
                _windowRect = GUI.Window(0x485446, _windowRect, DrawWindow, "How to Fish Trainer v0.3.0rc2.post1");
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
            GUILayout.FlexibleSpace(); GUILayout.Label("Insert 关闭面板 | F8 生成 | F10 安全退出"); GUI.DragWindow(new Rect(0f, 0f, 10000f, 24f));
        }

        private void DrawCombatTab()
        {
            var next = GUILayout.Toggle(_aimEnabled, "F9 360° 最近目标锁定"); if (next != _aimEnabled) Bootstrap.SetAimEnabled(next); _aimEnabled = next;
            _allCreatures = GUILayout.Toggle(_allCreatures, "包括其他生物（默认仅鱼）"); _ignoreOcclusion = GUILayout.Toggle(_ignoreOcclusion, "忽略墙体遮挡");
            GUILayout.Label(string.Format("最大距离: {0:0}m", _maxAimDistance)); _maxAimDistance = GUILayout.HorizontalSlider(_maxAimDistance, 10f, 300f);
            GUILayout.Label(string.Format("平滑速度: {0:0}", _smoothing)); _smoothing = GUILayout.HorizontalSlider(_smoothing, 1f, 60f);
            GUILayout.Label(string.Format("后坐力补偿: {0:0}%", _recoilCompensation * 100f)); _recoilCompensation = GUILayout.HorizontalSlider(_recoilCompensation, 0f, 1f);
            GUILayout.Label("持枪 ADS + 按住右键；世界距离最近，允许屏幕后方目标。");
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
            _highRiskEnabled = GUILayout.Toggle(_highRiskEnabled, "允许高风险本地对象（不同步，最多 20 个）");
            if (_selectedSpawn != null)
            {
                GUILayout.Label(string.Format("当前: {0} | 来源 {1} | {2}", _selectedSpawn.DisplayName, _selectedSpawn.Source, SafetyText(_selectedSpawn)));
                if (!_selectionConfirmed && _selectedSpawn.Safety != RuntimeSpawnSafety.Blocked && GUILayout.Button("确认选择（10 秒内按 F8）")) ConfirmSelection();
            }
            GUILayout.Label(string.Format("目录: {0} 项 | 生成状态: {1}", _catalog.Count, SelectedSpawnState));
            _spawnScroll = GUILayout.BeginScrollView(_spawnScroll); var lastSource = (SpawnCatalogSource)(-1); var lastCategory = (SpawnCatalogCategory)(-1); var search = (_catalogSearch ?? string.Empty).Trim().ToLowerInvariant();
            for (var i = 0; i < _catalog.Count; i++)
            {
                var entry = _catalog[i]; if (_catalogFilter >= 0 && (int)entry.Category != _catalogFilter) continue;
                if (search.Length != 0 && !(entry.DisplayName ?? string.Empty).ToLowerInvariant().Contains(search) && !(entry.SpawnKey ?? string.Empty).ToLowerInvariant().Contains(search) && !entry.Id.ToString().Contains(search)) continue;
                if (entry.Source != lastSource || entry.Category != lastCategory) { GUILayout.Space(5f); GUILayout.Label(string.Format("{0} / {1}", SourceText(entry.Source), CategoryText(entry.Category))); lastSource = entry.Source; lastCategory = entry.Category; }
                GUI.enabled = entry.Safety != RuntimeSpawnSafety.Blocked; var idText = entry.Id >= 0 ? entry.Id.ToString() : "--"; var marker = entry == _selectedSpawn ? "> " : string.Empty;
                if (GUILayout.Button(string.Format("{0}[{1}] {2}  {3}", marker, idText, entry.DisplayName, SafetyText(entry)))) SelectEntry(entry); GUI.enabled = true;
            }
            GUILayout.EndScrollView();
        }

        private void DrawExperimentTab()
        {
            var next = GUILayout.Toggle(_privateLobbyConsent, "好友/私有测试房（允许玩家锁定和客户端物品请求）"); if (next != _privateLobbyConsent) Bootstrap.SetPrivateLobbyConsent(next); _privateLobbyConsent = next;
            GUILayout.Label("不会伪造房主或服务器权限；原始引擎对象始终仅本机显示。"); GUILayout.Label(string.Format("客户端物品请求状态: {0}", ClientSpawnState));
        }

        private void DrawDiagnosticsTab()
        {
            GUILayout.Label(string.Format("锁定目标类型: {0}", _lockedKind)); GUILayout.Label(string.Format("锁定距离: {0:0.0}m", _lockedDistance)); GUILayout.Label(string.Format("ESP 对象数: {0}", EspCount)); GUILayout.Label(string.Format("目录对象数: {0}", _catalog.Count)); GUILayout.Label(string.Format("本地高风险克隆: {0}/{1}", _rawClones.Count, MaxRawClones)); GUILayout.Label(string.Format("最后错误码: {0}", LastErrorCode));
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
