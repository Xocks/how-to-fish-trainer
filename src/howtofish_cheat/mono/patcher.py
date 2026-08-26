"""Memory patcher for hot-patching JIT code and memory in target process."""

import ctypes
from typing import Dict, Optional
import pymem

kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

VirtualProtectEx = kernel32.VirtualProtectEx
VirtualProtectEx.restype = ctypes.c_bool
VirtualProtectEx.argtypes = [
    ctypes.c_void_p,
    ctypes.c_uint64,
    ctypes.c_size_t,
    ctypes.c_uint32,
    ctypes.POINTER(ctypes.c_uint32),
]

FlushInstructionCache = kernel32.FlushInstructionCache
FlushInstructionCache.restype = ctypes.c_bool
FlushInstructionCache.argtypes = [
    ctypes.c_void_p,
    ctypes.c_void_p,
    ctypes.c_size_t,
]

PAGE_EXECUTE_READWRITE = 0x40


class MemoryPatch:
    """Represents an active or standby memory patch."""

    def __init__(self, pm: pymem.Pymem, address: int, patch_bytes: bytes, original_bytes: bytes = None, name: str = ""):
        self.pm = pm
        self.address = address
        self.patch_bytes = patch_bytes
        if original_bytes is not None:
            self.original_bytes = original_bytes
        else:
            self.original_bytes = self.pm.read_bytes(address, len(patch_bytes))
        self.name = name
        self.is_applied = False

    def apply(self) -> bool:
        """Applies the patch bytes to target memory."""
        if self.is_applied or not self.patch_bytes:
            return True

        old_protect = ctypes.c_uint32(0)
        size = len(self.patch_bytes)

        VirtualProtectEx(self.pm.process_handle, self.address, size, PAGE_EXECUTE_READWRITE, ctypes.byref(old_protect))
        self.pm.write_bytes(self.address, self.patch_bytes, size)
        FlushInstructionCache(self.pm.process_handle, self.address, size)
        VirtualProtectEx(self.pm.process_handle, self.address, size, old_protect.value, ctypes.byref(old_protect))

        self.is_applied = True
        return True

    def restore(self) -> bool:
        """Restores original bytes."""
        if not self.is_applied or not self.original_bytes:
            return True

        old_protect = ctypes.c_uint32(0)
        size = len(self.original_bytes)

        VirtualProtectEx(self.pm.process_handle, self.address, size, PAGE_EXECUTE_READWRITE, ctypes.byref(old_protect))
        self.pm.write_bytes(self.address, self.original_bytes, size)
        FlushInstructionCache(self.pm.process_handle, self.address, size)
        VirtualProtectEx(self.pm.process_handle, self.address, size, old_protect.value, ctypes.byref(old_protect))

        self.is_applied = False
        return True


class MethodPatcher:
    """Manages method-level JIT code patches."""

    def __init__(self, pm: pymem.Pymem):
        self.pm = pm
        self.patches: Dict[str, MemoryPatch] = {}

    def register_method(self, patch_id: str, address: int) -> None:
        """Caches original bytes of a method before any patching occurs."""
        if patch_id not in self.patches:
            orig = self.pm.read_bytes(address, 1)
            if orig == b"\xC3":
                return
            self.patches[patch_id] = MemoryPatch(self.pm, address, b"\xC3", original_bytes=orig, name=patch_id)

    def register_custom(self, patch_id: str, address: int, patch_bytes: bytes, min_backup_len: int = 32) -> None:
        """Caches original bytes for a custom byte patch with safe backup length."""
        if patch_id not in self.patches:
            backup_len = max(len(patch_bytes), min_backup_len)
            orig = self.pm.read_bytes(address, backup_len)
            self.patches[patch_id] = MemoryPatch(self.pm, address, patch_bytes, original_bytes=orig, name=patch_id)

    def patch_ret(self, patch_id: str, address: int) -> MemoryPatch:
        """Patches function start with RET (0xC3) to immediately return."""
        if patch_id in self.patches:
            patch = self.patches[patch_id]
            patch.patch_bytes = b"\xC3"
        else:
            orig = self.pm.read_bytes(address, 1)
            patch = MemoryPatch(self.pm, address, b"\xC3", original_bytes=orig, name=patch_id)
            self.patches[patch_id] = patch
        patch.apply()
        return patch

    def patch_custom(self, patch_id: str, address: int, patch_bytes: bytes) -> MemoryPatch:
        """Patches function with arbitrary machine code bytes."""
        if patch_id in self.patches:
            patch = self.patches[patch_id]
            if not patch.is_applied and len(patch.original_bytes) < len(patch_bytes):
                patch.original_bytes = self.pm.read_bytes(address, max(len(patch_bytes), 32))
            patch.patch_bytes = patch_bytes
        else:
            orig = self.pm.read_bytes(address, max(len(patch_bytes), 32))
            patch = MemoryPatch(self.pm, address, patch_bytes, original_bytes=orig, name=patch_id)
            self.patches[patch_id] = patch
        patch.apply()
        return patch

    def restore(self, patch_id: str) -> bool:
        """Restores patched method."""
        if patch_id in self.patches:
            return self.patches[patch_id].restore()
        return False

    def is_applied(self, patch_id: str) -> bool:
        """Returns whether a patch is currently active."""
        if patch_id in self.patches:
            return self.patches[patch_id].is_applied
        return False

    def restore_all(self) -> None:
        """Restores all registered patches."""
        for patch in list(self.patches.values()):
            try:
                patch.restore()
            except Exception:
                pass
