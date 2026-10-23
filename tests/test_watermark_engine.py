"""
tests/test_watermark_engine.py - Unit tests for WatermarkEngine
"""

import unittest
from pathlib import Path
import tempfile
from PIL import Image

from watermark_engine import WatermarkEngine, AnchorPosition


class TestWatermarkEngine(unittest.TestCase):
    def setUp(self):
        """Creates a temporary test image before each test."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_img_path = Path(self.temp_dir.name) / "test_base.jpg"

        # Create a 800x600 RGB test image
        img = Image.new("RGB", (800, 600), color=(200, 200, 200))
        img.save(self.test_img_path, format="JPEG")

        self.engine = WatermarkEngine(str(self.test_img_path))

    def tearDown(self):
        """Cleans up temporary files after each test."""
        self.temp_dir.cleanup()

    def test_image_initialization(self):
        """Tests that base image is correctly converted to RGBA with valid dimensions."""
        self.assertEqual(self.engine.width, 800)
        self.assertEqual(self.engine.height, 600)
        self.assertEqual(self.engine.base_image.mode, "RGBA")

    def test_anchor_position_calculations(self):
        """Verifies top-left (X, Y) math across key 9-grid anchor positions."""
        layer_size = (100, 50)
        margin_x, margin_y = 20, 20

        # Top-Left: Should equal margins
        pos_tl = self.engine.calculate_position(layer_size, AnchorPosition.TOP_LEFT, margin_x, margin_y)
        self.assertEqual(pos_tl, (20, 20))

        # Center: Should center layer on canvas
        pos_center = self.engine.calculate_position(layer_size, AnchorPosition.CENTER, margin_x, margin_y)
        self.assertEqual(pos_center, ((800 - 100) // 2, (600 - 50) // 2))

        # Bottom-Right: Should pad from bottom-right boundary
        pos_br = self.engine.calculate_position(layer_size, AnchorPosition.BOTTOM_RIGHT, margin_x, margin_y)
        self.assertEqual(pos_br, (800 - 100 - 20, 600 - 50 - 20))

    def test_text_layer_rendering(self):
        """Tests rendering of text layers into valid RGBA images."""
        text_layer = self.engine.render_text_layer(
            text="Test Watermark",
            font_size=36,
            opacity=0.8,
            rotation=0.0
        )
        self.assertIsInstance(text_layer, Image.Image)
        self.assertEqual(text_layer.mode, "RGBA")
        self.assertGreater(text_layer.width, 0)
        self.assertGreater(text_layer.height, 0)

    def test_tiled_layer_rendering(self):
        """Tests that tiled mode generates an overlay matching the base image dimensions."""
        tiled_layer = self.engine.render_tiled_layer(
            text="PROOF ONLY",
            font_size=24,
            opacity=0.3,
            rotation=-30.0
        )
        self.assertEqual(tiled_layer.size, (800, 600))
        self.assertEqual(tiled_layer.mode, "RGBA")

    def test_export_image_png_and_jpeg(self):
        """Tests exporting composited images to PNG and JPEG formats."""
        text_layer = self.engine.render_text_layer(text="Export Test")
        composited = self.engine.composite_layer(text_layer)

        # PNG Export
        out_png = Path(self.temp_dir.name) / "output.png"
        saved_png = self.engine.export_image(composited, out_png, export_format="PNG")
        self.assertTrue(saved_png.exists())

        # JPEG Export (Flattening RGBA to RGB)
        out_jpg = Path(self.temp_dir.name) / "output.jpg"
        saved_jpg = self.engine.export_image(composited, out_jpg, export_format="JPEG", quality=90)
        self.assertTrue(saved_jpg.exists())


if __name__ == "__main__":
    unittest.main()