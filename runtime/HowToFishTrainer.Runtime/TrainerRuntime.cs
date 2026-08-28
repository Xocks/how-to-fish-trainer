using System;
using System.Collections.Generic;
using System.Reflection;
using UnityEngine;

namespace HowToFishTrainer.Runtime
{
    public static class Bootstrap
    {
        private static TrainerRuntimeBehaviour _instance;
        private static volatile bool _aimEnabled;
        private static volatile bool _espEnabled;
        private static volatile bool _menuOpen;
        private static volatile bool _privateLobbyConsent;
        private static volatile bool _shutdownRequested;
        private static volatile int _clientSpawnRequest = -1;

        public static bool Initialize()
        {
            if (_instance != null)
                return true;

            var host = new GameObject("HowToFishTrainer.Runtime");
            UnityEngine.Object.DontDestroyOnLoad(host);
            _instance = host.AddComponent<TrainerRuntimeBehaviour>();
            _instance.ApplyControlState(
                _aimEnabled,
                _espEnabled,
                _menuOpen,
                _privateLobbyConsent);
            return true;
        }

        public static void SetAimEnabled(bool value)
        {
            _aimEnabled = value;
        }

        public static void SetEspEnabled(bool value)
        {
            _espEnabled = value;
        }

        public static void SetMenuOpen(bool value)
        {
            _menuOpen = value;
        }

        public static void SetPrivateLobbyConsent(bool value)
        {
            _privateLobbyConsent = value;
        }

        public static bool GetAimEnabled() { return _aimEnabled; }
        public static bool GetEspEnabled() { return _espEnabled; }
        public static bool GetMenuOpen() { return _menuOpen; }

        public static void ConfigureAim(float maxDistance, float acquireAngle, float breakAngle, float smoothing)
        {
            if (_instance != null)
                _instance.ConfigureAim(maxDistance, acquireAngle, breakAngle, smoothing);
        }

        public static void ConfigureEsp(float maxDistance, int maxLabels)
        {
            if (_instance != null)
                _instance.ConfigureEsp(maxDistance, maxLabels);
        }

        public static int GetEspCount()
        {
            return _instance != null ? _instance.EspCount : 0;
        }

        public static int GetAimTargetKind()
        {
            return _instance != null ? _instance.AimTargetKind : 0;
        }

        public static int GetLastErrorCode()
        {
            return _instance != null ? _instance.LastErrorCode : 0;
        }

        public static int GetStatusWord()
        {
            var value = 0;
            if (_aimEnabled) value |= 1;
            if (_espEnabled) value |= 2;
            if (_menuOpen) value |= 4;
            if (_privateLobbyConsent) value |= 8;
            if (_instance != null)
            {
                value |= (_instance.AimTargetKind & 0x3) << 8;
                value |= (Mathf.Clamp(_instance.EspCount, 0, 0x7FFF) & 0x7FFF) << 16;
            }
            return value;
        }

        public static bool GetPrivateLobbyConsent()
        {
            return _privateLobbyConsent;
        }

        public static int RequestClientItem(int itemId)
        {
            if (!_privateLobbyConsent || _instance == null || itemId < 0 || itemId > 255)
                return 0;
            if (_instance.ClientSpawnState == 1 || _instance.ClientSpawnState == 2)
                return 0;
            _instance.ClientSpawnState = 1;
            _clientSpawnRequest = itemId;
            return 1;
        }

        public static int GetClientSpawnState()
        {
            return _instance != null ? _instance.ClientSpawnState : 0;
        }

        public static void ResetClientSpawnState()
        {
            if (_instance != null && _instance.ClientSpawnState != 1 && _instance.ClientSpawnState != 2)
                _instance.ClientSpawnState = 0;
        }

        public static void Shutdown()
        {
            _aimEnabled = false;
            _espEnabled = false;
            _menuOpen = false;
            _privateLobbyConsent = false;
            _clientSpawnRequest = -1;
            _shutdownRequested = true;
        }

        internal static void Tick()
        {
            if (_instance == null)
                return;
            _instance.ApplyControlState(
                _aimEnabled,
                _espEnabled,
                _menuOpen,
                _privateLobbyConsent);
            if (_shutdownRequested)
            {
                _shutdownRequested = false;
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

    internal enum RuntimeTargetKind
    {
        None = 0,
        Creature = 1,
        Player = 2,
    }

    internal enum OverlayKind
    {
        Item = 1,
        Fish = 2,
        Weapon = 3,
        Quest = 4,
        Dangerous = 5,
    }

    internal sealed class OverlayEntry
    {
        internal int InstanceId;
        internal string Name;
        internal Vector3 Screen;
        internal float Distance;
        internal bool Obstructed;
        internal OverlayKind Kind;
    }

    [DefaultExecutionOrder(10000)]
    public sealed class TrainerRuntimeBehaviour : MonoBehaviour
    {
        private const float SnapshotInterval = 0.1f;
        private const float DefaultMaxAimDistance = 120f;
        private const float DefaultAcquireAngle = 12f;
        private const float DefaultBreakAngle = 18f;
        private const float DefaultSmoothing = 18f;
        private const float DefaultMaxRotationSpeed = 540f;
        private const float DefaultEspDistance = 150f;
        private const int DefaultMaxLabels = 200;

        private static readonly FieldInfo AliveCreaturesField = typeof(CreatureManager).GetField(
            "_aliveCreatures",
            BindingFlags.Instance | BindingFlags.NonPublic);
        private static readonly FieldInfo CameraRotationField = typeof(PlayerCamera).GetField(
            "_rot",
            BindingFlags.Instance | BindingFlags.NonPublic);

        private readonly List<OverlayEntry> _overlayEntries = new List<OverlayEntry>(DefaultMaxLabels);
        private bool _aimEnabled;
        private bool _espEnabled;
        private bool _menuOpen;
        private bool _privateLobbyConsent;
        private float _maxAimDistance = DefaultMaxAimDistance;
        private float _acquireAngle = DefaultAcquireAngle;
        private float _breakAngle = DefaultBreakAngle;
        private float _smoothing = DefaultSmoothing;
        private float _maxRotationSpeed = DefaultMaxRotationSpeed;
        private float _maxEspDistance = DefaultEspDistance;
        private int _maxLabels = DefaultMaxLabels;
        private float _nextSnapshotAt;
        private object _lockedTarget;
        private RuntimeTargetKind _lockedKind;
        private GUIStyle _labelStyle;
        private GUIStyle _shadowStyle;
        private Rect _windowRect = new Rect(24f, 80f, 420f, 430f);
        private int _tab;
        private CursorLockMode _previousLockMode;
        private bool _previousCursorVisible;
        private bool _cursorStateSaved;

        public int EspCount { get; private set; }
        public int AimTargetKind { get { return (int)_lockedKind; } }
        public int LastErrorCode { get; private set; }
        public int ClientSpawnState { get; internal set; }
        private float _clientSpawnStartedAt;
        private int _previousHeldItemId;

        internal void ApplyControlState(bool aim, bool esp, bool menu, bool consent)
        {
            _aimEnabled = aim;
            _espEnabled = esp;
            _privateLobbyConsent = consent;
            if (_menuOpen != menu)
            {
                _menuOpen = menu;
                UpdateCursorState();
            }
        }

        internal void ConfigureAim(float maxDistance, float acquireAngle, float breakAngle, float smoothing)
        {
            _maxAimDistance = Mathf.Clamp(maxDistance, 10f, 300f);
            _acquireAngle = Mathf.Clamp(acquireAngle, 1f, 45f);
            _breakAngle = Mathf.Clamp(breakAngle, _acquireAngle, 60f);
            _smoothing = Mathf.Clamp(smoothing, 1f, 60f);
        }

        internal void ConfigureEsp(float maxDistance, int maxLabels)
        {
            _maxEspDistance = Mathf.Clamp(maxDistance, 10f, 500f);
            _maxLabels = Mathf.Clamp(maxLabels, 20, 500);
        }

        private void Update()
        {
            Bootstrap.Tick();
            ProcessClientSpawnRequest();
            if (_menuOpen)
                KeepCursorAvailable();
            if (_espEnabled && Time.unscaledTime >= _nextSnapshotAt)
            {
                _nextSnapshotAt = Time.unscaledTime + SnapshotInterval;
                CaptureOverlaySnapshot();
            }
            else if (!_espEnabled && _overlayEntries.Count != 0)
            {
                _overlayEntries.Clear();
                EspCount = 0;
            }
        }

        private void LateUpdate()
        {
            if (!_aimEnabled || _menuOpen)
            {
                ClearTarget();
                return;
            }
            UpdateAim();
        }

        private void OnDestroy()
        {
            ClearTarget();
            RestoreCursorState();
            _overlayEntries.Clear();
        }

        private void UpdateAim()
        {
            try
            {
                var local = Player.LocalPlayer;
                if (local == null || local.BlockInputs || !Input.GetMouseButton(1))
                {
                    ClearTarget();
                    return;
                }

                var held = local.Holding != null ? local.Holding.HeldItem : null;
                var weapon = held != null ? held.Weapon : null;
                if (weapon == null || !weapon.IsAds || local.CurCam == null)
                {
                    ClearTarget();
                    return;
                }

                var camera = local.CurCam;
                Vector3 targetPosition;
                if (!TryGetLockedTargetPosition(camera, out targetPosition))
                {
                    if (!FindBestTarget(camera, out _lockedTarget, out _lockedKind, out targetPosition))
                    {
                        ClearTarget();
                        return;
                    }
                }

                var direction = targetPosition - camera.transform.position;
                if (direction.sqrMagnitude < 0.001f)
                    return;

                var desired = Quaternion.LookRotation(direction.normalized, Vector3.up).eulerAngles;
                var current = camera.transform.rotation.eulerAngles;
                var blend = 1f - Mathf.Exp(-_smoothing * Time.unscaledDeltaTime);
                var maxStep = _maxRotationSpeed * Time.unscaledDeltaTime;
                var pitchStep = Mathf.Clamp(
                    Mathf.DeltaAngle(current.x, desired.x) * blend,
                    -maxStep,
                    maxStep);
                var yawStep = Mathf.Clamp(
                    Mathf.DeltaAngle(current.y, desired.y) * blend,
                    -maxStep,
                    maxStep);
                var next = new Vector3(current.x + pitchStep, current.y + yawStep, 0f);

                if (CameraRotationField != null && local.Camera != null)
                    CameraRotationField.SetValue(local.Camera, next);
                camera.transform.rotation = Quaternion.Euler(next);
                LastErrorCode = 0;
            }
            catch
            {
                LastErrorCode = 101;
                ClearTarget();
            }
        }

        private bool FindBestTarget(
            Camera camera,
            out object bestTarget,
            out RuntimeTargetKind bestKind,
            out Vector3 bestPosition)
        {
            bestTarget = null;
            bestKind = RuntimeTargetKind.None;
            bestPosition = Vector3.zero;
            var bestAngle = _acquireAngle;
            var bestDistance = float.MaxValue;
            var origin = camera.transform.position;
            var forward = camera.transform.forward;

            var manager = CreatureManager.Instance;
            var creatures = manager != null && AliveCreaturesField != null
                ? AliveCreaturesField.GetValue(manager) as List<Creature>
                : null;
            if (creatures != null)
            {
                for (var index = 0; index < creatures.Count; index++)
                {
                    var creature = creatures[index];
                    if (creature == null || creature.IsDead)
                        continue;
                    var position = CreatureHeadPosition(creature);
                    ConsiderTarget(
                        creature,
                        RuntimeTargetKind.Creature,
                        position,
                        creature.transform,
                        origin,
                        forward,
                        ref bestTarget,
                        ref bestKind,
                        ref bestPosition,
                        ref bestAngle,
                        ref bestDistance);
                }
            }

            if (_privateLobbyConsent)
            {
                for (var index = 0; index < PlayerManager.OtherPlayers.Count; index++)
                {
                    var player = PlayerManager.OtherPlayers[index];
                    if (player == null || player == Player.LocalPlayer || player.Vitals == null || player.Vitals.Health <= 0)
                        continue;
                    var head = player.Body != null ? player.Body.Head : null;
                    if (head == null)
                        continue;
                    ConsiderTarget(
                        player,
                        RuntimeTargetKind.Player,
                        head.position,
                        head,
                        origin,
                        forward,
                        ref bestTarget,
                        ref bestKind,
                        ref bestPosition,
                        ref bestAngle,
                        ref bestDistance);
                }
            }
            return bestTarget != null;
        }

        private void ConsiderTarget(
            object target,
            RuntimeTargetKind kind,
            Vector3 position,
            Transform targetTransform,
            Vector3 origin,
            Vector3 forward,
            ref object bestTarget,
            ref RuntimeTargetKind bestKind,
            ref Vector3 bestPosition,
            ref float bestAngle,
            ref float bestDistance)
        {
            var offset = position - origin;
            var distance = offset.magnitude;
            if (distance <= 0.01f || distance > _maxAimDistance)
                return;
            var angle = Vector3.Angle(forward, offset);
            if (angle > bestAngle || (Mathf.Approximately(angle, bestAngle) && distance >= bestDistance))
                return;
            if (IsObstructed(origin, position, targetTransform))
                return;
            bestTarget = target;
            bestKind = kind;
            bestPosition = position;
            bestAngle = angle;
            bestDistance = distance;
        }

        private bool TryGetLockedTargetPosition(Camera camera, out Vector3 position)
        {
            position = Vector3.zero;
            Transform targetTransform = null;
            if (_lockedKind == RuntimeTargetKind.Creature)
            {
                var creature = _lockedTarget as Creature;
                if (creature == null || creature.IsDead)
                    return false;
                position = CreatureHeadPosition(creature);
                targetTransform = creature.transform;
            }
            else if (_lockedKind == RuntimeTargetKind.Player)
            {
                var player = _lockedTarget as Player;
                if (!_privateLobbyConsent || player == null || player.Vitals == null || player.Vitals.Health <= 0 || player.Body == null)
                    return false;
                targetTransform = player.Body.Head;
                if (targetTransform == null)
                    return false;
                position = targetTransform.position;
            }
            else
            {
                return false;
            }

            var origin = camera.transform.position;
            var delta = position - origin;
            return delta.sqrMagnitude <= _maxAimDistance * _maxAimDistance
                && Vector3.Angle(camera.transform.forward, delta) <= _breakAngle
                && !IsObstructed(origin, position, targetTransform);
        }

        private static Vector3 CreatureHeadPosition(Creature creature)
        {
            return creature.transform.position + Vector3.up * creature.HeadPos;
        }

        private static bool IsObstructed(Vector3 origin, Vector3 target, Transform targetTransform)
        {
            RaycastHit hit;
            if (!Physics.Linecast(origin, target, out hit, Physics.DefaultRaycastLayers, QueryTriggerInteraction.Ignore))
                return false;
            if (hit.transform == null || targetTransform == null)
                return true;
            return hit.transform != targetTransform
                && !hit.transform.IsChildOf(targetTransform)
                && !targetTransform.IsChildOf(hit.transform);
        }

        private void ClearTarget()
        {
            _lockedTarget = null;
            _lockedKind = RuntimeTargetKind.None;
        }

        private void CaptureOverlaySnapshot()
        {
            _overlayEntries.Clear();
            try
            {
                var local = Player.LocalPlayer;
                var camera = local != null ? local.CurCam : GameInfo.CurCamera;
                if (camera == null)
                {
                    EspCount = 0;
                    return;
                }
                var origin = camera.transform.position;
                foreach (var pair in ItemManager.Items)
                {
                    var transform = pair.Key;
                    var item = pair.Value;
                    if (transform == null
                        || item == null
                        || item.DeadPlayer != null
                        || item.HasPlayerHolder
                        || item.IsInInventory
                        || !item.gameObject.activeInHierarchy)
                        continue;
                    AddOverlayEntry(camera, origin, item, transform);
                }
                _overlayEntries.Sort((left, right) => left.Distance.CompareTo(right.Distance));
                if (_overlayEntries.Count > _maxLabels)
                    _overlayEntries.RemoveRange(_maxLabels, _overlayEntries.Count - _maxLabels);
                EspCount = _overlayEntries.Count;
                LastErrorCode = 0;
            }
            catch
            {
                LastErrorCode = 201;
                _overlayEntries.Clear();
                EspCount = 0;
            }
        }

        private void ProcessClientSpawnRequest()
        {
            if (ClientSpawnState == 1)
            {
                var itemId = Bootstrap.TakeClientSpawnRequest();
                if (itemId < 0)
                    return;
                try
                {
                    var local = Player.LocalPlayer;
                    var server = Server.Instance;
                    var prefab = GameInfo.GetSpawnable((byte)itemId);
                    if (!_privateLobbyConsent || local == null || server == null || prefab == null)
                    {
                        ClientSpawnState = -1;
                        return;
                    }
                    var normalizedName = (prefab.name ?? string.Empty).Replace(" ", string.Empty).ToLowerInvariant();
                    if (prefab.DeadPlayer != null
                        || prefab.Creature != null
                        || prefab.IsQuestItem
                        || normalizedName == "deadplayer"
                        || normalizedName == "dynamite")
                    {
                        ClientSpawnState = -2;
                        return;
                    }
                    var holding = local.Holding;
                    if (holding == null || holding.UninitializedHeldItem != null)
                    {
                        ClientSpawnState = -3;
                        return;
                    }
                    var previous = holding.HeldItem;
                    _previousHeldItemId = previous != null ? previous.GetInstanceID() : 0;
                    var camera = local.CurCam;
                    var position = camera != null
                        ? camera.transform.position + camera.transform.forward * 2f
                        : local.Transform.position;
                    var rotation = camera != null ? camera.transform.rotation : local.Transform.rotation;
                    server.BuyItem((byte)itemId, local, null, position, rotation, true);
                    _clientSpawnStartedAt = Time.unscaledTime;
                    ClientSpawnState = 2;
                }
                catch
                {
                    ClientSpawnState = -5;
                    LastErrorCode = 301;
                }
            }
            else if (ClientSpawnState == 2)
            {
                var local = Player.LocalPlayer;
                var held = local != null && local.Holding != null ? local.Holding.HeldItem : null;
                if (held != null && held.GetInstanceID() != _previousHeldItemId)
                {
                    ClientSpawnState = 3;
                }
                else if (Time.unscaledTime - _clientSpawnStartedAt > 3f)
                {
                    ClientSpawnState = -7;
                }
            }
        }

        private void AddOverlayEntry(Camera camera, Vector3 origin, Item item, Transform transform)
        {
            var world = transform.position;
            var distance = Vector3.Distance(origin, world);
            if (distance > _maxEspDistance)
                return;
            var screen = camera.WorldToScreenPoint(world);
            if (screen.z <= 0f)
                return;
            var kind = OverlayKind.Item;
            if (item.IsQuestItem)
                kind = OverlayKind.Quest;
            else if (item.Weapon != null)
                kind = OverlayKind.Weapon;
            else if (item.Creature != null)
                kind = OverlayKind.Fish;
            var name = item.GetName();
            if (string.IsNullOrWhiteSpace(name))
                name = item.name;
            _overlayEntries.Add(new OverlayEntry
            {
                InstanceId = item.GetInstanceID(),
                Name = name,
                Screen = screen,
                Distance = distance,
                Obstructed = IsObstructed(origin, world, transform),
                Kind = kind,
            });
        }

        private void OnGUI()
        {
            EnsureStyles();
            if (_espEnabled)
            {
                for (var index = 0; index < _overlayEntries.Count; index++)
                    DrawOverlayEntry(_overlayEntries[index]);
            }
            if (_menuOpen)
                _windowRect = GUI.Window(0x485446, _windowRect, DrawWindow, "How to Fish Trainer v0.3");
        }

        private void DrawOverlayEntry(OverlayEntry entry)
        {
            var color = Color.white;
            switch (entry.Kind)
            {
                case OverlayKind.Fish: color = new Color(0.3f, 0.9f, 1f); break;
                case OverlayKind.Weapon: color = new Color(1f, 0.75f, 0.2f); break;
                case OverlayKind.Quest: color = new Color(1f, 0.35f, 0.75f); break;
                case OverlayKind.Dangerous: color = new Color(1f, 0.25f, 0.25f); break;
            }
            if (entry.Obstructed)
                color = Color.Lerp(color, Color.gray, 0.65f);
            _labelStyle.normal.textColor = color;
            var text = string.Format("{0}  {1:0}m", entry.Name, entry.Distance);
            var position = new Vector2(entry.Screen.x, Screen.height - entry.Screen.y);
            var size = _labelStyle.CalcSize(new GUIContent(text));
            var rect = new Rect(position.x - size.x * 0.5f, position.y - size.y, size.x + 8f, size.y + 4f);
            GUI.Label(new Rect(rect.x + 1f, rect.y + 1f, rect.width, rect.height), text, _shadowStyle);
            GUI.Label(rect, text, _labelStyle);
        }

        private void DrawWindow(int windowId)
        {
            GUILayout.BeginHorizontal();
            if (GUILayout.Toggle(_tab == 0, "战斗", GUI.skin.button)) _tab = 0;
            if (GUILayout.Toggle(_tab == 1, "透视", GUI.skin.button)) _tab = 1;
            if (GUILayout.Toggle(_tab == 2, "实验", GUI.skin.button)) _tab = 2;
            if (GUILayout.Toggle(_tab == 3, "诊断", GUI.skin.button)) _tab = 3;
            GUILayout.EndHorizontal();
            GUILayout.Space(8f);

            if (_tab == 0)
            {
                var nextAimEnabled = GUILayout.Toggle(_aimEnabled, "F9 枪械锁头");
                if (nextAimEnabled != _aimEnabled)
                    Bootstrap.SetAimEnabled(nextAimEnabled);
                _aimEnabled = nextAimEnabled;
                GUILayout.Label(string.Format("最大距离: {0:0}m", _maxAimDistance));
                _maxAimDistance = GUILayout.HorizontalSlider(_maxAimDistance, 10f, 300f);
                GUILayout.Label(string.Format("获取角度: {0:0}°", _acquireAngle));
                _acquireAngle = GUILayout.HorizontalSlider(_acquireAngle, 1f, 45f);
                _breakAngle = Mathf.Max(_acquireAngle, _breakAngle);
                GUILayout.Label(string.Format("平滑速度: {0:0}", _smoothing));
                _smoothing = GUILayout.HorizontalSlider(_smoothing, 1f, 60f);
                GUILayout.Label("仅持枪 ADS + 按住右键时生效");
            }
            else if (_tab == 1)
            {
                var nextEspEnabled = GUILayout.Toggle(_espEnabled, "F11 物品与生物标签");
                if (nextEspEnabled != _espEnabled)
                    Bootstrap.SetEspEnabled(nextEspEnabled);
                _espEnabled = nextEspEnabled;
                GUILayout.Label(string.Format("最大距离: {0:0}m", _maxEspDistance));
                _maxEspDistance = GUILayout.HorizontalSlider(_maxEspDistance, 10f, 500f);
                GUILayout.Label(string.Format("当前标签: {0} / {1}", EspCount, _maxLabels));
            }
            else if (_tab == 2)
            {
                var nextConsent = GUILayout.Toggle(
                    _privateLobbyConsent,
                    "好友/私有测试房（允许锁定其他玩家）");
                if (nextConsent != _privateLobbyConsent)
                    Bootstrap.SetPrivateLobbyConsent(nextConsent);
                _privateLobbyConsent = nextConsent;
                GUILayout.Label("默认关闭；不会伪造房主或服务器权限。");
                GUILayout.Label(string.Format("客户端物品请求状态: {0}", ClientSpawnState));
            }
            else
            {
                GUILayout.Label(string.Format("锁定目标类型: {0}", _lockedKind));
                GUILayout.Label(string.Format("ESP 对象数: {0}", EspCount));
                GUILayout.Label(string.Format("最后错误码: {0}", LastErrorCode));
            }
            GUILayout.FlexibleSpace();
            GUILayout.Label("Insert 关闭面板 | F10 安全退出");
            GUI.DragWindow(new Rect(0f, 0f, 10000f, 24f));
        }

        private void EnsureStyles()
        {
            if (_labelStyle != null)
                return;
            _labelStyle = new GUIStyle(GUI.skin.label)
            {
                fontSize = 14,
                fontStyle = FontStyle.Bold,
                alignment = TextAnchor.MiddleCenter,
            };
            _shadowStyle = new GUIStyle(_labelStyle);
            _shadowStyle.normal.textColor = Color.black;
        }

        private void UpdateCursorState()
        {
            if (_menuOpen)
            {
                if (!_cursorStateSaved)
                {
                    _previousLockMode = Cursor.lockState;
                    _previousCursorVisible = Cursor.visible;
                    _cursorStateSaved = true;
                }
                KeepCursorAvailable();
            }
            else
            {
                RestoreCursorState();
            }
        }

        private static void KeepCursorAvailable()
        {
            Cursor.lockState = CursorLockMode.None;
            Cursor.visible = true;
        }

        private void RestoreCursorState()
        {
            if (!_cursorStateSaved)
                return;
            Cursor.lockState = _previousLockMode;
            Cursor.visible = _previousCursorVisible;
            _cursorStateSaved = false;
        }
    }
}
