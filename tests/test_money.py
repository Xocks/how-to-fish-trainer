"""Unit tests for AddMoneyCheat and trainer integration."""

import unittest
from unittest.mock import MagicMock
from howtofish_cheat.features.money import AddMoneyCheat
from howtofish_cheat.trainer import HowToFishTrainer
from howtofish_cheat.ui.console import TrainerUI


class TestAddMoney(unittest.TestCase):
    def setUp(self):
        self.mock_pm = MagicMock()
        self.mock_mono = MagicMock()
        self.mock_patcher = MagicMock()

    def test_feature_initialization(self):
        cheat = AddMoneyCheat(self.mock_pm, self.mock_mono, self.mock_patcher, hotkey="F6")
        self.assertEqual(cheat.name, "Add Money (+1w)")
        self.assertEqual(cheat.hotkey, "F6")
        self.assertEqual(cheat.add_amount, 10000)
        self.assertEqual(cheat.total_added, 0)
        self.assertFalse(cheat.is_enabled)
        self.assertIn("PRESS TO +1w", cheat.get_status_badge())

    def test_prepare_offsets_and_methods(self):
        self.mock_mono.find_class.side_effect = lambda asm, cls: {
            "MoneyManager": 0x1000,
            "Player": 0x2000,
            "PlayerUI": 0x3000,
        }.get(cls, 0)

        self.mock_mono.get_export.return_value = 0x5555
        self.mock_mono.executor.call.side_effect = [
            0x1100,  # vtable MoneyManager
            0x1200,  # static_data MoneyManager
            0x2100,  # vtable Player
            0x2200,  # static_data Player
        ]

        def mock_get_field_offset(cls, name):
            if cls == 0x1000:
                if name == "<Money>k__BackingField":
                    return 0x08
                elif name == "Instance":
                    return 0x00
                elif name == "_money":
                    return 0xE8
            elif cls == 0x2000:
                if name == "LocalPlayer":
                    return 0x10
            return 0

        self.mock_mono.get_field_offset.side_effect = mock_get_field_offset
        self.mock_mono.find_method.side_effect = lambda cls, name, pcount: 0x4000 if name == "SetMoney" else 0x4100
        self.mock_mono.compile_method.side_effect = lambda mptr: 0x8000 if mptr == 0x4000 else 0x8100

        cheat = AddMoneyCheat(self.mock_pm, self.mock_mono, self.mock_patcher, hotkey="F6")
        self.assertTrue(cheat.prepare())

        self.assertEqual(cheat.static_data_addr, 0x1200)
        self.assertEqual(cheat.money_offset, 0x08)
        self.assertEqual(cheat.instance_offset, 0x00)
        self.assertEqual(cheat.syncvar_offset, 0xE8)
        self.assertEqual(cheat.local_player_ptr_addr, 0x2210)
        self.assertEqual(cheat.set_money_native, 0x8000)
        self.assertEqual(cheat.money_sound_native, 0x8100)

    def test_add_money_execution_and_effects(self):
        cheat = AddMoneyCheat(self.mock_pm, self.mock_mono, self.mock_patcher, hotkey="F6")
        cheat.static_data_addr = 0x1200
        cheat.money_offset = 0x08
        cheat.instance_offset = 0x00
        cheat.syncvar_offset = 0xE8
        cheat.local_player_ptr_addr = 0x2210
        cheat.set_money_native = 0x8000
        cheat.money_sound_native = 0x8100

        # Mock memory reads:
        # static_data + money_offset (0x1208) -> 50000
        # static_data + instance_offset (0x1200) -> 0x5000 (MoneyManager instance)
        # 0x5000 + 0xE8 -> 0x6000 (SyncVar instance)
        # local_player_ptr_addr (0x2210) -> 0x7000 (LocalPlayer instance)
        def mock_read_int(addr):
            if addr == 0x1208:
                return 50000
            return 0

        def mock_read_ulonglong(addr):
            if addr == 0x1200:
                return 0x5000
            elif addr == 0x50E8:
                return 0x6000
            elif addr == 0x2210:
                return 0x7000
            return 0

        self.mock_pm.read_int.side_effect = mock_read_int
        self.mock_pm.read_ulonglong.side_effect = mock_read_ulonglong

        # Execute add money (+10,000)
        new_balance = cheat.add_money(10000)
        self.assertEqual(new_balance, 60000)
        self.assertEqual(cheat.total_added, 10000)
        self.assertTrue(cheat.is_enabled)
        self.assertIn("60,000", cheat.last_action_message)

        # Verify static field write
        self.mock_pm.write_int.assert_any_call(0x1208, 60000)

        # Verify SyncVar writes (offsets 0x6C and 0x70)
        self.mock_pm.write_int.assert_any_call(0x606C, 60000)
        self.mock_pm.write_int.assert_any_call(0x6070, 60000)

        # Verify PlayerUI.SetMoney call: (native_addr, new_balance, diff, gainedMoney)
        self.mock_mono.executor.call.assert_any_call(0x8000, 60000, 10000, 1)

        # Verify MoneySound call: (native_addr, inst_ptr, increase, lp_ptr)
        self.mock_mono.executor.call.assert_any_call(0x8100, 0x5000, 1, 0x7000)

        # Verify status badge
        self.assertIn("$50,000", cheat.get_status_badge())

    def test_add_money_clamping(self):
        cheat = AddMoneyCheat(self.mock_pm, self.mock_mono, self.mock_patcher, hotkey="F6")
        cheat.static_data_addr = 0x1200
        cheat.money_offset = 0x08
        cheat.instance_offset = None
        cheat.local_player_ptr_addr = None

        self.mock_pm.read_int.return_value = 1_999_995_000
        new_balance = cheat.add_money(10000)
        self.assertEqual(new_balance, 2_000_000_000)
        self.mock_pm.write_int.assert_called_with(0x1208, 2_000_000_000)

    def test_trainer_setup_and_ui(self):
        trainer = HowToFishTrainer()
        trainer.pm = self.mock_pm
        trainer.mono = self.mock_mono
        trainer.patcher = self.mock_patcher

        self.mock_mono.find_class.return_value = 0x12345
        self.mock_mono.find_method.return_value = 0x67890
        self.mock_mono.compile_method.return_value = 0xABCDE
        self.mock_mono.get_field_offset.return_value = 0x20
        self.mock_mono.get_export.return_value = 0x11111
        self.mock_mono.executor.call.return_value = 0x22222

        trainer._setup_features()
        self.assertEqual(len(trainer.features), 10)

        money_feature = [f for f in trainer.features if isinstance(f, AddMoneyCheat)][0]
        self.assertEqual(money_feature.hotkey, "F6")

        ui = TrainerUI()
        panel = ui.generate_dashboard(
            is_attached=True,
            process_name="How to Fish.exe",
            pid=45096,
            mono_domain=0x123456,
            features=trainer.features,
            status_message="Ready",
        )
        self.assertIsNotNone(panel)


if __name__ == "__main__":
    unittest.main()
