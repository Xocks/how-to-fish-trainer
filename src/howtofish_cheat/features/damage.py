"""Damage Multiplier & One-Shot Kill cheat feature with pure real-time memory scaling."""

import logging
from typing import Dict, List, Optional
from .base import CheatFeature

logger = logging.getLogger(__name__)


class DamageMultiplierCheat(CheatFeature):
    """Cycles through damage multipliers (1x, 2x, 5x, 10x, One-Shot Kill) for all weapons, melee, and fists via in-memory scaling."""

    MODES: List[str] = ["1x (Normal)", "2x", "5x", "10x", "One-Shot Kill"]
    MULTIPLIERS: List[int] = [1, 2, 5, 10, 99999]

    def __init__(self, pm, mono, patcher=None, hotkey: str = "F5"):
        super().__init__(
            name="Damage Multiplier",
            description="Cycles damage multiplier for firearms, melee weapons, and punches (1x -> 2x -> 5x -> 10x -> One-Shot).",
            hotkey=hotkey,
            pm=pm,
            mono=mono,
            patcher=patcher,
        )
        self.current_mode_index: int = 0

        # Offsets
        self.local_player_ptr_addr: Optional[int] = None
        self.holding_offset: Optional[int] = None
        self.held_item_offset: Optional[int] = None
        self.item_melee_offset: Optional[int] = None
        self.item_weapon_offset: Optional[int] = None
        self.punching_offset: Optional[int] = None
        self.punch_damage_offset: Optional[int] = None

        self.melee_sharpness_offset: Optional[int] = None
        self.sharpness_damage_offset: Optional[int] = None

        self.weapon_attachments_offset: Optional[int] = None
        self.weapon_info_offset: Optional[int] = None
        self.attachments_bullets_offset: Optional[int] = None
        self.bullet_damage_offset: Optional[int] = None
        self.proj_damage_offset: Optional[int] = None

        # Base value caches to prevent compound scaling, enable safe 1x restoration,
        # support switching between multiple weapons in inventory, and maintain tick idempotence:
        # - Key: Memory address (pointer) of the specific upgrade / weapon component instance on Mono GC heap
        # - Value: Original, unmodified base damage integer read before any scaling was applied
        self._base_punch_damage: Optional[int] = None  # Unarmed punch damage (PlayerPunching._damage)
        self._base_sharpness_damages: Dict[int, int] = {}  # Melee upgrade damage (SharpnessUpgrade._damage ptr -> original value)
        self._base_bullet_damages: Dict[int, int] = {}  # Gun attachment/bullet upgrade damage (BulletUpgrade._damage ptr -> original value, used when weapon has bullet mods/upgrades)
        self._base_proj_damages: Dict[int, int] = {}  # Stock firearm base ballistic damage (WeaponInfo.ProjectileDamage ptr -> original value, used for stock/unmodified weapons)

    def prepare(self) -> bool:
        """Finds classes and caches memory offsets for live heap traversal."""
        try:
            player_cls = self.mono.find_class("Assembly-CSharp", "Player")
            punching_cls = self.mono.find_class("Assembly-CSharp", "PlayerPunching")
            holding_cls = self.mono.find_class("Assembly-CSharp", "PlayerHolding")
            item_cls = self.mono.find_class("Assembly-CSharp", "Item")
            melee_cls = self.mono.find_class("Assembly-CSharp", "Melee")
            sharpness_cls = self.mono.find_class("Assembly-CSharp", "SharpnessUpgrade")
            weapon_cls = self.mono.find_class("Assembly-CSharp", "Weapon")
            attachments_cls = self.mono.find_class("Assembly-CSharp", "Attachments")
            bullet_cls = self.mono.find_class("Assembly-CSharp", "BulletUpgrade")
            winfo_cls = self.mono.find_class("Assembly-CSharp", "WeaponInfo")

            # Resolve field offsets
            try:
                self.bullet_damage_offset = self.mono.get_field_offset(bullet_cls, "_damage")
                self.sharpness_damage_offset = self.mono.get_field_offset(sharpness_cls, "_damage")

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
                self.item_melee_offset = self.mono.get_field_offset(item_cls, "_melee")
                self.item_weapon_offset = self.mono.get_field_offset(item_cls, "_weapon")
                self.punching_offset = self.mono.get_field_offset(player_cls, "_playerPunching")
                self.punch_damage_offset = self.mono.get_field_offset(punching_cls, "_damage")

                self.melee_sharpness_offset = self.mono.get_field_offset(melee_cls, "_sharpnessUpgrades")
                self.weapon_attachments_offset = self.mono.get_field_offset(weapon_cls, "_attachments")
                self.weapon_info_offset = self.mono.get_field_offset(weapon_cls, "_weaponInfo")
                self.attachments_bullets_offset = self.mono.get_field_offset(attachments_cls, "_bulletUpgrades")

                try:
                    self.proj_damage_offset = self.mono.get_field_offset(winfo_cls, "<ProjectileDamage>k__BackingField")
                except Exception:
                    self.proj_damage_offset = self.mono.get_field_offset(winfo_cls, "_projectileDamage")
            except Exception as e:
                logger.debug(f"Could not resolve damage offsets: {e}")

            return self.local_player_ptr_addr is not None or self.punch_damage_offset is not None
        except Exception as e:
            logger.error(f"Failed to prepare Damage Multiplier: {e}")
            return False

    def apply_mode(self, mode_index: int) -> None:
        """Applies active memory scaling for the selected multiplier index."""
        self.current_mode_index = mode_index % len(self.MODES)
        multiplier = self.MULTIPLIERS[self.current_mode_index]

        if self.current_mode_index == 0:
            # 1x (Normal): restore all base damage values in memory
            self.restore_all_damages()
            self.is_enabled = False
            return

        self.is_enabled = True
        self._maintain_all_damages(multiplier)

    def toggle(self) -> bool:
        """Cycles to the next multiplier stage."""
        if not self.local_player_ptr_addr:
            self.prepare()
        next_mode = (self.current_mode_index + 1) % len(self.MODES)
        self.apply_mode(next_mode)
        return self.is_enabled

    def enable(self) -> bool:
        """Enables 2x multiplier if currently 1x, or re-applies current active mode."""
        if not self.local_player_ptr_addr:
            self.prepare()
        target_mode = self.current_mode_index if self.current_mode_index > 0 else 1
        self.apply_mode(target_mode)
        return True

    def disable(self) -> bool:
        """Restores original 1x game logic across all tracked weapons, inventory items, and dropped items."""
        self.apply_mode(0)
        return True

    def restore_all_damages(self) -> None:
        """Restores all cached base damage values across fists, melee weapons, firearms, inventory items, and dropped items in memory."""
        # 1. Restore punch damage (PlayerPunching._damage)
        if self.punching_offset and self.punch_damage_offset and self._base_punch_damage is not None:
            try:
                if self.local_player_ptr_addr:
                    lp_inst = self.pm.read_ulonglong(self.local_player_ptr_addr)
                    if lp_inst:
                        punching_inst = self.pm.read_ulonglong(lp_inst + self.punching_offset)
                        if punching_inst:
                            self.pm.write_int(punching_inst + self.punch_damage_offset, self._base_punch_damage)
            except Exception:
                pass

        # 2. Restore all tracked melee sharpness upgrades (held, in inventory, or dropped)
        if self.sharpness_damage_offset:
            for elem_ptr, base_val in list(self._base_sharpness_damages.items()):
                try:
                    self.pm.write_int(elem_ptr + self.sharpness_damage_offset, base_val)
                except Exception:
                    pass

        # 3. Restore all tracked bullet upgrades (held, in inventory, or dropped)
        if self.bullet_damage_offset:
            for elem_ptr, base_val in list(self._base_bullet_damages.items()):
                try:
                    self.pm.write_int(elem_ptr + self.bullet_damage_offset, base_val)
                except Exception:
                    pass

        # 4. Restore all tracked firearm projectile damages (held, in inventory, or dropped)
        if self.proj_damage_offset:
            for winfo_ptr, base_val in list(self._base_proj_damages.items()):
                try:
                    self.pm.write_int(winfo_ptr + self.proj_damage_offset, base_val)
                except Exception:
                    pass

    def _maintain_all_damages(self, multiplier: int) -> None:
        """Scales fists, held melee weapon upgrades, held firearm bullet upgrades, and projectile damage in memory.

        Maintains real-time scaling across all tracked weapons (currently held, stored in inventory,
        or dropped on the ground) to guarantee seamless weapon switching and clean restoration.
        """
        if multiplier == 1:
            self.restore_all_damages()
            return

        punching_inst = 0
        if self.local_player_ptr_addr:
            try:
                lp_inst = self.pm.read_ulonglong(self.local_player_ptr_addr)
                if lp_inst:
                    # 1. Discover punch damage (Fists)
                    if self.punching_offset and self.punch_damage_offset:
                        try:
                            punching_inst = self.pm.read_ulonglong(lp_inst + self.punching_offset)
                            if punching_inst:
                                cur_punch_dmg = self.pm.read_int(punching_inst + self.punch_damage_offset)
                                if self._base_punch_damage is None:
                                    if 0 < cur_punch_dmg < 99999:
                                        self._base_punch_damage = cur_punch_dmg
                        except Exception:
                            pass

                    # 2. Discover held item components (Melee or Weapon/Gun)
                    if self.holding_offset and self.held_item_offset:
                        try:
                            holding_inst = self.pm.read_ulonglong(lp_inst + self.holding_offset)
                            if holding_inst:
                                held_item = self.pm.read_ulonglong(holding_inst + self.held_item_offset)
                                if held_item:
                                    # A. Check if held_item has _melee component
                                    melee_inst = 0
                                    if self.item_melee_offset:
                                        melee_inst = self.pm.read_ulonglong(held_item + self.item_melee_offset)

                                    if melee_inst and self.melee_sharpness_offset and self.sharpness_damage_offset:
                                        try:
                                            sharpness_arr = self.pm.read_ulonglong(melee_inst + self.melee_sharpness_offset)
                                            if sharpness_arr:
                                                count = self.pm.read_uint(sharpness_arr + 0x18)
                                                if 0 < count < 20:
                                                    for i in range(count):
                                                        elem_ptr = self.pm.read_ulonglong(sharpness_arr + 0x20 + i * 8)
                                                        if elem_ptr and elem_ptr not in self._base_sharpness_damages:
                                                            raw_val = self.pm.read_int(elem_ptr + self.sharpness_damage_offset)
                                                            if 0 < raw_val < 99999:
                                                                self._base_sharpness_damages[elem_ptr] = raw_val
                                        except Exception:
                                            pass

                                    # B. Check if held_item has _weapon component
                                    weapon_inst = 0
                                    if self.item_weapon_offset:
                                        weapon_inst = self.pm.read_ulonglong(held_item + self.item_weapon_offset)

                                    if weapon_inst:
                                        if self.weapon_attachments_offset and self.bullet_damage_offset and self.attachments_bullets_offset:
                                            try:
                                                attachments_ptr = self.pm.read_ulonglong(weapon_inst + self.weapon_attachments_offset)
                                                if attachments_ptr:
                                                    bullets_arr = self.pm.read_ulonglong(attachments_ptr + self.attachments_bullets_offset)
                                                    if bullets_arr:
                                                        count = self.pm.read_uint(bullets_arr + 0x18)
                                                        if 0 < count < 20:
                                                            for i in range(count):
                                                                elem_ptr = self.pm.read_ulonglong(bullets_arr + 0x20 + i * 8)
                                                                if elem_ptr and elem_ptr not in self._base_bullet_damages:
                                                                    raw_val = self.pm.read_int(elem_ptr + self.bullet_damage_offset)
                                                                    if 0 < raw_val < 99999:
                                                                        self._base_bullet_damages[elem_ptr] = raw_val
                                            except Exception:
                                                pass

                                        # C. Check WeaponInfo.ProjectileDamage
                                        if self.weapon_info_offset and self.proj_damage_offset:
                                            try:
                                                winfo_ptr = self.pm.read_ulonglong(weapon_inst + self.weapon_info_offset)
                                                if winfo_ptr and winfo_ptr not in self._base_proj_damages:
                                                    raw_val = self.pm.read_int(winfo_ptr + self.proj_damage_offset)
                                                    if 0 < raw_val < 99999:
                                                        self._base_proj_damages[winfo_ptr] = raw_val
                                            except Exception:
                                                pass
                        except Exception:
                            pass
            except Exception:
                pass

        # 3. Apply active scaling to fists
        if self.punching_offset and self.punch_damage_offset and punching_inst:
            try:
                base_punch = self._base_punch_damage or 20
                target_punch = 99999 if multiplier >= 99999 else base_punch * multiplier
                self.pm.write_int(punching_inst + self.punch_damage_offset, target_punch)
            except Exception:
                pass

        # 4. Apply active scaling across ALL tracked melee weapons (held, inventory, dropped)
        if self.sharpness_damage_offset:
            for elem_ptr, base_val in list(self._base_sharpness_damages.items()):
                try:
                    target_val = 99999 if multiplier >= 99999 else base_val * multiplier
                    self.pm.write_int(elem_ptr + self.sharpness_damage_offset, target_val)
                except Exception:
                    pass

        # 5. Apply active scaling across ALL tracked bullet upgrades (held, inventory, dropped)
        if self.bullet_damage_offset:
            for elem_ptr, base_val in list(self._base_bullet_damages.items()):
                try:
                    target_val = 99999 if multiplier >= 99999 else base_val * multiplier
                    self.pm.write_int(elem_ptr + self.bullet_damage_offset, target_val)
                except Exception:
                    pass

        # 6. Apply active scaling across ALL tracked firearm projectile damages (held, inventory, dropped)
        if self.proj_damage_offset:
            for winfo_ptr, base_val in list(self._base_proj_damages.items()):
                try:
                    target_val = 99999 if multiplier >= 99999 else base_val * multiplier
                    self.pm.write_int(winfo_ptr + self.proj_damage_offset, target_val)
                except Exception:
                    pass

    def update(self) -> None:
        """Maintains active damage scaling during live gameplay ticks."""
        if self.is_enabled and self.current_mode_index > 0:
            multiplier = self.MULTIPLIERS[self.current_mode_index]
            self._maintain_all_damages(multiplier)

    def get_status_badge(self) -> str:
        """Returns a rich formatted status badge reflecting the active multiplier mode."""
        mode_name = self.MODES[self.current_mode_index]
        if self.current_mode_index == 0:
            return "[dim red]DISABLED (1x)[/dim red]"
        elif self.current_mode_index == 1:
            return "[bold green]ACTIVE (2x)[/bold green]"
        elif self.current_mode_index == 2:
            return "[bold green]ACTIVE (5x)[/bold green]"
        elif self.current_mode_index == 3:
            return "[bold yellow]ACTIVE (10x)[/bold yellow]"
        else:
            return "[bold red]ONE-SHOT KILL[/bold red]"
