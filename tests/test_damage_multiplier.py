"""Unit tests for DamageMultiplierCheat and trainer integration."""

import unittest
from unittest.mock import MagicMock
from howtofish_cheat.features.damage import DamageMultiplierCheat
from howtofish_cheat.trainer import HowToFishTrainer
from howtofish_cheat.ui.console import TrainerUI


class TestDamageMultiplier(unittest.TestCase):
    def setUp(self):
        self.mock_pm = MagicMock()
        self.mock_mono = MagicMock()
        self.mock_patcher = MagicMock()

    def test_feature_initialization(self):
        cheat = DamageMultiplierCheat(self.mock_pm, self.mock_mono, self.mock_patcher, hotkey="F5")
        self.assertEqual(cheat.name, "Damage Multiplier")
        self.assertEqual(cheat.hotkey, "F5")
        self.assertEqual(cheat.current_mode_index, 0)
        self.assertFalse(cheat.is_enabled)
        self.assertIn("1x", cheat.get_status_badge())

    def test_mode_cycling(self):
        cheat = DamageMultiplierCheat(self.mock_pm, self.mock_mono, self.mock_patcher, hotkey="F5")
        cheat.local_player_ptr_addr = 0x10000
        cheat.punching_offset = 0x40
        cheat.punch_damage_offset = 0x50

        # 1. Toggle to 2x
        cheat.toggle()
        self.assertEqual(cheat.current_mode_index, 1)
        self.assertTrue(cheat.is_enabled)
        self.assertIn("2x", cheat.get_status_badge())

        # 2. Toggle to 5x
        cheat.toggle()
        self.assertEqual(cheat.current_mode_index, 2)
        self.assertTrue(cheat.is_enabled)
        self.assertIn("5x", cheat.get_status_badge())

        # 3. Toggle to 10x
        cheat.toggle()
        self.assertEqual(cheat.current_mode_index, 3)
        self.assertTrue(cheat.is_enabled)
        self.assertIn("10x", cheat.get_status_badge())

        # 4. Toggle to One-Shot Kill
        cheat.toggle()
        self.assertEqual(cheat.current_mode_index, 4)
        self.assertTrue(cheat.is_enabled)
        self.assertIn("ONE-SHOT", cheat.get_status_badge())

        # 5. Toggle back to 1x (Disabled)
        cheat.toggle()
        self.assertEqual(cheat.current_mode_index, 0)
        self.assertFalse(cheat.is_enabled)
        self.assertIn("1x", cheat.get_status_badge())

    def test_in_memory_damage_maintenance(self):
        cheat = DamageMultiplierCheat(self.mock_pm, self.mock_mono, self.mock_patcher, hotkey="F5")
        cheat.local_player_ptr_addr = 0x10000
        cheat.holding_offset = 0x20
        cheat.held_item_offset = 0x30
        cheat.item_melee_offset = 0x38
        cheat.item_weapon_offset = 0x3C
        cheat.punching_offset = 0x40
        cheat.punch_damage_offset = 0x50

        cheat.melee_sharpness_offset = 0x60
        cheat.sharpness_damage_offset = 0x10

        cheat.weapon_attachments_offset = 0x70
        cheat.attachments_bullets_offset = 0x80
        cheat.bullet_damage_offset = 0x10

        cheat.weapon_info_offset = 0x90
        cheat.proj_damage_offset = 0x14

        def mock_read_ulonglong(addr):
            mapping = {
                0x10000: 0x20000, # local_player
                0x20000 + 0x40: 0x30000, # punching
                0x20000 + 0x20: 0x40000, # holding
                0x40000 + 0x30: 0x50000, # held_item
                0x50000 + 0x38: 0x51000, # item._melee
                0x50000 + 0x3C: 0x52000, # item._weapon
                0x51000 + 0x60: 0x60000, # sharpness_arr
                0x60000 + 0x20: 0x61000, # sharpness elem 0
                0x60000 + 0x28: 0x62000, # sharpness elem 1
                0x52000 + 0x70: 0x70000, # attachments_ptr
                0x70000 + 0x80: 0x80000, # bullets_arr
                0x80000 + 0x20: 0x81000, # bullet elem 0
                0x80000 + 0x28: 0x82000, # bullet elem 1
                0x52000 + 0x90: 0x90000, # weapon_info
            }
            return mapping.get(addr, 0)

        def mock_read_uint(addr):
            if addr == 0x60000 + 0x18:
                return 2
            if addr == 0x80000 + 0x18:
                return 2
            return 0

        def mock_read_int(addr):
            mapping = {
                0x30000 + 0x50: 20, # punch damage
                0x61000 + 0x10: 25, # sharpness 0
                0x62000 + 0x10: 35, # sharpness 1
                0x81000 + 0x10: 30, # bullet 0
                0x82000 + 0x10: 45, # bullet 1
                0x90000 + 0x14: 40, # proj damage
            }
            return mapping.get(addr, 0)

        self.mock_pm.read_ulonglong.side_effect = mock_read_ulonglong
        self.mock_pm.read_uint.side_effect = mock_read_uint
        self.mock_pm.read_int.side_effect = mock_read_int

        # Apply 5x multiplier
        cheat._maintain_all_damages(5)

        # Assert punch scaled: 20 * 5 = 100
        self.mock_pm.write_int.assert_any_call(0x30000 + 0x50, 100)
        # Assert sharpness scaled: 25 * 5 = 125, 35 * 5 = 175
        self.mock_pm.write_int.assert_any_call(0x61000 + 0x10, 125)
        self.mock_pm.write_int.assert_any_call(0x62000 + 0x10, 175)
        # Assert bullet scaled: 30 * 5 = 150, 45 * 5 = 225
        self.mock_pm.write_int.assert_any_call(0x81000 + 0x10, 150)
        self.mock_pm.write_int.assert_any_call(0x82000 + 0x10, 225)
        # Assert proj damage scaled: 40 * 5 = 200
        self.mock_pm.write_int.assert_any_call(0x90000 + 0x14, 200)

        # Restore to 1x
        cheat._maintain_all_damages(1)
        self.mock_pm.write_int.assert_any_call(0x30000 + 0x50, 20)
        self.mock_pm.write_int.assert_any_call(0x61000 + 0x10, 25)
        self.mock_pm.write_int.assert_any_call(0x62000 + 0x10, 35)
        self.mock_pm.write_int.assert_any_call(0x81000 + 0x10, 30)
        self.mock_pm.write_int.assert_any_call(0x82000 + 0x10, 45)
        self.mock_pm.write_int.assert_any_call(0x90000 + 0x14, 40)

    def test_inventory_and_dropped_items_restoration_on_exit(self):
        """Verifies that weapons moved to inventory or dropped on the ground have their base damages restored upon exit."""
        cheat = DamageMultiplierCheat(self.mock_pm, self.mock_mono, self.mock_patcher, hotkey="F5")
        cheat.local_player_ptr_addr = 0x10000
        cheat.holding_offset = 0x20
        cheat.held_item_offset = 0x30
        cheat.item_melee_offset = 0x38
        cheat.item_weapon_offset = 0x3C
        cheat.punching_offset = 0x40
        cheat.punch_damage_offset = 0x50

        cheat.melee_sharpness_offset = 0x60
        cheat.sharpness_damage_offset = 0x10

        cheat.weapon_attachments_offset = 0x70
        cheat.attachments_bullets_offset = 0x80
        cheat.bullet_damage_offset = 0x10

        cheat.weapon_info_offset = 0x90
        cheat.proj_damage_offset = 0x14

        # Scenario: Player equips firearm (Item A) first
        current_held_item = [0x50000]  # Item A (Firearm)

        def mock_read_ulonglong(addr):
            mapping = {
                0x10000: 0x20000,  # local_player
                0x20000 + 0x40: 0x30000,  # punching
                0x20000 + 0x20: 0x40000,  # holding
                0x40000 + 0x30: current_held_item[0],  # held_item (dynamic)
                # Item A (Firearm)
                0x50000 + 0x38: 0,  # no melee
                0x50000 + 0x3C: 0x52000,  # weapon component
                0x52000 + 0x70: 0x70000,  # attachments
                0x70000 + 0x80: 0x80000,  # bullets_arr
                0x80000 + 0x20: 0x81000,  # bullet elem 0
                0x80000 + 0x28: 0x82000,  # bullet elem 1
                0x52000 + 0x90: 0x90000,  # weapon_info
                # Item B (Melee Sword)
                0x55000 + 0x38: 0x51000,  # melee component
                0x55000 + 0x3C: 0,  # no weapon
                0x51000 + 0x60: 0x60000,  # sharpness_arr
                0x60000 + 0x20: 0x61000,  # sharpness elem 0
                0x60000 + 0x28: 0x62000,  # sharpness elem 1
            }
            return mapping.get(addr, 0)

        def mock_read_uint(addr):
            if addr in (0x60000 + 0x18, 0x80000 + 0x18):
                return 2
            return 0

        def mock_read_int(addr):
            mapping = {
                0x30000 + 0x50: 20,  # punch damage
                0x81000 + 0x10: 30,  # firearm bullet 0
                0x82000 + 0x10: 45,  # firearm bullet 1
                0x90000 + 0x14: 40,  # firearm proj damage
                0x61000 + 0x10: 25,  # sword sharpness 0
                0x62000 + 0x10: 35,  # sword sharpness 1
            }
            return mapping.get(addr, 0)

        self.mock_pm.read_ulonglong.side_effect = mock_read_ulonglong
        self.mock_pm.read_uint.side_effect = mock_read_uint
        self.mock_pm.read_int.side_effect = mock_read_int

        # Step 1: Scale firearm while held with 10x multiplier
        cheat.apply_mode(3)  # 10x
        self.mock_pm.write_int.assert_any_call(0x81000 + 0x10, 300)
        self.mock_pm.write_int.assert_any_call(0x82000 + 0x10, 450)
        self.mock_pm.write_int.assert_any_call(0x90000 + 0x14, 400)

        # Step 2: Player switches to sword (firearm is moved to inventory or dropped)
        current_held_item[0] = 0x55000  # Item B (Sword)
        cheat.update()
        self.mock_pm.write_int.assert_any_call(0x61000 + 0x10, 250)
        self.mock_pm.write_int.assert_any_call(0x62000 + 0x10, 350)

        # Reset mock write calls to cleanly test exit restoration
        self.mock_pm.write_int.reset_mock()

        # Step 3: Disable cheat / exit trainer while sword is held
        cheat.disable()

        # Assert BOTH sword (held) AND firearm (in inventory / on ground) AND fists are restored to 1x base values
        self.mock_pm.write_int.assert_any_call(0x30000 + 0x50, 20)  # Punch restored
        self.mock_pm.write_int.assert_any_call(0x61000 + 0x10, 25)  # Sword sharpness 0 restored
        self.mock_pm.write_int.assert_any_call(0x62000 + 0x10, 35)  # Sword sharpness 1 restored
        self.mock_pm.write_int.assert_any_call(0x81000 + 0x10, 30)  # Firearm bullet 0 restored
        self.mock_pm.write_int.assert_any_call(0x82000 + 0x10, 45)  # Firearm bullet 1 restored
        self.mock_pm.write_int.assert_any_call(0x90000 + 0x14, 40)  # Firearm proj damage restored

    def test_trainer_setup_and_ui(self):
        trainer = HowToFishTrainer()
        trainer.pm = self.mock_pm
        trainer.mono = self.mock_mono
        trainer.patcher = self.mock_patcher

        self.mock_mono.find_class.return_value = 0x12345
        self.mock_mono.find_method.return_value = 0x67890
        self.mock_mono.compile_method.return_value = 0xABCDE
        self.mock_mono.get_field_offset.return_value = 0x10
        self.mock_mono.get_export.return_value = 0x11111
        self.mock_mono.executor.call.return_value = 0x22222

        trainer._setup_features()
        self.assertEqual(len(trainer.features), 7)
        feature_names = [f.name for f in trainer.features]
        self.assertIn("Damage Multiplier", feature_names)
        self.assertIn("Add Money (+1w)", feature_names)

        # Verify UI render with all 7 cheats
        ui = TrainerUI()
        panel = ui.generate_dashboard(
            is_attached=True,
            process_name="How to Fish.exe",
            pid=1234,
            mono_domain=0x99999,
            features=trainer.features,
            status_message="Ready. Press F1 / F2 / F3 / F4 / F5 / F6.",
        )
        self.assertIsNotNone(panel)


if __name__ == "__main__":
    unittest.main()

