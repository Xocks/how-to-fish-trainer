"""One-shot Unity main-thread dispatch with a restoration handshake."""

from __future__ import annotations

import struct
import threading
import time
from typing import Callable


MAIN_THREAD_PATCH_LOCK = threading.Lock()


class MainThreadDispatcher:
    """Calls one managed native entry from ``Player.LateUpdate`` exactly once."""

    TIMEOUT_SECONDS = 4.0
    PATCH_ID = "runtime.main_thread_dispatch"

    def __init__(
        self,
        pm: object,
        mono: object,
        patcher: object,
        late_update_native: int,
        clock: Callable[[], float] = time.monotonic,
        sleeper: Callable[[float], None] = time.sleep,
    ):
        self.pm = pm
        self.mono = mono
        self.patcher = patcher
        self.late_update_native = late_update_native
        self.clock = clock
        self.sleeper = sleeper

    @staticmethod
    def build_stub(state_addr: int, function_addr: int) -> bytes:
        stub = bytearray()
        stub.extend(b"\x48\xB8" + struct.pack("<Q", state_addr))
        stub.extend(b"\x80\x38\x01")
        stub.extend(b"\x75\x00")
        skip_index = len(stub) - 1
        stub.extend(b"\xC6\x00\x02")
        stub.extend(b"\x48\x83\xEC\x28")
        stub.extend(b"\x48\xB8" + struct.pack("<Q", function_addr))
        stub.extend(b"\xFF\xD0")
        stub.extend(b"\x48\x83\xC4\x28")
        stub.extend(b"\x48\xB8" + struct.pack("<Q", state_addr))
        stub.extend(b"\xC6\x00\x03")
        wait_index = len(stub)
        stub.extend(b"\xF3\x90")
        stub.extend(b"\x80\x38\x04")
        stub.extend(b"\x75\x00")
        wait_jump_index = len(stub) - 1
        stub.extend(b"\xC3")
        done_index = len(stub)
        stub.extend(b"\xC3")
        stub[skip_index] = (done_index - (skip_index + 1)) & 0xFF
        stub[wait_jump_index] = (wait_index - (wait_jump_index + 1)) & 0xFF
        return bytes(stub)

    def call_static(self, function_addr: int) -> None:
        if not function_addr or not self.mono.executor.scratch_base:
            raise RuntimeError("Main-thread dispatcher is not prepared.")
        with MAIN_THREAD_PATCH_LOCK:
            state_addr = self.mono.executor.scratch_base + 0x6000
            stub_addr = self.mono.executor.scratch_base + 0x6800
            stub = self.build_stub(state_addr, function_addr)
            entry_jump = b"\x48\xB8" + struct.pack("<Q", stub_addr) + b"\xFF\xE0"
            self.pm.write_bytes(stub_addr, stub, len(stub))
            self.pm.write_uchar(state_addr, 1)
            self.patcher.patch_custom(
                self.PATCH_ID, self.late_update_native, entry_jump
            )
            restored = False
            released = False
            started = self.clock()
            try:
                while True:
                    state = int(self.pm.read_uchar(state_addr))
                    if state == 3:
                        self.patcher.restore(self.PATCH_ID)
                        restored = True
                        self.pm.write_uchar(state_addr, 4)
                        released = True
                        return
                    if state not in {1, 2}:
                        raise RuntimeError(
                            f"Invalid main-thread dispatcher state: {state}"
                        )
                    if self.clock() - started >= self.TIMEOUT_SECONDS:
                        raise TimeoutError(
                            f"Unity main-thread call timed out in state {state}."
                        )
                    self.sleeper(0.005)
            finally:
                if not restored:
                    self.patcher.restore(self.PATCH_ID)
                if not released:
                    try:
                        if int(self.pm.read_uchar(state_addr)) == 3:
                            self.pm.write_uchar(state_addr, 4)
                    except Exception:
                        pass
