# Imprinter Watermark Studio Pro 🎨📷

A production-grade, multi-threaded Python desktop application built to protect, brand, and batch-watermark digital photography with adaptive resolution scaling, smart quiet-spot detection, and privacy-aware EXIF metadata controls.

---

## 🌟 Key Features

* **✨ Smart Quiet-Spot Detection (Entropy & Luminance Analysis)**: Analyzes localized Shannon Entropy ($0.0 - 8.0$) across a 9-grid anchor canvas to identify visually quiet image regions and automatically recommends optimal text contrast styling (text fill, stroke width, drop shadow).
* **📐 Relative Adaptive Sizing Engine**: Dynamically calculates font point sizes and margins proportional to image dimensions (e.g., $4\%$ total height), ensuring watermarks maintain consistent visual presence across thumbnails, mobile photos, and ultra-high-resolution RAW photographs.
* **🔁 Tiled Diagonal Watermark Mode**: Generates repeated semi-transparent copyright grids diagonally across an expanded canvas to prevent unauthorized cropping or screenshot theft on proof photos.
* **🔒 Privacy-Aware EXIF Control & Auto-Orientation**: Automatically normalizes smartphone camera rotation tags (`ImageOps.exif_transpose`) and provides explicit user controls to either strip camera/GPS metadata or preserve original EXIF streams on export.
* **⚙️ Reusable JSON Presets Engine**: Persists user watermark configurations (*Photography Signature*, *Business Branding*, *Draft Overlay*) to a local `presets.json` store with instant load, save, and delete functionality.
* **⚡ Multi-Threaded Batch Processing Queue**: Processes entire image folders concurrently with isolated exception guards—skipping corrupt or unsupported files without halting queue execution.
* **🎯 Interactive Drag-and-Drop Canvas**: Supports manual watermark positioning directly on a live Tkinter canvas alongside 9-point grid anchor presets (`top_left`, `center`, `bottom_right`, etc.).

---

## 🏗 Modular Architecture

The codebase enforces strict separation of concerns, ensuring UI event loops remain decoupled from computational image processing and file operations:

```
ImprinterWatermarkStudio/
│
├── main.py               # Application entry point, workspace bootstrapper & Tkinter runner
├── app_gui.py            # Tkinter workspace UI, canvas event bindings & batch progress tree
├── watermark_engine.py   # Core Image Processing (Pillow, alpha compositing, entropy, EXIF, tiling)
├── batch_processor.py    # Multi-threaded batch queue execution engine with exception isolation
├── presets.py            # JSON storage manager for persistent user preset configurations
│
├── assets/               # Custom fonts (.ttf/.otf) and logo assets
├── examples/             # Portfolio showcase before/after watermarked images
├── exports/              # Default destination directory for processed batch outputs
│
└── tests/                # Automated unittest suite
    ├── test_watermark_engine.py
    ├── test_batch_processor.py
    └── test_presets.py
```

---

## 🛠 Tech Stack & Dependencies

* **Language**: Python 3.10+
* **GUI Framework**: Tkinter / `tkinter.ttk` (Native OS styling)
* **Image Processing**: `Pillow` (PIL) >= 10.2.0
* **Testing Framework**: Python `unittest` suite
* **Data Storage**: JSON (`presets.json`)

---

## 🚀 Quickstart & Installation

### 1. Clone the Repository
```bash
git clone https://github.com/AnthonyQuant/Imprinta-Watermark-Studio-Pro.git
cd Imprinter-Watermark-Studio-Pro
```

### 2. Create and Activate Virtual Environment
```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# Linux / macOS
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Required Dependencies
```bash
pip install -r requirements.txt
```

### 4. Launch Application
```bash
python main.py
```

---

## 📖 Step-by-Step Usage Guide

### Single Image Editor & Preset Management
1. Click **📁 Open Base Image** to load a photo onto the preview canvas.
2. Adjust watermark parameters:
   * **Type**: Switch between **Text** overlay or **Logo** image upload.
   * **Mode**: Toggle **🔁 Tiled Diagonal Grid Mode** for full proof protection or **📐 Relative Adaptive Font Sizing** for resolution independence.
   * **Sliders**: Finetune opacity, rotation, and font size.
3. Click **⚡ Auto-Detect Quiet Spot** to let the engine analyze luminance and position the watermark in the cleanest region.
4. Drag the watermark anywhere on the canvas to manually override positioning.
5. Save your design as a preset by clicking **💾 Save Current** under the **Reusable Presets** panel.
6. Click **💾 Export Single Image** to save the processed output.

### Multi-Threaded Batch Processing
1. Switch to the **📂 Batch Queue** tab.
2. Click **📁 Browse** to set your destination export folder.
3. Click **➕ Add Images** to load multiple photos into the queue list.
4. Click **⚡ Start Batch Processing**. The multi-threaded processor will apply your active Single Editor watermark configuration across all queued photos.

---

## 🧪 Running the Automated Test Suite

The project includes unit tests verifying core image operations, batch queue exception isolation, and preset persistence:

```bash
# Run all unit tests
python -m unittest discover tests

# Run specific test modules
python -m unittest tests/test_watermark_engine.py
python -m unittest tests/test_batch_processor.py
python -m unittest tests/test_presets.py
```

---

## 📜 License

Distributed under the MIT License.