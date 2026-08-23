"""Test suite for UnlimitedAmmoCheat and trainer integration."""

import unittest
from unittest.mock import MagicMock
from howtofish_cheat.features.ammo import UnlimitedAmmoCheat
from howtofish_cheat.features.health import LockHealthCheat
from howtofish_cheat.features.hunger import LockHungerCheat
from howtofish_cheat.features.jump import InfiniteJumpCheat
from howtofish_cheat.trainer import HowToFishTrainer
from howtofish_cheat.ui.console import TrainerUI


class TestUnlimitedAmmo(unittest.TestCase):
    def setUp(self):
        self.mock_pm = MagicMock()
        self.mock_mono = MagicMock()
        self.mock_patcher = MagicMock()

    def test_feature_initialization(self):
        cheat = UnlimitedAmmoCheat(self.mock_pm, self.mock_mono, self.mock_patcher, hotkey="F4")
        self.assertEqual(cheat.name, "Unlimited Ammo")
        self.assertEqual(cheat.hotkey, "F4")
        self.assertFalse(cheat.is_enabled)

    def test_prepare_and_enable_disable(self):
        self.mock_mono.find_class.return_value = 0x12345
        self.mock_mono.find_method.return_value = 0x67890
        self.mock_mono.compile_method.return_value = 0xABCDE
        self.mock_mono.get_field_offset.return_value = 0x20
        self.mock_mono.get_export.return_value = 0x11111
        self.mock_mono.executor.call.return_value = 0x22222

        cheat = UnlimitedAmmoCheat(self.mock_pm, self.mock_mono, self.mock_patcher, hotkey="F4")
        prepared = cheat.prepare()
        self.assertTrue(prepared)
        self.assertIn("set_Ammo", cheat.method_addrs)

        # Test enable
        self.assertTrue(cheat.enable())
        self.assertTrue(cheat.is_enabled)
        self.mock_patcher.patch_ret.assert_called_with("set_Ammo", 0xABCDE)

        # Test disable
        self.assertTrue(cheat.disable())
        self.assertFalse(cheat.is_enabled)
        self.mock_patcher.restore.assert_called_with("set_Ammo")

    def test_trainer_features_setup(self):
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
        self.assertEqual(len(trainer.features), 6)
        feature_names = [f.name for f in trainer.features]
        self.assertIn("Lock Health", feature_names)
        self.assertIn("Lock Hunger / Infinite Fullness", feature_names)
        self.assertIn("Infinite Air Jump", feature_names)
        self.assertIn("Unlimited Ammo", feature_names)
        self.assertIn("Damage Multiplier", feature_names)
        self.assertIn("Add Money (+1w)", feature_names)

        # Verify UI render
        ui = TrainerUI()
        panel = ui.generate_dashboard(
            is_attached=True,
            process_name="How to Fish.exe",
            pid=1234,
            mono_domain=0x99999,
            features=trainer.features,
            status_message="Test Status",
        )
        self.assertIsNotNone(panel)


if __name__ == "__main__":
    unittest.main()
