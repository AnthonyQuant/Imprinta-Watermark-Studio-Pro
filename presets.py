"""
presets.py - Stage 1: Reusable Watermark Presets Manager
Manages loading, saving, listing, and deleting persistent watermark
configurations to and from a JSON storage file.
"""

import json
from pathlib import Path
from typing import Any


DEFAULT_PRESETS: dict[str, dict[str, Any]] = {
    "Photography Signature": {
        "watermark_type": "Text",
        "text": "© PhotoSignature",
        "font_size": 42,
        "opacity": 0.75,
        "rotation": 0.0,
        "anchor": "bottom_right",
        "margin_x": 30,
        "margin_y": 30,
        "export_fmt": "PNG",
        "quality": 95
    },
    "Business Branding": {
        "watermark_type": "Text",
        "text": "CONFIDENTIAL - PROOF ONLY",
        "font_size": 48,
        "opacity": 0.50,
        "rotation": -30.0,
        "anchor": "center",
        "margin_x": 0,
        "margin_y": 0,
        "export_fmt": "JPEG",
        "quality": 90
    },
    "Draft Overlay": {
        "watermark_type": "Text",
        "text": "DRAFT",
        "font_size": 72,
        "opacity": 0.35,
        "rotation": -45.0,
        "anchor": "center",
        "margin_x": 0,
        "margin_y": 0,
        "export_fmt": "WEBP",
        "quality": 85
    }
}


class PresetManager:
    def __init__(self, storage_path: str | Path = "presets.json"):
        """Initializes preset manager and creates default presets if missing."""
        self.storage_path = Path(storage_path)
        if not self.storage_path.exists():
            self._save_all(DEFAULT_PRESETS)

    def _load_all(self) -> dict[str, dict[str, Any]]:
        """Reads all presets from disk safely."""
        try:
            with open(self.storage_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return DEFAULT_PRESETS.copy()

    def _save_all(self, data: dict[str, dict[str, Any]]) -> None:
        """Writes preset data to the JSON file."""
        with open(self.storage_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

    def list_presets(self) -> list[str]:
        """Returns a list of all available preset names."""
        data = self._load_all()
        return list(data.keys())

    def get_preset(self, name: str) -> dict[str, Any] | None:
        """Retrieves a specific preset configuration by name."""
        data = self._load_all()
        return data.get(name)

    def save_preset(self, name: str, config: dict[str, Any]) -> None:
        """Saves or updates a preset configuration."""
        data = self._load_all()
        data[name] = config
        self._save_all(data)

    def delete_preset(self, name: str) -> bool:
        """Deletes a user-defined preset. Returns True if successfully deleted."""
        data = self._load_all()
        if name in data:
            del data[name]
            self._save_all(data)
            return True
        return False


if __name__ == "__main__":
    pm = PresetManager()
    print("Stage 1 Preset Manager initialized.")
    print("Available Presets:", pm.list_presets())