---
name: unity-mono-trainer
description: Comprehensive guide and reference for developing external and internal memory trainers, JIT hook engines, and runtime injectors for Unity Mono games (x86/x64). Covers Mono Embedding C APIs, TLS thread attachment, loaded assembly resolution, JIT method compilation, prologue/trampoline patching, static vtables, and FishNet/Netcode client-prediction handling.
---

# Unity Mono Game Trainer Development Guide

A reference manual and reusable pattern collection for reverse engineering and developing memory trainers for Unity Mono games on Windows.

---

## 1. Unity Mono Engine Architecture

Unity Mono games compile gameplay code to IL (Intermediate Language) assemblies hosted inside an embedded Mono runtime DLL:
- **Mono Runtime DLL**: `MonoBleedingEdge/EmbedRuntime/mono-2.0-bdwgc.dll` (modern) or `Mono/EmbedRuntime/mono.dll` (legacy).
- **Game Assemblies**: `<GameName>_Data/Managed/Assembly-CSharp.dll`, `UnityEngine.CoreModule.dll`, `FishNet.Runtime.dll`, etc.

### Static Analysis Quick-Start
To inspect assemblies without external GUI tools, use Python with `pythonnet` (`clr`):
```python
import clr, sys, os
import System.Reflection

managed_dir = r"path/to/Game_Data/Managed"
sys.path.append(managed_dir)
for f in os.listdir(managed_dir):
    if f.endswith('.dll'):
        try: System.Reflection.Assembly.LoadFrom(os.path.join(managed_dir, f))
        except: pass

asm = System.Reflection.Assembly.LoadFrom(os.path.join(managed_dir, 'Assembly-CSharp.dll'))
t = asm.GetType("PlayerVitals")
for m in t.GetMethods():
    params = [f"{p.ParameterType.Name} {p.Name}" for p in m.GetParameters()]
    print(f"{m.Name}({', '.join(params)})")
```

---

## 2. Low-Level Mono C API Exports

The Mono runtime exports C functions that can be invoked remotely inside the target process using `CreateRemoteThread` or shellcode stubs:

| Function Export | Signature | Purpose |
| :--- | :--- | :--- |
| `mono_get_root_domain` | `MonoDomain* mono_get_root_domain()` | Returns the primary Mono root domain pointer. |
| `mono_thread_attach` | `MonoThread* mono_thread_attach(MonoDomain*)` | Attaches calling OS thread to Mono & initializes TLS. |
| `mono_image_loaded` | `MonoImage* mono_image_loaded(const char* name)` | Locates loaded assembly image (e.g. `"Assembly-CSharp"`). |
| `mono_class_from_name` | `MonoClass* mono_class_from_name(MonoImage*, const char* ns, const char* name)` | Gets `MonoClass*` by namespace and name. |
| `mono_class_get_method_from_name` | `MonoMethod* mono_class_get_method_from_name(MonoClass*, const char* name, int param_count)` | Resolves method pointer by name and exact parameter count. |
| `mono_compile_method` | `void* mono_compile_method(MonoMethod*)` | Forces JIT compilation to native x64 machine code; returns code address. |
| `mono_class_vtable` | `MonoVTable* mono_class_vtable(MonoDomain*, MonoClass*)` | Resolves class VTable for static fields. |
| `mono_vtable_get_static_field_data`| `void* mono_vtable_get_static_field_data(MonoVTable*)` | Returns pointer to the static data buffer for a class. |
| `mono_class_get_field_from_name` | `MonoClassField* mono_class_get_field_from_name(MonoClass*, const char* name)` | Gets field definition. |
| `mono_field_get_offset` | `uint32_t mono_field_get_offset(MonoClassField*)` | Returns the byte offset of a field within instances or static buffer. |

---

## 3. Critical Gotchas & Best Practices

### Gotcha 1: The Mono TLS (Thread-Local Storage) Trap
> [!CAUTION]
> **Never invoke Mono C APIs in a new remote thread without attaching to Mono first.**
> Win32 `CreateRemoteThread` allocates an OS thread whose Mono TLS pointer is `NULL`. If Mono APIs (like `mono_class_from_name`) check GC state or domain on an unattached thread, the game will crash immediately with `0xC0000005` (Access Violation).

**Solution**: Every remote call stub must execute `mono_thread_attach(mono_get_root_domain())` before calling any target Mono function:
```asm
sub rsp, 0x28                       ; Shadow space
mov rcx, <root_domain>
mov rax, <mono_thread_attach>
call rax
; Now safe to invoke target Mono API
add rsp, 0x28
ret
```

### Gotcha 2: Image Lookup (`mono_image_loaded` vs `mono_domain_assembly_open`)
> [!IMPORTANT]
> `mono_domain_assembly_open` searches disk paths for *unloaded* assemblies. For assemblies already loaded by Unity (like `Assembly-CSharp`), it will fail or return `NULL`.
> **Always use `mono_image_loaded("Assembly-CSharp")`.**

### Gotcha 3: Method Parameter Counts
`mono_class_get_method_from_name` matches on exact parameter count:
- Parameterless method: `param_count = 0`
- Unity New Input System event handlers: `JumpInput(CallbackContext context)` -> `param_count = 1`
- `TakeDamage(int, Vector3, Vector3, bool)` -> `param_count = 4`

---

## 4. JIT Patching Patterns

### Pattern A: Prologue `RET` Patch (`0xC3`)
Used to completely disable damage, depletion, or hazard functions that return `void`:
- **Original Prologue**: `48 89 5C 24 08 ...` (e.g. `sub rsp, 0x38`)
- **Patched Prologue**: `C3` (`RET`)
- **Effect**: Function returns immediately with zero execution and zero performance overhead.

### Pattern B: Direct JIT Trampoline Patch
Used to bypass condition checks and immediately invoke an inner action (e.g. calling `Jump()` inside `JumpInput()` to enable Infinite Air Jump):
```asm
sub rsp, 0x28                       ; 48 83 EC 28
mov rax, <target_function_addr>     ; 48 B8 [8-byte address]
call rax                            ; FF D0
add rsp, 0x28                       ; 48 83 C4 28
ret                                 ; C3
```
- **Bytecode**: `\x48\x83\xEC\x28\x48\xB8` + `struct.pack('<Q', target_addr)` + `\xFF\xD0\x48\x83\xC4\x28\xC3` (21 bytes).

### Pattern C: Boolean Getter Return-True Stub
Used to force boolean properties (`Grounded`, `CanJump`, `IsAdmin`) to always return `true`:
- **Bytecode**: `\xB8\x01\x00\x00\x00\xC3` (`mov eax, 1; ret`)

---

## 5. Multiplayer & Networking Architecture (FishNet / Netcode)

Unity multiplayer games handle player state across two layers:
1. **Local Prediction State (`_localHp`, `_localIsDead`)**:
   - Decremented locally on incoming hits (`LocalHit`) to give zero latency feedback.
   - Sends RPC to server (`Server.HitPlayer`).
2. **Authoritative Networked State (`SyncVar<int> _syncedHealth`)**:
   - Updated on server via `TakeDamage`.
   - Fires `OnHealthChange` when synced back to clients, updating HUD `HealthPercent`.

### Complete Multi-Hook Defense Strategy
When implementing God Mode / Lock Health:
1. JIT patch `TakeDamage` with `RET` (stops server sync damage).
2. JIT patch `LocalHit` with `RET` (stops local prediction decrement and outbound RPC).
3. JIT patch `ApplyNewFire` / `ApplyNewPoison` with `RET` (stops elemental status gauges from filling).
4. Actively maintain `_localHp = 100`, `_prevHealth = 100`, `_invulnerableUntil = 999999.0`, `_prevFire = 0`, `_prevPoison = 0` in memory.
5. On teardown, restore all bytes, and reset `_invulnerableUntil = 0.0` in memory.

---

## 6. Reusable Implementation Skeleton

```python
import pymem
from typing import Dict, Optional

class UnityMonoTrainer:
    def __init__(self, process_name: str):
        self.pm = pymem.Pymem(process_name)
        self.mono_base = pymem.process.module_from_name(self.pm.process_handle, "mono-2.0-bdwgc.dll").lpBaseOfDll
        self.root_domain = self._resolve_domain()

    def get_export(self, name: str) -> int:
        # Resolve export address from mono-2.0-bdwgc.dll
        ...

    def find_class(self, assembly_name: str, class_name: str, namespace: str = "") -> int:
        # Use mono_image_loaded -> mono_class_from_name
        ...

    def compile_method(self, class_ptr: int, method_name: str, param_count: int) -> int:
        # Use mono_class_get_method_from_name -> mono_compile_method
        ...

    def patch_ret(self, address: int) -> bytes:
        # Backup byte, VirtualProtectEx -> 0xC3
        ...
```
