---
name: game-trainer-dev
description: General framework and methodologies for developing robust, external game trainers on Windows. Covers reverse engineering workflows, process attachment, memory protection management (VirtualProtectEx), non-polling event loops, hotkey hooks, terminal dashboards with Rich, multiplayer authority models, and guaranteed clean teardown on exit.
---

# Game Trainer Development Framework & Best Practices

A universal framework and design guide for developing external memory trainers, cheat engines, and game modification tools on Windows.

---

## 1. Game Trainer Development Lifecycle

```
+-------------------------------------------------------------------------+
|                           DEVELOPMENT PHASES                            |
|                                                                         |
|  1. REVERSE ENGINEERING                                                 |
|     - Identify engine (Unity Mono, IL2CPP, Unreal Engine, Native C++)   |
|     - Disassemble binaries / reflection dump                            |
|     - Locate key structures (Vitals, Inventory, Movement, Physics)     |
|                               |                                         |
|                               v                                         |
|  2. STRATEGY SELECTION                                                  |
|     - JIT / Bytecode Prologue Patch (Zero runtime overhead)             |
|     - Mid-Function Code Cave / Trampoline Hook                          |
|     - Pointer Traversal & Real-Time Memory Freeze                       |
|                               |                                         |
|                               v                                         |
|  3. TRAINER IMPLEMENTATION                                              |
|     - Process attachment & handle management                            |
|     - Non-blocking hotkey listeners (keyboard hooks)                    |
|     - Live terminal dashboard (Rich TUI)                                |
|                               |                                         |
|                               v                                         |
|  4. ROBUST TEARDOWN & REVERSION                                         |
|     - Catch OS signals (SIGINT, SIGTERM, atexit)                        |
|     - Restore all original byte arrays atomically                       |
|     - Reset altered memory flags and timers back to normal              |
+-------------------------------------------------------------------------+
```

---

## 2. Memory Protection & Safe Patching Mechanics

When patching code or static data in external processes on Windows, memory pages are often marked `PAGE_EXECUTE_READ` or `PAGE_READONLY`.

### The Atomic Patching Pattern
```python
import ctypes
import pymem

kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
VirtualProtectEx = kernel32.VirtualProtectEx
PAGE_EXECUTE_READWRITE = 0x40

class MemoryPatch:
    def __init__(self, pm: pymem.Pymem, address: int, patch_bytes: bytes):
        self.pm = pm
        self.address = address
        self.patch_bytes = patch_bytes
        # Always capture original bytes before modifying anything!
        self.original_bytes = self.pm.read_bytes(address, len(patch_bytes))
        self.is_applied = False

    def apply(self) -> bool:
        if self.is_applied: return True
        old_protect = ctypes.c_uint32(0)
        size = len(self.patch_bytes)
        
        # 1. Elevate page permission to Read/Write/Execute
        VirtualProtectEx(self.pm.process_handle, self.address, size, PAGE_EXECUTE_READWRITE, ctypes.byref(old_protect))
        # 2. Write patch bytes
        self.pm.write_bytes(self.address, self.patch_bytes, size)
        # 3. Restore original page protection
        VirtualProtectEx(self.pm.process_handle, self.address, size, old_protect.value, ctypes.byref(old_protect))
        
        self.is_applied = True
        return True

    def restore(self) -> bool:
        if not self.is_applied: return True
        old_protect = ctypes.c_uint32(0)
        size = len(self.original_bytes)
        
        VirtualProtectEx(self.pm.process_handle, self.address, size, PAGE_EXECUTE_READWRITE, ctypes.byref(old_protect))
        self.pm.write_bytes(self.address, self.original_bytes, size)
        VirtualProtectEx(self.pm.process_handle, self.address, size, old_protect.value, ctypes.byref(old_protect))
        
        self.is_applied = False
        return True
```

---

## 3. UI Dashboard & Live Refresh with Rich

A clean, responsive terminal dashboard provides clear feedback without spamming terminal output:

```python
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.live import Live
import time

console = Console()
# Use Live display with refresh_per_second=4 for smooth rendering
with Live(console=console, refresh_per_second=4, screen=False) as live:
    while is_running:
        table = Table(box=box.ROUNDED, expand=True)
        table.add_column("Hotkey", justify="center", style="bold cyan")
        table.add_column("Feature", style="bold white")
        table.add_column("Status", justify="center")
        table.add_column("Description", style="dim")
        
        for cheat in cheats:
            status = "[bold green]ACTIVE[/bold green]" if cheat.is_enabled else "[dim]OFF[/dim]"
            table.add_row(cheat.hotkey, cheat.name, status, cheat.description)
            
        live.update(Panel(table, title="GAME TRAINER"))
        time.sleep(0.25)
```

---

## 4. Guaranteed Teardown & Reversion (Preventing "Dirty Exits")

> [!WARNING]
> If a trainer exits without restoring memory patches, the game will remain modified. Furthermore, if the trainer altered internal timers (e.g. `_invulnerableUntil = 999999.0`), the player will remain permanently invulnerable even after the trainer is closed.

### Implementation Checklist for Clean Exits:
1. **Signal Handlers**: Bind `signal.signal(signal.SIGINT, handler)` and `signal.signal(signal.SIGTERM, handler)`.
2. **`atexit` Registration**: Register `atexit.register(self.cleanup)`.
3. **`try ... finally` Structure**: Always enclose the main `run()` loop in `try ... finally: self.cleanup()`.
4. **Memory Reversion**:
   - Restore all original bytecode buffers in target functions.
   - Reset altered memory values back to normal (e.g. `_invulnerableUntil = 0.0`, `InGodMode = 0`).
   - Remove keyboard hooks (`keyboard.remove_hotkey`).
   - Close process handles (`CloseHandle`).

---

## 5. Multiplayer & Network Authority Considerations

When building trainers for multiplayer games:

| Concept | Client-Side Behavior | Server-Side Behavior | Trainer Strategy |
| :--- | :--- | :--- | :--- |
| **Client-Authoritative Movement** | Local physics & velocity dictate position. | Accepts client position updates. | Hook jump/speed functions directly; works 100% on remote servers. |
| **Client-Initiated Hit Detection** | Local client detects collision and sends RPC. | Server applies damage based on incoming RPC. | Hook `LocalHit` with `RET` to prevent outbound RPCs; stops damage on remote servers. |
| **Server-Authoritative Damage** | Client displays synced health from server. | Server calculates damage and syncs value. | Hooking local `TakeDamage` protects host/solo; remote servers require preventing hit reports or leveraging fullness regen loops. |

---

## 6. Checklist Before Releasing a Trainer

- [ ] Does the trainer auto-detect and attach to the game regardless of launch order?
- [ ] Are all original bytes backed up before applying patches?
- [ ] Are hotkeys non-blocking and easily toggleable?
- [ ] Does pressing exit (`F10`, `Ctrl+C`, window close) cleanly restore all modified code and memory?
- [ ] Are secondary visual effects (elemental gauges, screen overlays) properly handled alongside raw health values?
- [ ] Are movement mechanics decoupled from godmode flags to preserve normal physics?
