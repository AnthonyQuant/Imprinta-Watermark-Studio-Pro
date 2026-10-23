"""
tests/test_presets.py - Unit tests for PresetManager
"""

import unittest
from pathlib import Path
import tempfile

from presets import PresetManager


class TestPresetManager(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.json_path = Path(self.temp_dir.name) / "test_presets.json"
        self.manager = PresetManager(storage_path=self.json_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_default_presets_created(self):
        """Tests that default presets are created if JSON file does not exist."""
        presets = self.manager.list_presets()
        self.assertIn("Photography Signature", presets)
        self.assertIn("Business Branding", presets)

    def test_save_and_get_preset(self):
        """Tests saving a new custom preset and retrieving its values."""
        custom_config = {
            "watermark_type": "Text",
            "text": "Custom Test",
            "font_size": 50,
            "opacity": 0.9,
            "anchor": "center"
        }
        self.manager.save_preset("Custom Preset", custom_config)

        retrieved = self.manager.get_preset("Custom Preset")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved["text"], "Custom Test")
        self.assertEqual(retrieved["font_size"], 50)

    def test_delete_preset(self):
        """Tests deleting an existing preset."""
        self.manager.save_preset("To Delete", {"text": "Temp"})
        self.assertIn("To Delete", self.manager.list_presets())

        deleted = self.manager.delete_preset("To Delete")
        self.assertTrue(deleted)
        self.assertNotIn("To Delete", self.manager.list_presets())


if __name__ == "__main__":
    unittest.main()