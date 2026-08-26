# How to Fish - Trainer Technical Deep Dive & Architecture

A comprehensive technical breakdown of reverse engineering, memory architecture, Mono runtime interop, networking pipelines, and JIT patching for the Unity Mono game **How to Fish**.

---

## 1. Game Engine & Technology Stack

- **Game**: *How to Fish*
- **Engine**: Unity 2022/2023 x64
- **Scripting Backend**: Mono (Bleeding Edge embed runtime: `mono-2.0-bdwgc.dll`)
- **Networking Framework**: **FishNet** (`FishNet.Runtime.dll`)
- **Memory Trainer Stack**: Python 3.10+, `pymem`, x64 Windows API (`VirtualAllocEx`, `CreateRemoteThread`, `VirtualProtectEx`), `rich`

---

## 2. Reverse Engineering the Game Systems

```
+-----------------------------------------------------------------------------------+
|                                 HOW TO FISH                                       |
|                                                                                   |
|  [Incoming Hit / Weapon / NPC]       [Touching Fire / Lava / Poison]              |
|               |                                      |                            |
|               v                                      v                            |
|    PlayerVitals.LocalHit()               PlayerVitals.ApplyNewFire/Poison()       |
|    - Decrements _localHp (Prediction)    - Fills _syncedFire / _syncedPoison      |
|    - Sends Server.HitPlayer RPC          - Triggers UI fire/poison animation      |
|               |                                      |                            |
|               v                                      v                            |
|    PlayerVitals.TakeDamage()             PlayerVitals.FireTick / PoisonTick()     |
|    - Checks PlayerManager.InGodMode      - Decrements fire/poison meter           |
|    - Updates _syncedHealth (SyncVar)     - Calls TakeDamage()                     |
|               |                                      |                            |
|               +-------------------+------------------+                            |
|                                   v                                               |
|                       PlayerVitals.OnHealthChange()                               |
|                       - Updates UI fillAmount                                     |
|                       - Triggers death if _prevHealth <= 0                        |
+-----------------------------------------------------------------------------------+
```

### 2.1 The Dual-State Health Pipeline (Local vs Networked)

Unlike simple single-player games where health is a single integer in memory, *How to Fish* uses **FishNet** networking with client-side prediction:

1. **Local Prediction State (`_localHp`, `_localIsDead`)**:
   - When an NPC hits you or a projectile strikes, the client immediately executes `PlayerVitals.LocalHit(...)`.
   - `LocalHit` immediately subtracts damage from `_localHp` on the local machine so the player feels zero latency, plays hit sounds, shows hit markers, and sends a `Server.HitPlayer` RPC.
2. **Authoritative Networked State (`_syncedHealth`)**:
   - `_syncedHealth` is a FishNet `SyncVar<int>` structure managed by the host/server.
   - When damage is processed server-side, `PlayerVitals.TakeDamage(...)` subtracts from `_syncedHealth.Value`.
   - When `_syncedHealth` synchronizes over the network, `OnHealthChange(int prev, int next, bool asServer)` fires on clients, setting `_prevHealth = next` and updating the UI (`PlayerUI.SetPlayerHp`).
3. **Environmental / Hazard Damage**:
   - Poison and Fire tick functions (`PoisonTick`, `FireTick`) run periodically and call `TakeDamage`.
   - Hunger depletion (`DamageFromFullness`) runs when fullness is 0 and calls `TakeDamage`.

#### Why Only Patching `TakeDamage` is Not Enough:
If you *only* patch `TakeDamage` (or only use `InGodMode`):
- **Health Bar**: The health bar *does* stay at 100% because `TakeDamage` controls `_syncedHealth`, which drives `_prevHealth` and the UI `HealthPercent`.
- **The Catch / Side Effects**:
  1. **Elemental Gauges Stuck**: Touching fire/poison still calls `ApplyNewFire`/`ApplyNewPoison`, filling the screen with fire/poison vignette overlays. Because `TakeDamage` is blocked, the tick cycle never burns off the status properly.
  2. **Local Prediction Desync**: `LocalHit` still runs on the client when attacked, subtracting damage from `_localHp`. If `_localHp <= 0`, it sets `_localIsDead = true` locally even while the server considers you alive.
- **The Complete Solution**: We JIT-patch all 5 entry points simultaneously (`TakeDamage`, `LocalHit`, `DamageFromFullness`, `ApplyNewFire`, `ApplyNewPoison`) with `RET` (`0xC3`), and actively maintain `_localHp = 100`, `_prevHealth = 100`, and `_invulnerableUntil = 999999.0` in memory for a clean, glitch-free experience.

---

### 2.2 Elemental Gauges & Visual FX Dissipation

When touching lava or poison:
1. `PlayerVitals.ApplyNewFire()` or `ApplyNewPoison()` sets `_syncedFire.Value = 100`.
2. `OnFireChange` sets `_prevFire = 100` and animates the fire/poison vignette and HUD gauge via `VitalsUI.SetPlayerFire(...)`.
3. `FireTick()` normally burns down the fire meter over time while calling `TakeDamage`.
4. **The Gotcha**: If damage was blocked by disabling `FireTick`, the fire gauge had no way to drain and remained permanently stuck on screen at 100%.
5. **The Fix**:
   - JIT-patch `ApplyNewFire` and `ApplyNewPoison` with `RET` so fire never starts.
   - Force `_prevFire = 0` and `_prevPoison = 0` in memory, which immediately clears any existing visual overlays and resets the UI.

---

### 2.3 Jump Mechanics & The `InGodMode` Trap

The game's internal `PlayerMovement.JumpInput` method controls jumping:

```csharp
public void JumpInput(CallbackContext context) {
    if (_player.BlockInputs) return;
    if (Grounded && CanJumpGroundAngle()) { Jump(); return; }
    if (!_hasJumped && Time.time - _timeOfLastGrounded < _coyoteJumpTime && CanJumpGroundAngle()) { Jump(); return; }
    if (_isSwimming) { Jump(); return; }
    if ((OnBoat || _isTouchingBoat) && ...) { Jump(); return; }
    if (PlayerManager.InGodMode) { Jump(); return; } // <-- Developer debug bypass
}
```

- **The Developer Coupling**: The game developer built a debug flag `PlayerManager.InGodMode`. It did two unrelated things:
  1. Skipped damage in `PlayerVitals.TakeDamage`.
  2. Unlocked infinite jumping in `PlayerMovement.JumpInput`.
- **The Issue**: When Lock Health enabled `InGodMode`, the player accidentally got infinite mid-air jumps. When Infinite Jump used `InGodMode`, it accidentally made the player invincible!
- **The Solution**: We eliminated `InGodMode` completely.
  - **Lock Health (`F1`)**: Protected via direct JIT patches on `TakeDamage` + `LocalHit` (normal jump physics 100% preserved).
  - **Infinite Air Jump (`F3`)**: Installs a direct 21-byte x64 JIT trampoline on `PlayerMovement.JumpInput` that immediately executes `PlayerMovement.Jump(this)` on keypress, completely bypassing ground checks without touching God Mode or health.

---

### 2.4 Weapon & Ammo Architecture

In *How to Fish*, all firearms inherit from `Weapon` (which extends `Tool` $\rightarrow$ `Item`):

```csharp
// Weapon.Shoot() IL decompilation summary
if (this.HasCooldown() || this._isReloading || this.Ammo == 0)
    return;

this._queuedShoot = false;
// ... Recoil, screen shake, and skill triggers ...

this.Ammo = this.Ammo - 1; // Decrements Ammo via Weapon.set_Ammo(int)

if (this.Ammo == 0) {
    this._queueReload = true; // Triggers automatic reload state
} else {
    this._hasCoolDown = true;
    this.Invoke("CoolDown", this._timeBetweenShots);
}

this.ShootEffects(true);
// ... Raycast hit detection & ProjectileManager.AddProjectile ...
```

#### Why Unlimited Ammo Needs JIT Hooking + Memory Lock:
1. **The Ammo Decrement (`set_Ammo`)**: Every shot calls `set_Ammo(this.Ammo - 1)`. If ammo reaches 0, `_queueReload` is flagged, causing `Update()` to initiate `LocalReload()` and interrupt continuous firing.
2. **Infinite Ammo Implementation**:
   - **JIT Hooking**: JIT-compiles `Weapon.set_Ammo(int)` and writes `RET` (`0xC3`) at the prologue. Calls from `Shoot()` or `ShootEffects()` return immediately without modifying `<Ammo>k__BackingField`.
   - **Active State Lock**: Traverses `Player.LocalPlayer` $\rightarrow$ `_holding` $\rightarrow$ `_heldItem` $\rightarrow$ `_weapon`, setting `<Ammo>k__BackingField = 999` and clearing `_isReloading = 0` / `_queueReload = 0`.
   - Result: Continuous, uninterrupted firing with 0 reload delays or magazine depletion.

---

### 2.5 Damage Calculation & Client-Side Authority in Multiplayer

How damage flows through *How to Fish*'s multiplayer pipeline:

```
[Attacker Client]
    |
    +---> Real-time In-Memory Scaling:
    |     - Melee: SharpnessUpgrade._damage in _sharpnessUpgrades array
    |     - Guns: BulletUpgrade._damage in _bulletUpgrades array & ProjectileDamage
    |     - Fists: PlayerPunching._damage
    |
    +---> PlayerVitals.LocalHit(target, damage, ...) / Item.LocalHit(target, damage, ...)
    |
    +---> Server.Instance.HitPlayer / HitCreature(target, damage, ...)  <-- [Damage sent over RPC]
               |
               v
        [Host / Remote Server]
               |
               v
        Server.RpcLogic___HitPlayer(target, damage, ...) / TakeDamage
               |
               v
        PlayerVitals.TakeDamage(damage, ...)  <-- [Applies exact received damage]
```

#### Why Multipliers & One-Shot Work in Multiplayer Lobbies:
1. **Client-Authoritative Damage Computation**: When you attack an NPC, item, or other player, your local client calculates the final damage value from `_sharpnessUpgrades[idx]._damage`, `_bulletUpgrades[idx]._damage`, and `_damage`.
2. **RPC Transmission**: The computed integer `damage` is packaged directly into the `Server.HitPlayer` / `Server.HitCreature` network RPC and sent to the server. The host server does not recalculate base weapon values; it deducts the exact received damage from the target.
3. **Implementation Strategy**:
   - **Multipliers (`2x`, `5x`, `10x`, `One-Shot`)**: Real-time in-memory scaling dynamically updates `_damage` fields on `PlayerPunching`, the active `Melee._sharpnessUpgrades` array, the active `Attachments._bulletUpgrades` array, and `WeaponInfo.ProjectileDamage`.
   - **Zero Bytecode Overflow Risk**: Modifies 0 bytes of leaf getter machine code, completely avoiding JIT method boundary overflow and working seamlessly with Mono JIT inlining.
   - Result: 100% reliable damage scaling whether you are the Host or a Client in someone else's server.

---

### 2.6 Money System & Network Synchronization

In *How to Fish*, currency is managed globally by `MoneyManager` and displayed via `PlayerUI` / `MoneyUI`:

```csharp
public class MoneyManager : NetworkBehaviour {
    public static MoneyManager Instance;
    public readonly SyncVar<int> _money = new SyncVar<int>();
    public static int Money { get; private set; } // <Money>k__BackingField

    public static void AddMoney(int amount, Player player) {
        if ((bool)Instance && Instance.IsServerInitialized) {
            Instance._money.Value += Mathf.Abs(amount);
            Instance.ObserverMoneySound(increase: true, player);
            Instance.MoneySound(increase: true, player);
        }
    }
}
```

#### Dual State & UI Pipeline:
1. **Authoritative Field (`<Money>k__BackingField`)**:
   - `MoneyManager.Money` is read by `Purchasable.Hover()`, `ItemPurchasable.Interact()`, `Server.BuyItem()`, etc., using `MoneyManager.CanAfford(cost)`.
2. **FishNet `SyncVar<int>` (`_money`)**:
   - Holds the networked synchronizer (`FishNet.Object.Synchronizing.SyncVar<int>`), storing the active value at internal offsets `+0x6C` and `+0x70`.
3. **Floating Text & Count-Up Animation (`PlayerUI.SetMoney`)**:
   - `PlayerUI.SetMoney(int to, int diff, bool gainedMoney)` spawns a dynamic green/red floating TextMeshPro element with LeanTween upward movement and smoothly interpolates the HUD balance string `$xxxx`.
4. **Multiplayer Authority Model & Implementation Strategy (`F6`)**:
   - **Host / Singleplayer (True Synchronization)**: On keypress, reads `<Money>k__BackingField`, adds `10,000` (clamped to `2,000,000,000`), writes both the static field and `SyncVar` offsets (`+0x6C` and `+0x70`), triggers `PlayerUI.SetMoney`, and plays `MoneySound`. Because the Host is authoritative, FishNet automatically replicates the new balance to all connected clients in the lobby.
   - **Client Mode (Local Prediction & Interaction Unlock)**: In Client mode, modifying local memory allows `Purchasable.Hover()` to pass `CanAfford` checks, unlocking the `[E] Buy` prompt and playing native UI/sound effects. (Actual purchase execution via `Server.BuyItem` RPC is validated by the host against the server-side balance).

---

### 2.7 Native Item Spawner (v0.2.0 RC)

The item spawner deliberately reuses the game's developer-command path instead of constructing Unity or FishNet objects from raw memory:

1. The bridge iterates Mono method metadata and selects `GameInfo.GetSpawnable(byte)` by its exact `System.Byte` parameter type before probing IDs `0..255`. This avoids the same-count `GetSpawnable(string)` overload.
2. `Item.GetName()`, `UnityEngine.Object.get_name()`, `Item.get_Type()`, and `Item.get_IsQuestItem()` provide display, lookup, category, and risk metadata.
3. F7 displays the catalog and stores a validated selection. Quest and unknown items require a second confirmation.
4. F8 verifies `NetworkBehaviour.IsServerInitialized`, creates a managed Mono string, and invokes `DazedCommands.UseSpawnCommand(name, false)`.
5. The game command computes `Camera.CurCamera.position + Camera.CurCamera.forward * 2`, calls `Object.Instantiate`, then registers the result through FishNet `Server.Spawn`.

This path is intentionally restricted to single-player and the host. A joined client does not own FishNet server authority and is rejected before invocation. A 500 ms cooldown limits accidental object floods. Runtime catalog pointers are discarded whenever the game disconnects and rebuilt after reattachment.

The RC includes automated bridge, catalog, selector, authority, cooldown, diagnostic, and regression tests. It is not considered feature-level verified until fish, firearm, host synchronization, reconnect, and safe-exit scenarios have been exercised in the game.

---

## 3. Trainer Architecture & Mono Runtime Interop

```
+-------------------------------------------------------------------------+
|                          PYTHON TRAINER ENGINE                          |
|                                                                         |
|  [Pymem Process Handle] <---> [Win32 VirtualAllocEx / WriteProcess]     |
|                                          |                              |
|                                          v                              |
|                       +--------------------------------------+          |
|                       |   MonoBridge (mono-2.0-bdwgc.dll)    |          |
|                       +--------------------------------------+          |
|                                          |                              |
|                 +------------------------+------------------------+     |
|                 v                                                 v     |
|    [Mono TLS Auto-Attachment]                       [mono_image_loaded] |
|    - Attaches remote thread to Mono root domain     - Resolves loaded   |
|    - Prevents null TLS dereferences / crashes         Assembly-CSharp   |
|                 |                                                 |     |
|                 +------------------------+------------------------+     |
|                                          v                              |
|                       +--------------------------------------+          |
|                       |    JIT Method Compilation Engine     |          |
|                       |    - mono_compile_method()           |          |
|                       |    - Resolves native x64 pointers    |          |
|                       +--------------------------------------+          |
|                                          |                              |
|                 +------------------------+------------------------+     |
|                 v                                                 v     |
|    [MethodPatcher (RET & Trampolines)]              [Memory State Lock] |
|    - TakeDamage         -> 0xC3                     - _localHp = 100    |
|    - LocalHit           -> 0xC3                     - _prevHealth = 100 |
|    - DamageFromFullness -> 0xC3                     - _prevFullness=100 |
|    - LowerFullness      -> 0xC3                     - _invuln = 999999  |
|    - ApplyNewFire/Poison-> 0xC3                     - _prevFire/Poison=0|
|    - Weapon.set_Ammo    -> 0xC3                     - Ammo = 999        |
|    - JumpInput -> Direct Jump Trampoline            - Punching._damage  |
|                                                     - Sharpness._damage |
|                                                     - Bullets._damage   |
|                                                     - ProjectileDamage  |
+-------------------------------------------------------------------------+
```

### 3.1 Resolving Mono Runtime Structures Remotely

Unity games load Mono via `mono-2.0-bdwgc.dll`. This DLL exports C functions for the Mono Embedding API:

| Mono C API Function | Purpose in Trainer |
| :--- | :--- |
| `mono_get_root_domain` | Retrieves the primary `MonoDomain*` instance. |
| `mono_thread_attach` | Attaches calling thread to Mono GC & initializes TLS. |
| `mono_image_loaded` | Finds the `MonoImage*` for loaded assemblies (`Assembly-CSharp`). |
| `mono_class_from_name` | Finds a `MonoClass*` by namespace and class name. |
| `mono_class_get_method_from_name` | Finds a `MonoMethod*` by name and parameter count. |
| `mono_compile_method` | Forces Mono's JIT compiler to compile IL into native x64 machine code and returns the executable memory address. |
| `mono_class_vtable` & `mono_vtable_get_static_field_data` | Resolves the memory address of static fields (`Player.LocalPlayer`, `PlayerManager`). |
| `mono_field_get_offset` | Computes field offsets within class instances. |

---

### 3.2 JIT Trampolines and Machine Code Patching

When Mono compiles a C# method, it allocates an executable page (`PAGE_EXECUTE_READWRITE`) and emits native x64 instructions.

#### The `RET` Patch (`0xC3`)
For methods that return `void` (e.g. `TakeDamage`, `LocalHit`, `LowerFullness`, `set_Ammo`):
- Writing `0xC3` (`RET`) at the first byte causes the CPU to return immediately upon entering the function.
- The method body never executes; variables are untouched; performance overhead is literally zero cycles.

#### The Multiplier Bytecode Stub
For getter methods returning `int` (e.g. `BulletUpgrade.get_Damage`, `SharpnessUpgrade.get_Damage`):
```asm
; RCX = this (pointer to upgrade instance)
mov eax, dword ptr [rcx + _damage_offset] ; Load base damage into EAX
imul eax, eax, <multiplier>               ; Multiply damage by active scale factor
ret                                       ; Return scaled integer
```

#### The Jump Trampoline Patch
For `PlayerMovement.JumpInput(this, context)`:
```asm
; Parameters at entry: RCX = this (PlayerMovement*), RDX = context
sub rsp, 0x28                           ; Allocate shadow space and align stack
mov rax, 0x000001F3B485D730             ; Pointer to PlayerMovement.Jump()
call rax                                ; Execute PlayerMovement.Jump(this)
add rsp, 0x28                           ; Clean up stack frame
ret                                     ; Return to caller
```
- **Bytecode**: `\x48\x83\xEC\x28\x48\xB8` + `<8-byte address>` + `\xFF\xD0\x48\x83\xC4\x28\xC3` (21 bytes total).

---

## 4. Key Gotchas & Solutions

### Gotcha 1: The Mono TLS (Thread-Local Storage) Crash
- **Symptom**: Calling Mono functions via `CreateRemoteThread` crashed the game with access violation `0xC0000005`.
- **Cause**: Mono relies on Thread-Local Storage (`mono_domain_get()`). When a new OS thread is created by `CreateRemoteThread`, its Mono TLS slot is `NULL`. Calling Mono APIs without calling `mono_thread_attach` first causes an immediate null pointer dereference in Mono's GC/domain checks.
- **Solution**: Every remote execution stub automatically injects:
  ```asm
  sub rsp, 0x28
  mov rcx, [root_domain]
  mov rax, [mono_thread_attach]
  call rax
  ; NOW safe to call target Mono API
  ```

### Gotcha 2: Loaded Assembly Discovery
- **Symptom**: `mono_domain_assembly_open(domain, "Assembly-CSharp")` returned `NULL`.
- **Cause**: `mono_domain_assembly_open` searches disk paths for unloaded assemblies. `Assembly-CSharp` is already loaded in memory by Unity at game launch.
- **Solution**: Use `mono_image_loaded("Assembly-CSharp")`, which queries Mono's in-memory image table directly.

### Gotcha 3: Method Signature Parameter Counts
- **Symptom**: `mono_class_get_method_from_name` failed to find `JumpInput` or `TakeDamage`.
- **Cause**: In Unity's new Input System, `JumpInput` takes `(CallbackContext context)` (parameter count = 1), whereas standard methods take 0 or 4. Mono requires exact parameter counts.
- **Solution**: Reflection inspection was used to verify exact parameter counts across all methods (`JumpInput: 1`, `TakeDamage: 4`, `LocalHit: 7`, `LowerFullness: 1`, `set_Ammo: 1`, `get_Damage: 0`).

### Gotcha 4: Memory Leak & Dirty Exit
- **Symptom**: Game logic remained modified even after closing the trainer.
- **Cause**: Memory patches remained active and `_invulnerableUntil` remained set to `999999.0` in the target process.
- **Solution**:
  - Registered `atexit`, `SIGINT`, `SIGTERM` hooks.
  - Wrapped trainer execution in `try ... finally: self._cleanup()`.
  - On exit, the trainer restores all original machine code bytes, resets `InGodMode = 0`, and resets `_invulnerableUntil = 0.0`.

---

## 5. File & Component Index

| Path | Description |
| :--- | :--- |
| [`src/howtofish_cheat/mono/remote.py`](file:///c:/Users/Huan%20Wang/workspace/howtofish-pycheat/src/howtofish_cheat/mono/remote.py) | Safe x64 remote function executor with auto TLS attachment. |
| [`src/howtofish_cheat/mono/bridge.py`](file:///c:/Users/Huan%20Wang/workspace/howtofish-pycheat/src/howtofish_cheat/mono/bridge.py) | Low-level Mono runtime dissector and JIT compiler bridge. |
| [`src/howtofish_cheat/mono/patcher.py`](file:///c:/Users/Huan%20Wang/workspace/howtofish-pycheat/src/howtofish_cheat/mono/patcher.py) | Memory protection and atomic JIT bytecode patcher. |
| [`src/howtofish_cheat/features/health.py`](file:///c:/Users/Huan%20Wang/workspace/howtofish-pycheat/src/howtofish_cheat/features/health.py) | Lock Health cheat (5 JIT hooks + active memory lock + elemental dissipation). |
| [`src/howtofish_cheat/features/hunger.py`](file:///c:/Users/Huan%20Wang/workspace/howtofish-pycheat/src/howtofish_cheat/features/hunger.py) | Lock Hunger cheat (LowerFullness hooks + fullness memory lock). |
| [`src/howtofish_cheat/features/jump.py`](file:///c:/Users/Huan%20Wang/workspace/howtofish-pycheat/src/howtofish_cheat/features/jump.py) | Infinite Air Jump (pure movement JIT trampoline; zero God Mode). |
| [`src/howtofish_cheat/features/ammo.py`](file:///c:/Users/Huan%20Wang/workspace/howtofish-pycheat/src/howtofish_cheat/features/ammo.py) | Unlimited Ammo cheat (Weapon.set_Ammo JIT hook + active ammo memory lock). |
| [`src/howtofish_cheat/features/damage.py`](file:///c:/Users/Huan%20Wang/workspace/howtofish-pycheat/src/howtofish_cheat/features/damage.py) | Damage Multiplier cheat (1x, 2x, 5x, 10x, One-Shot Kill via JIT patches + memory lock). |
| [`src/howtofish_cheat/features/money.py`](file:///c:/Users/Huan%20Wang/workspace/howtofish-pycheat/src/howtofish_cheat/features/money.py) | Add Money cheat (+1w / +$10,000 on press with sound, UI float text; Host lobby sync / Client UI prediction). |
| [`src/howtofish_cheat/ui/console.py`](file:///c:/Users/Huan%20Wang/workspace/howtofish-pycheat/src/howtofish_cheat/ui/console.py) | Rich-based cross-platform terminal dashboard. |
| [`src/howtofish_cheat/trainer.py`](file:///c:/Users/Huan%20Wang/workspace/howtofish-pycheat/src/howtofish_cheat/trainer.py) | Process lifecycle, hotkeys, upfront JIT compilation, and teardown. |
| [`run_trainer.py`](file:///c:/Users/Huan%20Wang/workspace/howtofish-pycheat/run_trainer.py) | Main entry runner. |


