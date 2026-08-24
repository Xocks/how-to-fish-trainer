"""Unlimited Ammo cheat feature with JIT hook and active memory lock."""

import logging
from typing import Dict, Optional
from .base import CheatFeature

logger = logging.getLogger(__name__)


class UnlimitedAmmoCheat(CheatFeature):
    """Provides infinite ammunition for all firearms by hooking set_Ammo and locking weapon ammo in memory."""

    def __init__(self, pm, mono, patcher, hotkey: str = "F4"):
        super().__init__(
            name="Unlimited Ammo",
            description="Infinite ammunition for all weapons (no ammo consumption or reload interruptions).",
            name_zh="无限弹药 / 免换弹",
            description_zh="所有枪械无限弹药(不消耗子弹且无换弹打断)。",
            hotkey=hotkey,
            pm=pm,
            mono=mono,
            patcher=patcher,
        )
        self.method_addrs: Dict[str, int] = {}

        # Player & Holding & Weapon offsets
        self.local_player_ptr_addr: Optional[int] = None
        self.holding_offset: Optional[int] = None
        self.held_item_offset: Optional[int] = None
        self.item_weapon_offset: Optional[int] = None
        self.ammo_offset: Optional[int] = None
        self.is_reloading_offset: Optional[int] = None
        self.queue_reload_offset: Optional[int] = None

    def prepare(self) -> bool:
        """Finds and JIT compiles Weapon.set_Ammo and caches memory offsets."""
        try:
            player_cls = self.mono.find_class("Assembly-CSharp", "Player")
            holding_cls = self.mono.find_class("Assembly-CSharp", "PlayerHolding")
            item_cls = self.mono.find_class("Assembly-CSharp", "Item")
            weapon_cls = self.mono.find_class("Assembly-CSharp", "Weapon")

            # 1. JIT compile Weapon.set_Ammo(int value) -> 1 parameter
            try:
                set_ammo_m = self.mono.find_method(weapon_cls, "set_Ammo", 1)
                set_ammo_addr = self.mono.compile_method(set_ammo_m)
                self.method_addrs["set_Ammo"] = set_ammo_addr
                self.patcher.register_method("set_Ammo", set_ammo_addr)
            except Exception as e:
                logger.debug(f"Could not compile Weapon.set_Ammo: {e}")

            # 2. Resolve Player.LocalPlayer static address and field offsets
            try:
                p_vtable = self.mono.executor.call(
                    self.mono.get_export("mono_class_vtable"), self.mono.root_domain, player_cls
                )
                p_static = self.mono.executor.call(
                    self.mono.get_export("mono_vtable_get_static_field_data"), p_vtable
                )
                lp_offset = self.mono.get_field_offset(player_cls, "LocalPlayer")
                self.local_player_ptr_addr = p_static + lp_offset

                self.holding_offset = self.mono.get_field_offset(player_cls, "_holding")
                self.held_item_offset = self.mono.get_field_offset(holding_cls, "_heldItem")
                self.item_weapon_offset = self.mono.get_field_offset(item_cls, "_weapon")
                self.ammo_offset = self.mono.get_field_offset(weapon_cls, "<Ammo>k__BackingField")
                self.is_reloading_offset = self.mono.get_field_offset(weapon_cls, "_isReloading")
                self.queue_reload_offset = self.mono.get_field_offset(weapon_cls, "_queueReload")
            except Exception as e:
                logger.debug(f"Could not resolve LocalPlayer weapon offsets: {e}")

            return len(self.method_addrs) > 0 or self.local_player_ptr_addr is not None
        except Exception as e:
            logger.error(f"Failed to prepare Unlimited Ammo: {e}")
            return False

    def enable(self) -> bool:
        """Applies JIT patch to Weapon.set_Ammo and locks ammo in memory."""
        try:
            if not self.method_addrs:
                self.prepare()

            for mname, native_addr in self.method_addrs.items():
                self.patcher.patch_ret(mname, native_addr)

            self._maintain_ammo()
            self.is_enabled = True
            return True
        except Exception as e:
            logger.error(f"Failed to enable Unlimited Ammo: {e}")
            return False

    def disable(self) -> bool:
        """Restores original Weapon.set_Ammo bytecode."""
        try:
            for mname in self.method_addrs.keys():
                self.patcher.restore(mname)

            self.is_enabled = False
            return True
        except Exception as e:
            logger.error(f"Failed to disable Unlimited Ammo: {e}")
            return False

    def _maintain_ammo(self) -> None:
        """Locks held weapon ammo to 999 and clears reload flags."""
        if not self.local_player_ptr_addr or not self.holding_offset or not self.held_item_offset:
            return
        try:
            lp_inst = self.pm.read_ulonglong(self.local_player_ptr_addr)
            if not lp_inst:
                return

            holding_inst = self.pm.read_ulonglong(lp_inst + self.holding_offset)
            if not holding_inst:
                return

            held_item = self.pm.read_ulonglong(holding_inst + self.held_item_offset)
            if not held_item:
                return

            # Retrieve weapon instance (either held_item directly or held_item._weapon)
            weapon_inst = held_item
            if self.item_weapon_offset:
                w_ptr = self.pm.read_ulonglong(held_item + self.item_weapon_offset)
                if w_ptr:
                    weapon_inst = w_ptr

            if self.ammo_offset:
                self.pm.write_int(weapon_inst + self.ammo_offset, 999)
            if self.is_reloading_offset:
                self.pm.write_uchar(weapon_inst + self.is_reloading_offset, 0)
            if self.queue_reload_offset:
                self.pm.write_uchar(weapon_inst + self.queue_reload_offset, 0)
        except Exception:
            pass

    def update(self) -> None:
        """Maintains ammo lock each tick."""
        if self.is_enabled:
            self._maintain_ammo()
