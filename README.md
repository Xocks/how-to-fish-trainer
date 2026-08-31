# How to Fish (渔力全开) - Xocks External Trainer Edition

[English](README.md) | [简体中文](README_zh.md)

An external trainer for the Unity Mono game **[How to Fish (渔力全开)](https://store.steampowered.com/)**. It installs no mod and replaces no game file, while providing a runtime item catalog, native-presentation third person, aim assistance, silent-aim experiments, item/creature ESP, and reversible diagnostics.

> [!IMPORTANT]
> This is a **community fork maintained by Xocks**, developed from commit
> `688a9c9` of
> **[fredwangwang/how-to-fish-trainer](https://github.com/fredwangwang/how-to-fish-trainer)**.
> It is not an official update published by the original author. The upstream
> copyright notice and MIT license are preserved.

- **Modified repository:** [Xocks/how-to-fish-trainer](https://github.com/Xocks/how-to-fish-trainer)
- **Current branch:** [`main`](https://github.com/Xocks/how-to-fish-trainer/tree/main)
- **Current release:** `0.3.0`

Powered by `pymem`, JIT function hooking via Mono runtime interop, and an interactive `rich` TUI dashboard.

> **v0.3.0:** Core code, compatibility gates, reversible cleanup, runtime catalog, aim/ESP, and the native third-person presentation chain have automated coverage and final DLL/EXE builds. Silent ballistics, network poses, player targeting, and joined-client capabilities remain private-room experiments whose server acceptance requires two-client testing.

---

## What This Fork Adds

Compared with the upstream baseline, this branch adds:

| Modification | Description |
| :--- | :--- |
| **F7 runtime item catalog** | Shows the game's `GameInfo.GetSpawnable(byte)` IDs first, then merges named/skin, resource Item, and engine entries under synthetic selection IDs above 1000. The catalog is rebuilt after reconnecting. |
| **F8 native item spawning** | Calls `DazedCommands.UseSpawnCommand` to spawn the selected item about two metres in front of the camera. It is restricted to single-player or the host and has a 500ms cooldown. |
| **Special-item safeguards** | Quest and unknown items receive a red `!` marker and require a second confirmation. |
| **Character hard block** | ID 53, `deadplayer`, and prefabs carrying `DeadPlayer` are marked with `×` and cannot reach the native spawn call. |
| **Compatibility gate** | Verifies the assembly hash, Mono method/field contracts, and native JIT entries; unknown builds run in diagnostics-only mode. |
| **F9 360° head aim** | ADS plus right mouse selects the nearest enabled target by world distance. Fish and birds are enabled by default; other creatures are optional, while players are off by default and require per-session private-room consent. |
| **Home third person** | Keeps the verified `CurCam` shoulder camera, rebuilds the owner-hidden render hierarchy from a loaded player prefab, and temporarily rebinds the retained native `PlayerLegs`, `PlayerHands`, `PlayerBody`, and `IK` presentation chain to it. v0.3.0 uses real local movement, held item, camera, breathing, ground and boat state; it contains no hand-written gait and restores every rebound reference on exit. It copies no player/network/collision/rigidbody behavior. Local rendering is not proof of another client's rendering or hitbox changes. |
| **End silent aim (experimental)** | Pre-locks without right mouse and leaves the camera under player control. Each new local projectile receives one initial correction; tracking mode then steers with a rate limit and stops at obstruction. Network acceptance remains unverified. |
| **Private-room pose experiment** | Offers mutually exclusive low/backwards and high-speed body-spin modes. Pitch/yaw are substituted only during the game's existing pose send window, then the local view is restored. Remote animation and hitbox behavior are not yet verified and are not advertised as anti-headshot. |
| **F11 item/creature labels** | Projects labels at up to 60 Hz, staggers occlusion checks, and exposes a 10-36 font-size slider. |
| **Insert mouse panel** | Adds a Spawn tab and captures look/fire actions while the mouse is interacting with the panel. |
| **Layered spawn catalog** | Separates official pickups, hidden `Item` prefabs, safe static visual previews, and diagnostic-only Unity resources. Engine resources are no longer all described as spawnable items. |
| **Single F8 dispatch** | F8 triggers on key release and deduplicates requests for 400ms, preventing held keys from repeatedly creating objects or flooding diagnostics. |
| **Joined-client experiment** | Uses the game's existing `Server.BuyItem` RPC only for safe items/weapons after private-lobby consent, with one request at a time, a two-second cooldown, and fail-closed synchronization. |
| **Crash fixes** | Dispatches spawning on Unity's main thread, uses a two-way restoration handshake, and retains pinned Mono command strings for the current game process to avoid the identified cleanup-timing crashes. |
| **Responsive selector UI** | Uses four `ID / Item` pairs on wide terminals, automatically reduces columns on narrow windows, uses available height for larger pages, and redraws cleanly after resizing. |
| **Diagnostics and tests** | Adds sanitized support bundles, a one-shot `spawn_probe`, and automated coverage for catalog scanning, selector input, authority checks, cooldowns, reconnects, and main-thread restoration. |

This remains an external process-memory trainer. It does not replace game files and is not installed as a mod. Item spawning creates game objects, so test it with a disposable save in single-player or as the host.

---

## Features

| Hotkey | Feature | Description |
| :--- | :--- | :--- |
| **F1** | **Lock Health** | Full protection for solo/host. Joined clients block local damage reports and statuses but honestly show partial support when the server owns the damage result. |
| **F2** | **Lock Hunger** | Prevents fullness meter from dropping over time or during actions. |
| **F3** | **Infinite Air Jump** | Pure movement patch: allows infinite mid-air jumps / air flight (**InGodMode is NOT used; health unaffected**). |
| **F4** | **Unlimited Ammo** | Infinite ammunition for all firearms without magazine depletion or forced reloads. |
| **F5** | **Damage Multiplier** | Cycles damage multiplier for firearms, melee weapons, and fists: **`1x` $\rightarrow$ `2x` $\rightarrow$ `5x` $\rightarrow$ `10x` $\rightarrow$ `One-Shot Kill (99999)`**. |
| **F6** | **Add Money (+1w)** | Adds **+$10,000 (1w)** money with sound effect, UI animation, and multiplayer synchronization on keypress. |
| **F7** | **Select Spawn Item** | Official entries keep their native IDs; named/resource/engine entries use synthetic IDs above 1000. A red `!` marks confirmation-required items and `×` marks hard blocks. |
| **F8** | **Spawn Selected Item** | Solo/host spawns in front; a consented private-lobby client may request one safe item directly into its hand. |
| **F9** | **360° Head Aim** | Locks the nearest enabled fish/bird/creature; the optional player category is shared with End and requires private-room consent. |
| **Home** | **Third Person** | Toggles the collision-shortened shoulder camera and render-only local avatar mirror; detailed state is shown in Insert Diagnostics. |
| **End** | **Silent Aim (Experimental)** | Keeps the view free while correcting the original firing path; joined clients require private-room consent. |
| **F11** | **Item / Creature ESP** | Toggles categorized 60 Hz name and distance labels. |
| **Insert** | **Mouse Panel** | Opens Combat, ESP, Spawn, Experiment, and Diagnostics without moving the game camera. |
| **F12** | **Switch Language** | Toggles trainer interface language between **Chinese (中文)** and **English (EN)**. |
| **F10** | **Safe Exit** | Restores all modified code/memory and exits the trainer safely. |

---

## Architecture & How It Works

1. **Mono Runtime Interop (`howtofish_cheat.mono.bridge`)**:
   - Resolves `mono-2.0-bdwgc.dll` exports inside `How to Fish.exe`.
   - Attaches remote threads to the Mono root domain with TLS setup.
   - Dynamically locates loaded assemblies (`Assembly-CSharp`), classes, methods, and static vtables.
2. **JIT Compilation & Memory Scaling (`howtofish_cheat.mono.patcher`)**:
   - **Lock Health (`F1`)**: JIT-patches `PlayerVitals.TakeDamage`, `PlayerVitals.LocalHit`, `PlayerVitals.DamageFromFullness`, `PlayerVitals.ApplyNewFire`, and `PlayerVitals.ApplyNewPoison`.
   - **Lock Hunger (`F2`)**: JIT-patches `PlayerVitals.LowerFullness` and `PlayerVitals.LowerFullnessTick`.
   - **Infinite Air Jump (`F3`)**: Installs a direct call trampoline on `PlayerMovement.JumpInput` pointing straight to `PlayerMovement.Jump`, enabling unlimited air jumps without touching health or God Mode.
   - **Unlimited Ammo (`F4`)**: JIT-patches `Weapon.set_Ammo` with `RET` (`0xC3`) and actively locks magazine capacity to `999` while resetting reload flags.
   - **Damage Multiplier (`F5`)**: Pure real-time in-memory scaling across `PlayerPunching._damage`, `Melee._sharpnessUpgrades` array, `Attachments._bulletUpgrades` array, and `WeaponInfo.ProjectileDamage` (1x, 2x, 5x, 10x, One-Shot Kill).
   - **Add Money (`F6`)**: Directly updates authoritative static `<Money>k__BackingField` and FishNet `SyncVar<int> _money`, invokes `PlayerUI.SetMoney` for floating `+$10000` text + HUD animated roll, and calls `MoneyManager.MoneySound` for audio feedback.
   - **Item Spawner (`F7` / `F8`)**: The managed main thread merges official IDs, the name registry, `Resources/Items`, and prefab-like engine objects. Hotkeys only queue requests; joined clients never spoof `IsServerInitialized`.
   - **Aim / ESP (`F9` / `F11`)**: The external controller loads a repository-built helper into the existing Mono domain. 360-degree selection, two-layer recoil handling, object enumeration, 60 Hz projection, and IMGUI drawing remain on Unity's main thread.
   - Disabling any cheat or exiting cleanly restores original machine code bytes and base values.
3. **Interactive Console UI (`howtofish_cheat.ui.console`)**:
   - Live status display with connection status, active PID, Mono domain pointer, and real-time cheat states.

---

## Usage

### 1. Launch the Trainer
You can launch the trainer either **before** or **after** starting the game:

```powershell
# Using the quick-launch script with uv
uv run python run_trainer.py

# Or as a module with uv
uv run python -m howtofish_cheat

# Build single standalone executable (dist/HowToFishTrainer.exe)
uv run python build.py

# Run unit tests with uv
uv run pytest -v
```

### 2. In-Game Controls
- Press **F1** to toggle **Lock Health**.
- Press **F2** to toggle **Lock Hunger**.
- Press **F3** to toggle **Infinite Air Jump**.
- Press **F4** to toggle **Unlimited Ammo**.
- Press **F5** to cycle **Damage Multiplier** (`1x` $\rightarrow$ `2x` $\rightarrow$ `5x` $\rightarrow$ `10x` $\rightarrow$ `One-Shot`).
- Press **F6** to **Add Money (+1w / +$10,000)** on press.
- Press **F7** to open the item catalog, enter an ID, and confirm the selection.
- Press **F8** to spawn one selected item in single-player or while hosting.
- Press **F9** to toggle head aim; hold right mouse while ADS.
- Press **Home** to toggle the third-person shoulder camera.
- Press **End** to toggle experimental silent aim; choose initial correction or projectile tracking in Insert.
- Press **F11** to toggle item / creature labels.
- Press **Insert** to open or close the mouse panel.
- Press **F12** to **Switch Language (中文 / EN)** at any time.
- Press **F10** or **Ctrl+C** to cleanly exit the trainer.

### 3. Item Spawner Validation and Diagnostics

Use a new disposable save for initial testing. Verify one fish and one firearm in single-player first, then test host synchronization with a second client. A visual-preview entry copies only static Mesh/Sprite data, cannot be picked up, and never synchronizes; diagnostic-only resources cannot be spawned.

Steam Build `24911270` exposes 85 entries in the game's native spawn dictionary (IDs `0–85`, with ID `30` empty). Use **PageUp / PageDown** to view every page; fish and weapons are classified separately.

After testing, create a sanitized support bundle inside `test-artifacts/`:

```powershell
uv run python -m howtofish_cheat.diagnostics collect
```

For a controlled one-shot integration check against a game that you have
already started and placed in a local session, run:

```powershell
uv run python -m howtofish_cheat.spawn_probe --item-id 56 --confirm-live-spawn
```

The probe does not launch the game. It performs exactly one spawn attempt,
checks that the process remains alive, restores the temporary patch, and writes
only the normal workspace-local diagnostic log.

The bundle contains the latest trainer JSONL log and repository metadata. It does not include saves, full Unity logs, chat, or credentials.

---

## Technical Documentation

For an in-depth breakdown of the reverse engineering, FishNet network architecture, Mono runtime TLS internals, JIT trampolines, and gotchas, see:

📖 **[Technical Deep Dive & Architecture Documentation](docs/TECHNICAL_DEEP_DIVE.md)**

---

## Credits and License

- **Upstream project:** [fredwangwang/how-to-fish-trainer](https://github.com/fredwangwang/how-to-fish-trainer)
- **Modified edition:** [Xocks/how-to-fish-trainer](https://github.com/Xocks/how-to-fish-trainer)
- The project remains under the repository's [MIT License](LICENSE). Keep the original copyright and license notice when redistributing source code or binaries.
- This project is not affiliated with or endorsed by the game developer, publisher, Steam, or Valve.
