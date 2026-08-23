# How to Fish - Memory Trainer

An external Python-based trainer and cheat engine for the Unity Mono game **[How to Fish](https://store.steampowered.com/)**.

Powered by `pymem`, JIT function hooking via Mono runtime interop, and an interactive `rich` TUI dashboard.

---

## Features

| Hotkey | Feature | Description |
| :--- | :--- | :--- |
| **F1** | **Lock Health** | Blocks all incoming damage (NPC hits, punches, hazards, fire, poison, starvation) & dissipates elemental gauges. **Normal jump physics preserved.** |
| **F2** | **Lock Hunger** | Prevents fullness meter from dropping over time or during actions. |
| **F3** | **Infinite Air Jump** | Pure movement patch: allows infinite mid-air jumps / air flight (**InGodMode is NOT used; health unaffected**). |
| **F4** | **Unlimited Ammo** | Infinite ammunition for all firearms without magazine depletion or forced reloads. |
| **F5** | **Damage Multiplier** | Cycles damage multiplier for firearms, melee weapons, and fists: **`1x` $\rightarrow$ `2x` $\rightarrow$ `5x` $\rightarrow$ `10x` $\rightarrow$ `One-Shot Kill (99999)`**. |
| **F10** | **Safe Exit** | Restores all modified code/memory and exits the trainer safely. |

---

## Architecture & How It Works

1. **Mono Runtime Interop (`howtofish_cheat.mono.bridge`)**:
   - Resolves `mono-2.0-bdwgc.dll` exports inside `How to Fish.exe`.
   - Attaches remote threads to the Mono root domain with TLS setup.
   - Dynamically locates loaded assemblies (`Assembly-CSharp`), classes, methods, and static vtables.
2. **JIT Compilation & Prologue Patching (`howtofish_cheat.mono.patcher`)**:
   - **Lock Health (`F1`)**: JIT-patches `PlayerVitals.TakeDamage`, `PlayerVitals.LocalHit`, `PlayerVitals.DamageFromFullness`, `PlayerVitals.ApplyNewFire`, and `PlayerVitals.ApplyNewPoison`.
   - **Lock Hunger (`F2`)**: JIT-patches `PlayerVitals.LowerFullness` and `PlayerVitals.LowerFullnessTick`.
   - **Infinite Air Jump (`F3`)**: Installs a direct call trampoline on `PlayerMovement.JumpInput` pointing straight to `PlayerMovement.Jump`, enabling unlimited air jumps without touching health or God Mode.
   - **Unlimited Ammo (`F4`)**: JIT-patches `Weapon.set_Ammo` with `RET` (`0xC3`) and actively locks magazine capacity to `999` while resetting reload flags.
   - **Damage Multiplier (`F5`)**: Pure real-time in-memory scaling across `PlayerPunching._damage`, `Melee._sharpnessUpgrades` array, `Attachments._bulletUpgrades` array, and `WeaponInfo.ProjectileDamage` (1x, 2x, 5x, 10x, One-Shot Kill).
   - Disabling any cheat or exiting cleanly restores original machine code bytes and base damage values.
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

# Run unit tests with uv
uv run pytest -v
```

### 2. In-Game Controls
- Press **F1** to toggle **Lock Health**.
- Press **F2** to toggle **Lock Hunger**.
- Press **F3** to toggle **Infinite Air Jump**.
- Press **F4** to toggle **Unlimited Ammo**.
- Press **F5** to cycle **Damage Multiplier** (`1x` $\rightarrow$ `2x` $\rightarrow$ `5x` $\rightarrow$ `10x` $\rightarrow$ `One-Shot`).
- Press **F10** or **Ctrl+C** to cleanly exit the trainer.

---

## Technical Documentation

For an in-depth breakdown of the reverse engineering, FishNet network architecture, Mono runtime TLS internals, JIT trampolines, and gotchas, see:

📖 **[Technical Deep Dive & Architecture Documentation](docs/TECHNICAL_DEEP_DIVE.md)**
