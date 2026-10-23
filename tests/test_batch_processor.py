"""
tests/test_batch_processor.py - Unit tests for BatchProcessor
"""

import unittest
from pathlib import Path
import tempfile
from PIL import Image

from batch_processor import BatchProcessor


class TestBatchProcessor(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.input_dir = Path(self.temp_dir.name) / "input"
        self.output_dir = Path(self.temp_dir.name) / "output"

        self.input_dir.mkdir()
        self.output_dir.mkdir()

        # Create 2 valid test images
        self.valid_file_1 = self.input_dir / "valid1.png"
        self.valid_file_2 = self.input_dir / "valid2.jpg"

        Image.new("RGBA", (400, 400), "blue").save(self.valid_file_1)
        Image.new("RGB", (500, 500), "red").save(self.valid_file_2)

        # Create 1 corrupt/invalid image file
        self.corrupt_file = self.input_dir / "corrupt.jpg"
        with open(self.corrupt_file, "w") as f:
            f.write("Not an image file content.")

        self.processor = BatchProcessor(self.output_dir)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_batch_processing_success_and_error_isolation(self):
        """Verifies valid files are processed and corrupt files are isolated without crashing."""
        queue = [self.valid_file_1, self.corrupt_file, self.valid_file_2]

        config = {
            "watermark_type": "Text",
            "text": "Batch Test",
            "font_size": 30,
            "opacity": 0.8,
            "rotation": 0.0,
            "anchor": "bottom_right",
            "margin_x": 10,
            "margin_y": 10,
            "export_fmt": "PNG",
            "quality": 90
        }

        results = self.processor.process_queue(queue, config)

        self.assertEqual(results["total"], 3)
        self.assertEqual(results["successful"], 2)
        self.assertEqual(results["failed"], 1)

        # Verify exported output files exist
        exported_files = list(self.output_dir.glob("*_watermarked.png"))
        self.assertEqual(len(exported_files), 2)


if __name__ == "__main__":
    unittest.main()