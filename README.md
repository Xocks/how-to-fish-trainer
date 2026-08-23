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
   - Disabling any cheat or exiting cleanly restores the original machine code bytes.
3. **Interactive Console UI (`howtofish_cheat.ui.console`)**:
   - Live status display with connection status, active PID, Mono domain pointer, and real-time cheat states.

---

## Usage

### 1. Launch the Trainer
You can launch the trainer either **before** or **after** starting the game:

```powershell
# Using the quick-launch script
.venv\Scripts\python run_trainer.py

# Or as a module
.venv\Scripts\python -m howtofish_cheat
```

### 2. In-Game Controls
- Press **F1** to toggle **Lock Health**.
- Press **F2** to toggle **Lock Hunger**.
- Press **F3** to toggle **Infinite Air Jump**.
- Press **F10** or **Ctrl+C** to cleanly exit the trainer.

---

## Technical Documentation

For an in-depth breakdown of the reverse engineering, FishNet network architecture, Mono runtime TLS internals, JIT trampolines, and gotchas, see:

📖 **[Technical Deep Dive & Architecture Documentation](docs/TECHNICAL_DEEP_DIVE.md)**
