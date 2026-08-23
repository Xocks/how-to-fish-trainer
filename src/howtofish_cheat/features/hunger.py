"""Lock Hunger and Infinite Fullness cheat feature."""

import logging
from typing import Dict, Optional
from .base import CheatFeature

logger = logging.getLogger(__name__)


class LockHungerCheat(CheatFeature):
    """Locks fullness/hunger meter and prevents hunger depletion."""

    def __init__(self, pm, mono, patcher, hotkey: str = "F2"):
        super().__init__(
            name="Lock Hunger / Infinite Fullness",
            description="Prevents fullness meter from dropping over time or during actions.",
            hotkey=hotkey,
            pm=pm,
            mono=mono,
            patcher=patcher,
        )
        self.method_addrs: Dict[str, int] = {}
        self.local_player_ptr_addr: Optional[int] = None
        self.vitals_offset: Optional[int] = None
        self.prev_fullness_offset: Optional[int] = None

    def prepare(self) -> bool:
        """Finds and JIT compiles required hunger methods and caches memory offsets."""
        try:
            vitals_cls = self.mono.find_class("Assembly-CSharp", "PlayerVitals")
            player_cls = self.mono.find_class("Assembly-CSharp", "Player")

            # 1. JIT compile hunger depletion methods
            methods_to_compile = [
                ("LowerFullness", 1),
                ("LowerFullnessTick", 0),
            ]
            for mname, pcount in methods_to_compile:
                try:
                    mptr = self.mono.find_method(vitals_cls, mname, pcount)
                    native_addr = self.mono.compile_method(mptr)
                    self.method_addrs[mname] = native_addr
                    self.patcher.register_method(mname, native_addr)
                except Exception as e:
                    logger.debug(f"Could not compile {mname}: {e}")

            # 2. Resolve Player.LocalPlayer static address and field offsets
            try:
                p_vtable = self.mono.executor.call(self.mono.get_export("mono_class_vtable"), self.mono.root_domain, player_cls)
                p_static = self.mono.executor.call(self.mono.get_export("mono_vtable_get_static_field_data"), p_vtable)
                lp_offset = self.mono.get_field_offset(player_cls, "LocalPlayer")
                self.local_player_ptr_addr = p_static + lp_offset
                self.vitals_offset = self.mono.get_field_offset(player_cls, "_playerVitals")
                self.prev_fullness_offset = self.mono.get_field_offset(vitals_cls, "_prevFullness")
            except Exception as e:
                logger.debug(f"Could not resolve LocalPlayer hunger offsets: {e}")

            return len(self.method_addrs) > 0
        except Exception as e:
            logger.error(f"Failed to prepare Lock Hunger: {e}")
            return False

    def enable(self) -> bool:
        """Applies JIT patches to hunger methods."""
        try:
            if not self.method_addrs:
                self.prepare()

            for mname, native_addr in self.method_addrs.items():
                self.patcher.patch_ret(mname, native_addr)

            self._maintain_hunger()
            self.is_enabled = True
            return True
        except Exception as e:
            logger.error(f"Failed to enable Lock Hunger: {e}")
            return False

    def disable(self) -> bool:
        """Restores original hunger methods."""
        try:
            for mname in self.method_addrs.keys():
                self.patcher.restore(mname)

            self.is_enabled = False
            return True
        except Exception as e:
            logger.error(f"Failed to disable Lock Hunger: {e}")
            return False

    def _maintain_hunger(self) -> None:
        """Forces fullness meter to 100 in memory."""
        if not self.local_player_ptr_addr or not self.vitals_offset:
            return
        try:
            lp_inst = self.pm.read_ulonglong(self.local_player_ptr_addr)
            if not lp_inst:
                return

            vitals_inst = self.pm.read_ulonglong(lp_inst + self.vitals_offset)
            if not vitals_inst:
                return

            if self.prev_fullness_offset:
                self.pm.write_int(vitals_inst + self.prev_fullness_offset, 100)
        except Exception:
            pass

    def update(self) -> None:
        """Maintains hunger every tick."""
        if self.is_enabled:
            self._maintain_hunger()
