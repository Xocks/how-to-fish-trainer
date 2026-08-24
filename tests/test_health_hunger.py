"""Unit tests for LockHealthCheat and LockHungerCheat features."""

import unittest
from unittest.mock import MagicMock
from howtofish_cheat.features.health import LockHealthCheat
from howtofish_cheat.features.hunger import LockHungerCheat


class TestHealthAndHungerCheats(unittest.TestCase):
    def setUp(self):
        self.mock_pm = MagicMock()
        self.mock_mono = MagicMock()
        self.mock_patcher = MagicMock()

    def test_lock_health_initialization(self):
        cheat = LockHealthCheat(self.mock_pm, self.mock_mono, self.mock_patcher, hotkey="F1")
        self.assertEqual(cheat.name, "Lock Health")
        self.assertEqual(cheat.hotkey, "F1")
        self.assertIn("100", cheat.description)
        self.assertFalse(cheat.is_enabled)

    def test_lock_health_prepare(self):
        self.mock_mono.find_class.side_effect = lambda asm, cls: {
            "PlayerVitals": 0x1000,
            "Player": 0x2000,
        }.get(cls, 0)

        self.mock_mono.get_export.return_value = 0x5555
        self.mock_mono.executor.call.side_effect = [
            0x2100,  # vtable Player
            0x2200,  # static_data Player
        ]

        def mock_get_field_offset(cls, name):
            if cls == 0x2000:
                if name == "LocalPlayer":
                    return 0x10
                elif name == "_playerVitals":
                    return 0x20
            elif cls == 0x1000:
                fields = {
                    "_localHp": 0x194,
                    "_prevHealth": 0x184,
                    "_syncedHealth": 0x0F0,
                    "_invulnerableUntil": 0x19C,
                    "_localIsDead": 0x198,
                    "_prevFire": 0x190,
                    "_prevPoison": 0x18C,
                }
                return fields.get(name, 0)
            return 0

        self.mock_mono.get_field_offset.side_effect = mock_get_field_offset
        self.mock_mono.find_method.return_value = 0x4000
        self.mock_mono.compile_method.return_value = 0x8000

        cheat = LockHealthCheat(self.mock_pm, self.mock_mono, self.mock_patcher, hotkey="F1")
        self.assertTrue(cheat.prepare())

        self.assertEqual(cheat.local_player_ptr_addr, 0x2210)
        self.assertEqual(cheat.vitals_offset, 0x20)
        self.assertEqual(cheat.local_hp_offset, 0x194)
        self.assertEqual(cheat.prev_hp_offset, 0x184)
        self.assertEqual(cheat.synced_hp_offset, 0x0F0)
        self.assertEqual(cheat.invuln_offset, 0x19C)
        self.assertEqual(cheat.local_is_dead_offset, 0x198)
        self.assertEqual(cheat.prev_fire_offset, 0x190)
        self.assertEqual(cheat.prev_poison_offset, 0x18C)
        self.assertEqual(cheat.on_health_change_native, 0x8000)

    def test_lock_health_enable_and_maintain(self):
        cheat = LockHealthCheat(self.mock_pm, self.mock_mono, self.mock_patcher, hotkey="F1")
        cheat.method_addrs = {"TakeDamage": 0x8000}
        cheat.local_player_ptr_addr = 0x2210
        cheat.vitals_offset = 0x20
        cheat.local_hp_offset = 0x194
        cheat.prev_hp_offset = 0x184
        cheat.synced_hp_offset = 0x0F0
        cheat.invuln_offset = 0x19C
        cheat.local_is_dead_offset = 0x198
        cheat.prev_fire_offset = 0x190
        cheat.prev_poison_offset = 0x18C
        cheat.on_health_change_native = 0x8500

        def mock_read_ulonglong(addr):
            if addr == 0x2210:
                return 0x5000  # LocalPlayer instance
            elif addr == 0x5020:
                return 0x6000  # PlayerVitals instance
            elif addr == 0x60F0:
                return 0x7000  # SyncVar<int> _syncedHealth instance
            return 0

        self.mock_pm.read_ulonglong.side_effect = mock_read_ulonglong

        self.assertTrue(cheat.enable())
        self.assertTrue(cheat.is_enabled)

        # Verify JIT patch
        self.mock_patcher.patch_ret.assert_called_with("TakeDamage", 0x8000)

        # Verify memory writes for Health = 100
        self.mock_pm.write_int.assert_any_call(0x6194, 100)  # _localHp
        self.mock_pm.write_int.assert_any_call(0x6184, 100)  # _prevHealth
        self.mock_pm.write_int.assert_any_call(0x706C, 100)  # SyncVar +0x6C
        self.mock_pm.write_int.assert_any_call(0x7070, 100)  # SyncVar +0x70
        self.mock_pm.write_float.assert_any_call(0x619C, 999999.0)  # _invulnerableUntil
        self.mock_pm.write_uchar.assert_any_call(0x6198, 0)  # _localIsDead
        self.mock_pm.write_int.assert_any_call(0x6190, 0)  # _prevFire
        self.mock_pm.write_int.assert_any_call(0x618C, 0)  # _prevPoison

        # Verify UI update call: OnHealthChange(vitals_inst, 100, 100, 0)
        self.mock_mono.executor.call.assert_called_with(0x8500, 0x6000, 100, 100, 0)

    def test_lock_health_disable(self):
        cheat = LockHealthCheat(self.mock_pm, self.mock_mono, self.mock_patcher, hotkey="F1")
        cheat.method_addrs = {"TakeDamage": 0x8000}
        cheat.local_player_ptr_addr = 0x2210
        cheat.vitals_offset = 0x20
        cheat.invuln_offset = 0x19C
        cheat.is_enabled = True

        self.mock_pm.read_ulonglong.side_effect = lambda addr: 0x5000 if addr == 0x2210 else 0x6000

        self.assertTrue(cheat.disable())
        self.assertFalse(cheat.is_enabled)
        self.mock_patcher.restore.assert_called_with("TakeDamage")
        self.mock_pm.write_float.assert_called_with(0x619C, 0.0)

    def test_lock_hunger_initialization(self):
        cheat = LockHungerCheat(self.mock_pm, self.mock_mono, self.mock_patcher, hotkey="F2")
        self.assertEqual(cheat.name, "Lock Hunger / Infinite Fullness")
        self.assertEqual(cheat.hotkey, "F2")
        self.assertIn("100", cheat.description)
        self.assertFalse(cheat.is_enabled)

    def test_lock_hunger_prepare(self):
        self.mock_mono.find_class.side_effect = lambda asm, cls: {
            "PlayerVitals": 0x1000,
            "Player": 0x2000,
        }.get(cls, 0)

        self.mock_mono.get_export.return_value = 0x5555
        self.mock_mono.executor.call.side_effect = [
            0x2100,  # vtable Player
            0x2200,  # static_data Player
        ]

        def mock_get_field_offset(cls, name):
            if cls == 0x2000:
                if name == "LocalPlayer":
                    return 0x10
                elif name == "_playerVitals":
                    return 0x20
            elif cls == 0x1000:
                if name == "_prevFullness":
                    return 0x188
                elif name == "_syncedFullness":
                    return 0x0F8
            return 0

        self.mock_mono.get_field_offset.side_effect = mock_get_field_offset
        self.mock_mono.find_method.return_value = 0x4000
        self.mock_mono.compile_method.return_value = 0x8000

        cheat = LockHungerCheat(self.mock_pm, self.mock_mono, self.mock_patcher, hotkey="F2")
        self.assertTrue(cheat.prepare())

        self.assertEqual(cheat.local_player_ptr_addr, 0x2210)
        self.assertEqual(cheat.vitals_offset, 0x20)
        self.assertEqual(cheat.prev_fullness_offset, 0x188)
        self.assertEqual(cheat.synced_fullness_offset, 0x0F8)
        self.assertEqual(cheat.on_fullness_change_native, 0x8000)

    def test_lock_hunger_enable_and_maintain(self):
        cheat = LockHungerCheat(self.mock_pm, self.mock_mono, self.mock_patcher, hotkey="F2")
        cheat.method_addrs = {"LowerFullness": 0x8000}
        cheat.local_player_ptr_addr = 0x2210
        cheat.vitals_offset = 0x20
        cheat.prev_fullness_offset = 0x188
        cheat.synced_fullness_offset = 0x0F8
        cheat.on_fullness_change_native = 0x8600

        def mock_read_ulonglong(addr):
            if addr == 0x2210:
                return 0x5000  # LocalPlayer instance
            elif addr == 0x5020:
                return 0x6000  # PlayerVitals instance
            elif addr == 0x60F8:
                return 0x7500  # SyncVar<int> _syncedFullness instance
            return 0

        self.mock_pm.read_ulonglong.side_effect = mock_read_ulonglong

        self.assertTrue(cheat.enable())
        self.assertTrue(cheat.is_enabled)

        # Verify JIT patch
        self.mock_patcher.patch_ret.assert_called_with("LowerFullness", 0x8000)

        # Verify memory writes for Fullness = 100
        self.mock_pm.write_int.assert_any_call(0x6188, 100)  # _prevFullness
        self.mock_pm.write_int.assert_any_call(0x756C, 100)  # SyncVar +0x6C
        self.mock_pm.write_int.assert_any_call(0x7570, 100)  # SyncVar +0x70

        # Verify UI update call: OnFullnessChange(vitals_inst, 100, 100, 0)
        self.mock_mono.executor.call.assert_called_with(0x8600, 0x6000, 100, 100, 0)

    def test_lock_health_update_dissipates_elemental_only(self):
        cheat = LockHealthCheat(self.mock_pm, self.mock_mono, self.mock_patcher, hotkey="F1")
        cheat.local_player_ptr_addr = 0x2210
        cheat.vitals_offset = 0x20
        cheat.local_hp_offset = 0x194
        cheat.prev_hp_offset = 0x184
        cheat.synced_hp_offset = 0x0F0
        cheat.prev_fire_offset = 0x190
        cheat.prev_poison_offset = 0x18C
        cheat.local_is_dead_offset = 0x198
        cheat.is_enabled = True

        self.mock_pm.read_ulonglong.side_effect = lambda addr: 0x5000 if addr == 0x2210 else 0x6000

        cheat.update()

        # Should dissipate elemental meters and clear death flag
        self.mock_pm.write_int.assert_called_with(0x618C, 0)  # _prevPoison
        self.mock_pm.write_uchar.assert_called_with(0x6198, 0)  # _localIsDead

        # Should NOT overwrite health fields in tick loop
        written_addrs = [call[0][0] for call in self.mock_pm.write_int.call_args_list]
        self.assertNotIn(0x6194, written_addrs)  # _localHp not overwritten in update
        self.assertNotIn(0x6184, written_addrs)  # _prevHealth not overwritten in update

    def test_lock_hunger_update_noop(self):
        cheat = LockHungerCheat(self.mock_pm, self.mock_mono, self.mock_patcher, hotkey="F2")
        cheat.is_enabled = True
        cheat.update()
        # No writes should occur during update
        self.mock_pm.write_int.assert_not_called()


if __name__ == "__main__":
    unittest.main()
