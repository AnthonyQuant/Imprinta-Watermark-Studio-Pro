"""
main.py - Stage 8: Application Bootstrapper & Entry Point
Initializes required application directories, checks runtime environment,
and boots the Tkinter event loop.
"""

import sys
import tkinter as tk
from pathlib import Path

# Ensure project root is present in Python path
PROJECT_ROOT = Path(__file__).parent.resolve()
sys.path.insert(0, str(PROJECT_ROOT))

from app_gui import WatermarkGUI


def initialize_workspace() -> None:
    """Ensures required application folders exist before launching."""
    directories = [
        PROJECT_ROOT / "assets",
        PROJECT_ROOT / "examples",
        PROJECT_ROOT / "exports"
    ]
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)


def main() -> None:
    """Boots the GUI application event loop."""
    initialize_workspace()

    root = tk.Tk()

    # Configure root window properties
    root.title("Imprinta Watermark Studio Pro")
    root.minsize(1000, 700)

    # Initialize Application Interface
    app = WatermarkGUI(root)

    # Bind canvas resizing event handler
    root.bind("<Configure>", lambda event: app.update_preview() if event.widget == root else None)

    # Start Tkinter main loop
    root.mainloop()


if __name__ == "__main__":
    main()