"""Tests for TrainerUI dashboard rendering when connected and disconnected."""

import unittest
from unittest.mock import MagicMock, patch
from rich.panel import Panel
from rich.table import Table
from rich.console import Group
from howtofish_cheat.ui.console import TrainerUI
from howtofish_cheat.features import get_default_features
from howtofish_cheat.trainer import HowToFishTrainer


class TestTrainerUIDashboard(unittest.TestCase):
    """Test dashboard rendering and cheat table visibility in all connection states."""

    def setUp(self):
        self.ui = TrainerUI()

    def test_get_default_features(self):
        """Verify default feature catalog contains all 7 cheats."""
        features = get_default_features()
        self.assertEqual(len(features), 7)
        hotkeys = [f.hotkey for f in features]
        self.assertEqual(hotkeys, ["F1", "F2", "F3", "F4", "F5", "F6", "F8"])
        self.assertEqual(features[-1].select_hotkey, "F7")

    def test_dashboard_shows_cheats_when_disconnected_with_empty_features(self):
        """Verify cheats table is populated even when disconnected and features=[] is passed."""
        panel_zh = self.ui.generate_dashboard(
            is_attached=False,
            process_name="How to Fish.exe",
            pid=0,
            mono_domain=0,
            features=[],
            status_message="Waiting...",
            language="zh",
        )
        self.assertIsInstance(panel_zh, Panel)

        # Extract Table from Group renderable
        group = panel_zh.renderable
        self.assertIsInstance(group, Group)
        tables = [item for item in group.renderables if isinstance(item, Table)]
        self.assertEqual(len(tables), 1)
        table = tables[0]

        # Ensure all 7 cheat rows are present in the table
        self.assertEqual(len(table.rows), 7)

    def test_dashboard_shows_cheats_when_disconnected_with_none_features(self):
        """Verify cheats table is populated when features=None is passed."""
        panel_en = self.ui.generate_dashboard(
            is_attached=False,
            process_name="How to Fish.exe",
            pid=0,
            mono_domain=0,
            features=None,
            status_message="Waiting...",
            language="en",
        )
        self.assertIsInstance(panel_en, Panel)

        group = panel_en.renderable
        tables = [item for item in group.renderables if isinstance(item, Table)]
        self.assertEqual(len(tables), 1)
        table = tables[0]
        self.assertEqual(len(table.rows), 7)

    @patch("howtofish_cheat.trainer.keyboard")
    def test_trainer_features_populated_before_attachment(self, mock_keyboard):
        """Verify HowToFishTrainer initializes self.features with all available cheats before attaching."""
        trainer = HowToFishTrainer(language="zh")
        self.assertEqual(len(trainer.features), 7)
        self.assertFalse(trainer.features[0].is_enabled)

        # Cleanup should also reset to default features rather than leaving empty list
        trainer._cleanup_game_resources()
        self.assertEqual(len(trainer.features), 7)

    def test_selector_grid_uses_available_terminal_width_and_height(self):
        self.assertEqual(HowToFishTrainer._selector_grid_size(160, 40), (4, 120))
        self.assertEqual(HowToFishTrainer._selector_grid_size(100, 30), (3, 60))
        self.assertEqual(HowToFishTrainer._selector_grid_size(55, 20), (2, 20))
        self.assertEqual(HowToFishTrainer._selector_grid_size(20, 10), (1, 2))


if __name__ == "__main__":
    unittest.main()
