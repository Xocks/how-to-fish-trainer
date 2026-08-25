"""Lock Hunger and Infinite Fullness cheat feature."""

import logging
from typing import Dict, Optional
from .base import CheatFeature

logger = logging.getLogger(__name__)


class LockHungerCheat(CheatFeature):
    """Locks fullness/hunger meter and prevents hunger depletion."""

    def __init__(
        self,
        pm: Optional[object] = None,
        mono: Optional[object] = None,
        patcher: Optional[object] = None,
        hotkey: str = "F2",
    ):
        super().__init__(
            name="Lock Hunger / Infinite Fullness",
            description="Locks fullness meter at 100 and prevents hunger depletion over time or actions.",
            name_zh="锁定饱食度 / 无限饱腹",
            description_zh="锁定饱食度100，防止饱食度随时间或动作消耗。",
            hotkey=hotkey,
            pm=pm,
            mono=mono,
            patcher=patcher,
        )
        self.method_addrs: Dict[str, int] = {}
        self.local_player_ptr_addr: Optional[int] = None
        self.vitals_offset: Optional[int] = None
        self.prev_fullness_offset: Optional[int] = None
        self.synced_fullness_offset: Optional[int] = None
        self.on_fullness_change_native: Optional[int] = None

    def prepare(self) -> bool:
        """Finds and JIT compiles required hunger methods and caches memory offsets."""
        if not self.mono or not self.patcher or not self.pm:
            return False
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

            # JIT compile OnFullnessChange for UI animation and networking synchronization
            try:
                on_fn_m = self.mono.find_method(vitals_cls, "OnFullnessChange", 3)
                self.on_fullness_change_native = self.mono.compile_method(on_fn_m)
            except Exception as e:
                logger.debug(f"Could not compile OnFullnessChange: {e}")

            # 2. Resolve Player.LocalPlayer static address and field offsets
            try:
                p_vtable = self.mono.executor.call(self.mono.get_export("mono_class_vtable"), self.mono.root_domain, player_cls)
                p_static = self.mono.executor.call(self.mono.get_export("mono_vtable_get_static_field_data"), p_vtable)
                lp_offset = self.mono.get_field_offset(player_cls, "LocalPlayer")
                self.local_player_ptr_addr = p_static + lp_offset
                self.vitals_offset = self.mono.get_field_offset(player_cls, "_playerVitals")
                self.prev_fullness_offset = self.mono.get_field_offset(vitals_cls, "_prevFullness")
                self.synced_fullness_offset = self.mono.get_field_offset(vitals_cls, "_syncedFullness")
            except Exception as e:
                logger.debug(f"Could not resolve LocalPlayer hunger offsets: {e}")

            return len(self.method_addrs) > 0
        except Exception as e:
            logger.error(f"Failed to prepare Lock Hunger: {e}")
            return False

    def enable(self) -> bool:
        """Applies JIT patches to hunger methods and sets fullness to 100 on activation."""
        try:
            if not self.method_addrs:
                self.prepare()

            for mname, native_addr in self.method_addrs.items():
                self.patcher.patch_ret(mname, native_addr)

            # Set fullness to 100 once upon activation
            self._set_fullness_to_100()

            # Trigger native UI refresh
            if self.on_fullness_change_native and self.local_player_ptr_addr and self.vitals_offset:
                try:
                    lp_inst = self.pm.read_ulonglong(self.local_player_ptr_addr)
                    if lp_inst:
                        vitals_inst = self.pm.read_ulonglong(lp_inst + self.vitals_offset)
                        if vitals_inst:
                            # OnFullnessChange(this, prev, next, asServer) -> (vitals_inst, 100, 100, 0)
                            self.mono.executor.call(self.on_fullness_change_native, vitals_inst, 100, 100, 0)
                except Exception:
                    pass

            self.is_enabled = True
            return True
        except Exception as e:
            logger.error(f"Failed to enable Lock Hunger: {e}")
            return False

    def disable(self) -> bool:
        """Restores original hunger methods."""
        try:
            if self.patcher:
                for mname in self.method_addrs.keys():
                    self.patcher.restore(mname)

            self.is_enabled = False
            return True
        except Exception as e:
            logger.error(f"Failed to disable Lock Hunger: {e}")
            return False

    def _set_fullness_to_100(self) -> None:
        """Forces fullness meter to 100 in memory and SyncVar upon activation."""
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

            if self.synced_fullness_offset:
                synced_fn_ptr = self.pm.read_ulonglong(vitals_inst + self.synced_fullness_offset)
                if synced_fn_ptr:
                    self.pm.write_int(synced_fn_ptr + 0x6C, 100)
                    self.pm.write_int(synced_fn_ptr + 0x70, 100)
        except Exception:
            pass

    def update(self) -> None:
        """No-op on tick since LowerFullness methods are JIT-patched with RET."""
        pass
