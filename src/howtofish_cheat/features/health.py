"""Lock Health cheat feature with elemental dissipation."""

import logging
from typing import Dict, Optional
from .base import CheatFeature

logger = logging.getLogger(__name__)


class LockHealthCheat(CheatFeature):
    """Locks player health, disables incoming damage, and dissipates elemental gauges without altering movement."""

    def __init__(self, pm, mono, patcher, hotkey: str = "F1"):
        super().__init__(
            name="Lock Health",
            description="Blocks all damage and dissipates fire/poison gauges (normal jump physics preserved).",
            hotkey=hotkey,
            pm=pm,
            mono=mono,
            patcher=patcher,
        )
        self.method_addrs: Dict[str, int] = {}

        # Player & Vitals offsets for real-time memory locking
        self.local_player_ptr_addr: Optional[int] = None
        self.vitals_offset: Optional[int] = None
        self.local_hp_offset: Optional[int] = None
        self.prev_hp_offset: Optional[int] = None
        self.invuln_offset: Optional[int] = None
        self.local_is_dead_offset: Optional[int] = None
        self.prev_fire_offset: Optional[int] = None
        self.prev_poison_offset: Optional[int] = None

    def prepare(self) -> bool:
        """Finds and JIT compiles all damage and elemental methods, and caches memory offsets."""
        try:
            vitals_cls = self.mono.find_class("Assembly-CSharp", "PlayerVitals")
            player_cls = self.mono.find_class("Assembly-CSharp", "Player")

            # 1. JIT compile all damage & elemental status bottlenecks
            methods_to_compile = [
                ("TakeDamage", 4),
                ("LocalHit", 7),
                ("DamageFromFullness", 0),
                ("ApplyNewFire", 0),
                ("ApplyNewPoison", 0),
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

                self.local_hp_offset = self.mono.get_field_offset(vitals_cls, "_localHp")
                self.prev_hp_offset = self.mono.get_field_offset(vitals_cls, "_prevHealth")
                self.invuln_offset = self.mono.get_field_offset(vitals_cls, "_invulnerableUntil")
                self.local_is_dead_offset = self.mono.get_field_offset(vitals_cls, "_localIsDead")
                self.prev_fire_offset = self.mono.get_field_offset(vitals_cls, "_prevFire")
                self.prev_poison_offset = self.mono.get_field_offset(vitals_cls, "_prevPoison")
            except Exception as e:
                logger.debug(f"Could not resolve LocalPlayer vitals offsets: {e}")

            return len(self.method_addrs) > 0
        except Exception as e:
            logger.error(f"Failed to prepare Lock Health: {e}")
            return False

    def enable(self) -> bool:
        """Applies JIT patches to block all damage."""
        try:
            if not self.method_addrs:
                self.prepare()

            for mname, native_addr in self.method_addrs.items():
                self.patcher.patch_ret(mname, native_addr)

            self._maintain_health()
            self.is_enabled = True
            return True
        except Exception as e:
            logger.error(f"Failed to enable Lock Health: {e}")
            return False

    def disable(self) -> bool:
        """Restores original code and resets invulnerability timer."""
        try:
            for mname in self.method_addrs.keys():
                self.patcher.restore(mname)

            self._reset_invulnerability()
            self.is_enabled = False
            return True
        except Exception as e:
            logger.error(f"Failed to disable Lock Health: {e}")
            return False

    def _maintain_health(self) -> None:
        """Forces HP to 100, sets invulnerability timer, and clears fire/poison elemental meters."""
        if not self.local_player_ptr_addr or not self.vitals_offset:
            return
        try:
            lp_inst = self.pm.read_ulonglong(self.local_player_ptr_addr)
            if not lp_inst:
                return

            vitals_inst = self.pm.read_ulonglong(lp_inst + self.vitals_offset)
            if not vitals_inst:
                return

            if self.local_hp_offset:
                self.pm.write_int(vitals_inst + self.local_hp_offset, 100)
            if self.prev_hp_offset:
                self.pm.write_int(vitals_inst + self.prev_hp_offset, 100)
            if self.invuln_offset:
                self.pm.write_float(vitals_inst + self.invuln_offset, 999999.0)
            if self.local_is_dead_offset:
                self.pm.write_uchar(vitals_inst + self.local_is_dead_offset, 0)

            # Dissipate elemental status gauges
            if self.prev_fire_offset:
                self.pm.write_int(vitals_inst + self.prev_fire_offset, 0)
            if self.prev_poison_offset:
                self.pm.write_int(vitals_inst + self.prev_poison_offset, 0)
        except Exception:
            pass

    def _reset_invulnerability(self) -> None:
        """Resets invulnerability timer to 0 so the player can take normal damage again."""
        if not self.local_player_ptr_addr or not self.vitals_offset or not self.invuln_offset:
            return
        try:
            lp_inst = self.pm.read_ulonglong(self.local_player_ptr_addr)
            if lp_inst:
                vitals_inst = self.pm.read_ulonglong(lp_inst + self.vitals_offset)
                if vitals_inst:
                    self.pm.write_float(vitals_inst + self.invuln_offset, 0.0)
        except Exception:
            pass

    def update(self) -> None:
        """Maintains health and elemental dissipation every tick."""
        if self.is_enabled:
            self._maintain_health()
