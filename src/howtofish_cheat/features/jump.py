"""Infinite Air Jump feature (pure movement patch, zero God Mode)."""

import logging
import struct
from typing import Optional
from .base import CheatFeature

logger = logging.getLogger(__name__)


class InfiniteJumpCheat(CheatFeature):
    """Allows infinite mid-air jumping without touching God Mode or health."""

    def __init__(
        self,
        pm: Optional[object] = None,
        mono: Optional[object] = None,
        patcher: Optional[object] = None,
        hotkey: str = "F3",
    ):
        super().__init__(
            name="Infinite Air Jump",
            description="Allows jumping in mid-air infinitely.",
            name_zh="无限多段跳 / 空中连跳",
            description_zh="允许在空中无限次起跳。",
            hotkey=hotkey,
            pm=pm,
            mono=mono,
            patcher=patcher,
        )
        self.jump_input_addr: Optional[int] = None
        self.jump_native_addr: Optional[int] = None
        self.patch_bytes: Optional[bytes] = None

    def prepare(self) -> bool:
        """Finds and JIT compiles PlayerMovement.JumpInput and PlayerMovement.Jump."""
        if not self.mono or not self.patcher:
            return False
        try:
            mov_cls = self.mono.find_class("Assembly-CSharp", "PlayerMovement")

            # 1. JIT compile JumpInput(CallbackContext context) - 1 parameter
            jump_input_m = self.mono.find_method(mov_cls, "JumpInput", 1)
            self.jump_input_addr = self.mono.compile_method(jump_input_m)

            # 2. JIT compile Jump() - 0 parameters
            jump_m = self.mono.find_method(mov_cls, "Jump", 0)
            self.jump_native_addr = self.mono.compile_method(jump_m)

            # 3. Build direct call trampoline:
            # sub rsp, 0x28
            # mov rax, jump_native_addr
            # call rax
            # add rsp, 0x28
            # ret
            stub = bytearray()
            stub.extend(b"\x48\x83\xEC\x28")
            stub.extend(b"\x48\xB8" + struct.pack("<Q", self.jump_native_addr))
            stub.extend(b"\xFF\xD0")
            stub.extend(b"\x48\x83\xC4\x28\xC3")
            self.patch_bytes = bytes(stub)

            # Register custom patch to cache original bytes
            self.patcher.register_custom("JumpInput", self.jump_input_addr, self.patch_bytes)
            return True
        except Exception as e:
            logger.error(f"Failed to prepare Infinite Air Jump: {e}")
            return False

    def enable(self) -> bool:
        """Applies trampoline to JumpInput to call Jump directly on keypress."""
        try:
            if not self.jump_input_addr or not self.patch_bytes:
                self.prepare()

            if self.jump_input_addr and self.patch_bytes:
                self.patcher.patch_custom("JumpInput", self.jump_input_addr, self.patch_bytes)

            self.is_enabled = True
            return True
        except Exception as e:
            logger.error(f"Failed to enable Infinite Air Jump: {e}")
            return False

    def disable(self) -> bool:
        """Restores original JumpInput logic (restores normal ground/coyote jumping)."""
        try:
            if self.patcher:
                self.patcher.restore("JumpInput")
            self.is_enabled = False
            return True
        except Exception as e:
            logger.error(f"Failed to disable Infinite Air Jump: {e}")
            return False
