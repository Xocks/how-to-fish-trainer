"""Unit tests for internationalization (i18n) and language switching functionality."""

import unittest
from unittest.mock import MagicMock, patch

from howtofish_cheat.i18n import TRANSLATIONS, tr
from howtofish_cheat.features.health import LockHealthCheat
from howtofish_cheat.features.hunger import LockHungerCheat
from howtofish_cheat.features.jump import InfiniteJumpCheat
from howtofish_cheat.features.ammo import UnlimitedAmmoCheat
from howtofish_cheat.features.damage import DamageMultiplierCheat
from howtofish_cheat.features.money import AddMoneyCheat
from howtofish_cheat.features.spawner import ItemSpawnerCheat
from howtofish_cheat.ui.console import TrainerUI
from howtofish_cheat.trainer import HowToFishTrainer


class TestI18nAndLanguageSwitch(unittest.TestCase):
    def setUp(self):
        self.mock_pm = MagicMock()
        self.mock_mono = MagicMock()
        self.mock_patcher = MagicMock()

    def test_tr_function(self):
        # Test Chinese translation
        zh_title = tr("header_title", "zh")
        self.assertIn("内存修改器", zh_title)

        # Test English translation
        en_title = tr("header_title", "en")
        self.assertIn("EXTERNAL MEMORY TRAINER", en_title)

        # Test parameterized translations
        zh_attached = tr("attached_info", "zh", process_name="Game.exe", pid=1234, mono_domain=0xABCD)
        self.assertIn("Game.exe", zh_attached)
        self.assertIn("1234", zh_attached)
        self.assertIn("0xABCD", zh_attached)
        self.assertIn("目标进程", zh_attached)

        en_attached = tr("attached_info", "en", process_name="Game.exe", pid=1234, mono_domain=0xABCD)
        self.assertIn("Process:", en_attached)
        self.assertIn("Game.exe", en_attached)

    def test_features_bilingual_names_and_descriptions(self):
        features = [
            LockHealthCheat(self.mock_pm, self.mock_mono, self.mock_patcher),
            LockHungerCheat(self.mock_pm, self.mock_mono, self.mock_patcher),
            InfiniteJumpCheat(self.mock_pm, self.mock_mono, self.mock_patcher),
            UnlimitedAmmoCheat(self.mock_pm, self.mock_mono, self.mock_patcher),
            DamageMultiplierCheat(self.mock_pm, self.mock_mono, self.mock_patcher),
            AddMoneyCheat(self.mock_pm, self.mock_mono, self.mock_patcher),
            ItemSpawnerCheat(self.mock_pm, self.mock_mono, self.mock_patcher),
        ]

        expected_zh_names = [
            "锁定生命 / 无敌",
            "锁定饱食度 / 无限饱腹",
            "无限多段跳 / 空中连跳",
            "无限弹药 / 免换弹",
            "伤害倍率调节",
            "增加金钱 (+1万)",
            "物品生成器",
        ]

        expected_en_names = [
            "Lock Health",
            "Lock Hunger / Infinite Fullness",
            "Infinite Air Jump",
            "Unlimited Ammo",
            "Damage Multiplier",
            "Add Money (+1w)",
            "Item Spawner",
        ]

        for f, zh_name, en_name in zip(features, expected_zh_names, expected_en_names):
            self.assertEqual(f.get_name("zh"), zh_name)
            self.assertEqual(f.get_name("en"), en_name)
            self.assertTrue(len(f.get_description("zh")) > 0)
            self.assertTrue(len(f.get_description("en")) > 0)

    def test_damage_multiplier_status_badge_bilingual(self):
        dmg_cheat = DamageMultiplierCheat(self.mock_pm, self.mock_mono, self.mock_patcher)

        # 0: 1x (Normal)
        dmg_cheat.current_mode_index = 0
        self.assertIn("已关闭", dmg_cheat.get_status_badge("zh"))
        self.assertIn("DISABLED", dmg_cheat.get_status_badge("en"))

        # 1: 2x
        dmg_cheat.current_mode_index = 1
        self.assertIn("已开启 (2x)", dmg_cheat.get_status_badge("zh"))
        self.assertIn("ACTIVE (2x)", dmg_cheat.get_status_badge("en"))

        # 4: One-shot
        dmg_cheat.current_mode_index = 4
        self.assertIn("一击秒杀", dmg_cheat.get_status_badge("zh"))
        self.assertIn("ONE-SHOT KILL", dmg_cheat.get_status_badge("en"))

    def test_add_money_status_badge_bilingual(self):
        money_cheat = AddMoneyCheat(self.mock_pm, self.mock_mono, self.mock_patcher)
        money_cheat.get_current_balance = MagicMock(return_value=0)

        self.assertIn("按键增加 +1万", money_cheat.get_status_badge("zh"))
        self.assertIn("PRESS TO +1w", money_cheat.get_status_badge("en"))

        money_cheat.get_current_balance = MagicMock(return_value=50000)
        self.assertIn("$50,000", money_cheat.get_status_badge("zh"))
        self.assertIn("$50,000", money_cheat.get_status_badge("en"))

    @patch("howtofish_cheat.trainer.keyboard")
    def test_trainer_toggle_language(self, mock_keyboard):
        trainer = HowToFishTrainer(language="zh")
        self.assertEqual(trainer.language, "zh")
        self.assertIn("正在启动", trainer.status_message)

        # Toggle to English
        trainer.toggle_language()
        self.assertEqual(trainer.language, "en")
        self.assertIn("English", trainer.status_message)

        # Toggle back to Chinese
        trainer.toggle_language()
        self.assertEqual(trainer.language, "zh")
        self.assertIn("中文", trainer.status_message)

    def test_ui_dashboard_rendering_both_languages(self):
        ui = TrainerUI()
        features = [
            LockHealthCheat(self.mock_pm, self.mock_mono, self.mock_patcher),
            DamageMultiplierCheat(self.mock_pm, self.mock_mono, self.mock_patcher),
        ]

        panel_zh = ui.generate_dashboard(
            is_attached=True,
            process_name="How to Fish.exe",
            pid=1234,
            mono_domain=0xABCD,
            features=features,
            status_message="测试状态",
            language="zh",
        )
        self.assertIsNotNone(panel_zh)

        panel_en = ui.generate_dashboard(
            is_attached=False,
            process_name="How to Fish.exe",
            pid=0,
            mono_domain=0,
            features=features,
            status_message="Test Status",
            language="en",
        )
    @patch("howtofish_cheat.trainer.keyboard")
    def test_trainer_hotkey_status_messages_bilingual(self, mock_keyboard):
        trainer = HowToFishTrainer(language="zh")
        trainer.pm = self.mock_pm
        trainer.mono = self.mock_mono

        # Test standard toggle (Lock Health) in Chinese
        health_cheat = LockHealthCheat(self.mock_pm, self.mock_mono, self.mock_patcher)
        trainer._on_hotkey_pressed(health_cheat)
        self.assertIn("锁定生命 / 无敌", trainer.status_message)
        self.assertIn("已开启", trainer.status_message)

        # Switch to English
        trainer.toggle_language()
        trainer._on_hotkey_pressed(health_cheat)
        self.assertIn("Lock Health", trainer.status_message)
        self.assertIn("DISABLED", trainer.status_message)

        # Test Damage Multiplier in Chinese
        trainer.toggle_language()
        dmg_cheat = DamageMultiplierCheat(self.mock_pm, self.mock_mono, self.mock_patcher)
        trainer._on_hotkey_pressed(dmg_cheat)
        self.assertIn("伤害倍率调节", trainer.status_message)
        self.assertIn("2x", trainer.status_message)

        # Test Add Money in Chinese
        money_cheat = AddMoneyCheat(self.mock_pm, self.mock_mono, self.mock_patcher)
        money_cheat.add_money = MagicMock(return_value=True)
        money_cheat.total_added = 10000
        trainer._on_hotkey_pressed(money_cheat)
        self.assertIn("成功增加 +$10,000 金币", trainer.status_message)


if __name__ == "__main__":
    unittest.main()
