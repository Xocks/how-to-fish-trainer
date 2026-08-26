"""Remote execution engine for x64 Windows processes with automatic Mono thread attachment."""

import ctypes
import struct
from typing import Any, List, Optional
import pymem
import pymem.process

kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

VirtualAllocEx = kernel32.VirtualAllocEx
VirtualAllocEx.restype = ctypes.c_uint64
VirtualAllocEx.argtypes = [
    ctypes.c_void_p,
    ctypes.c_uint64,
    ctypes.c_size_t,
    ctypes.c_uint32,
    ctypes.c_uint32,
]

VirtualFreeEx = kernel32.VirtualFreeEx
VirtualFreeEx.restype = ctypes.c_bool
VirtualFreeEx.argtypes = [
    ctypes.c_void_p,
    ctypes.c_uint64,
    ctypes.c_size_t,
    ctypes.c_uint32,
]

CreateRemoteThread = kernel32.CreateRemoteThread
CreateRemoteThread.restype = ctypes.c_void_p
CreateRemoteThread.argtypes = [
    ctypes.c_void_p,
    ctypes.c_void_p,
    ctypes.c_size_t,
    ctypes.c_uint64,
    ctypes.c_void_p,
    ctypes.c_uint32,
    ctypes.c_void_p,
]

WaitForSingleObject = kernel32.WaitForSingleObject
WaitForSingleObject.restype = ctypes.c_uint32
WaitForSingleObject.argtypes = [ctypes.c_void_p, ctypes.c_uint32]

CloseHandle = kernel32.CloseHandle
CloseHandle.restype = ctypes.c_bool
CloseHandle.argtypes = [ctypes.c_void_p]

MEM_COMMIT = 0x1000
MEM_RESERVE = 0x2000
MEM_RELEASE = 0x8000
PAGE_EXECUTE_READWRITE = 0x40


class RemoteExecutor:
    """Provides safe x64 remote function execution with automatic Mono TLS initialization."""

    def __init__(self, pm: pymem.Pymem, scratch_size: int = 0x10000):
        self.pm = pm
        self.handle = pm.process_handle
        self.scratch_size = scratch_size
        self.scratch_base: Optional[int] = None
        self.root_domain: Optional[int] = None
        self.mono_thread_attach_fn: Optional[int] = None
        self._allocate_scratch()

    def _allocate_scratch(self) -> None:
        """Allocates a dedicated RWX memory pool in the target process."""
        self.scratch_base = VirtualAllocEx(
            self.handle, 0, self.scratch_size, MEM_COMMIT | MEM_RESERVE, PAGE_EXECUTE_READWRITE
        )
        if not self.scratch_base:
            raise RuntimeError(f"Failed to allocate remote scratch memory: {ctypes.get_last_error()}")

    def set_mono_attach(self, root_domain: int, mono_thread_attach_fn: int) -> None:
        """Configures automatic Mono thread attachment for all subsequent remote calls."""
        self.root_domain = root_domain
        self.mono_thread_attach_fn = mono_thread_attach_fn

    def close(self) -> None:
        """Frees the remote scratch pool."""
        if self.scratch_base:
            try:
                VirtualFreeEx(self.handle, self.scratch_base, 0, MEM_RELEASE)
            except Exception:
                pass
            self.scratch_base = None

    def write_string(self, offset_in_scratch: int, text: str) -> int:
        """Writes a null-terminated UTF-8 string to the scratch buffer."""
        if not self.scratch_base:
            raise RuntimeError("Scratch buffer is not allocated.")
        if offset_in_scratch < 0:
            raise ValueError("Scratch offset cannot be negative.")
        encoded = text.encode("utf-8") + b"\x00"
        if offset_in_scratch + len(encoded) > self.scratch_size:
            raise ValueError(
                f"String does not fit in remote scratch buffer: "
                f"offset=0x{offset_in_scratch:X}, size={len(encoded)}"
            )
        target_addr = self.scratch_base + offset_in_scratch
        self.pm.write_bytes(target_addr, encoded, len(encoded))
        return target_addr

    def call(self, func_addr: int, *args: int, timeout_ms: int = 4000) -> int:
        """Executes a 64-bit function in the remote process with up to 4 arguments."""
        if not self.scratch_base:
            raise RuntimeError("Scratch buffer is not allocated.")

        code_offset = 0x0
        result_offset = 0x500
        result_addr = self.scratch_base + result_offset

        arg_vals = [int(a) if a is not None else 0 for a in args]
        while len(arg_vals) < 4:
            arg_vals.append(0)

        # Clear result address
        self.pm.write_ulonglong(result_addr, 0)

        stub = bytearray()
        # sub rsp, 0x28 (align stack to 16 bytes and reserve shadow space)
        stub.extend(b"\x48\x83\xEC\x28")

        # If Mono attach is configured, attach this thread first:
        # rcx = root_domain; rax = mono_thread_attach; call rax;
        if self.root_domain and self.mono_thread_attach_fn and func_addr != self.mono_thread_attach_fn:
            stub.extend(b"\x48\xB9" + struct.pack("<Q", self.root_domain))
            stub.extend(b"\x48\xB8" + struct.pack("<Q", self.mono_thread_attach_fn))
            stub.extend(b"\xFF\xD0")

        # Load arguments into RCX, RDX, R8, R9
        stub.extend(b"\x48\xB9" + struct.pack("<Q", arg_vals[0]))
        stub.extend(b"\x48\xBA" + struct.pack("<Q", arg_vals[1]))
        stub.extend(b"\x49\xB8" + struct.pack("<Q", arg_vals[2]))
        stub.extend(b"\x49\xB9" + struct.pack("<Q", arg_vals[3]))

        # Call target function
        stub.extend(b"\x48\xB8" + struct.pack("<Q", func_addr))
        stub.extend(b"\xFF\xD0")

        # Save return value
        stub.extend(b"\x48\xB9" + struct.pack("<Q", result_addr))
        stub.extend(b"\x48\x89\x01")

        # add rsp, 0x28; ret
        stub.extend(b"\x48\x83\xC4\x28\xC3")

        stub_addr = self.scratch_base + code_offset
        self.pm.write_bytes(stub_addr, bytes(stub), len(stub))

        # Create remote thread
        thread_handle = CreateRemoteThread(
            self.handle, None, 0, stub_addr, None, 0, None
        )
        if not thread_handle:
            raise RuntimeError(f"CreateRemoteThread failed: {ctypes.get_last_error()}")

        wait_res = WaitForSingleObject(thread_handle, timeout_ms)
        CloseHandle(thread_handle)

        if wait_res != 0:
            raise TimeoutError(f"Remote call to 0x{func_addr:X} timed out (wait result: {wait_res})")

        return self.pm.read_ulonglong(result_addr)
