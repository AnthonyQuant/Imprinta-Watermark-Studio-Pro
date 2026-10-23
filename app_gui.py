"""
app_gui.py - Stage 6: Full UI Controls Integration
Integrates Preset Management (JSON saving/loading), Tiled Diagonal Mode toggles,
EXIF Metadata privacy controls, Adaptive Sizing options, and Batch Queue processing.
"""

from pathlib import Path
import threading
import tkinter as tk
from tkinter import filedialog, ttk, messagebox, simpledialog
from PIL import Image, ImageTk

from watermark_engine import WatermarkEngine, AnchorPosition
from batch_processor import BatchProcessor
from presets import PresetManager


class WatermarkGUI:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Imprinta Watermark Studio Pro - Full Suite")
        self.root.geometry("1250x900")
        self.root.configure(bg="#1E1E2E")

        # Engine & Managers
        self.preset_mgr = PresetManager()
        self.engine: WatermarkEngine | None = None
        self.current_preview_img: Image.Image | None = None
        self.tk_preview: ImageTk.PhotoImage | None = None

        # Drag-and-Drop Canvas Coordinates
        self.custom_pos: tuple[int, int] | None = None
        self.drag_start_mouse: tuple[int, int] | None = None
        self.drag_start_pos: tuple[int, int] | None = None
        self.display_scale: float = 1.0

        # Batch Queue State
        self.batch_files: list[Path] = []
        self.batch_output_dir = tk.StringVar(value=str(Path.home() / "Watermarked_Exports"))

        # Watermark Control Variables
        self.watermark_type = tk.StringVar(value="Text")
        self.text_val = tk.StringVar(value="© My Watermark")
        self.font_size_val = tk.IntVar(value=36)
        self.opacity_val = tk.DoubleVar(value=0.8)
        self.rotation_val = tk.DoubleVar(value=0.0)
        self.anchor_val = tk.StringVar(value=AnchorPosition.BOTTOM_RIGHT.value)
        self.margin_x_val = tk.IntVar(value=20)
        self.margin_y_val = tk.IntVar(value=20)
        self.logo_path = tk.StringVar(value="")
        self.scale_factor_val = tk.DoubleVar(value=0.2)

        # Stage 2, 3, & 4 Control Toggles
        self.use_adaptive_sizing = tk.BooleanVar(value=False)
        self.is_tiled_mode = tk.BooleanVar(value=False)
        self.keep_exif = tk.BooleanVar(value=False)

        # Stage 9 & 10 Smart Contrast Variables
        self.stroke_width_val = tk.IntVar(value=0)
        self.text_color_rgb: tuple[int, int, int] = (255, 255, 255)
        self.stroke_color_rgb: tuple[int, int, int] = (0, 0, 0)
        self.enable_auto_contrast = tk.BooleanVar(value=True)

        # Export Variables
        self.export_fmt = tk.StringVar(value="PNG")
        self.export_quality = tk.IntVar(value=95)

        # Preset Variable
        self.selected_preset = tk.StringVar(value="Select Preset...")

        # Status Message
        self.smart_status_msg = tk.StringVar(value="Open an image to start watermarking.")

        self._build_notebook_ui()
        self._bind_drag_events()

    def _build_notebook_ui(self):
        style = ttk.Style()
        style.theme_use("default")
        style.configure("TNotebook", background="#1E1E2E", borderwidth=0)
        style.configure("TNotebook.Tab", background="#181825", foreground="#CDD6F4", padding=[15, 8], font=("Arial", 10, "bold"))
        style.map("TNotebook.Tab", background=[("selected", "#313244")], foreground=[("selected", "#89B4FA")])

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)

        # Tab 1: Single Editor with Presets & Advanced Options
        self.tab_single = tk.Frame(self.notebook, bg="#1E1E2E")
        self.notebook.add(self.tab_single, text=" 🖼 Single Editor & Presets ")

        # Tab 2: Batch Processing Queue
        self.tab_batch = tk.Frame(self.notebook, bg="#1E1E2E")
        self.notebook.add(self.tab_batch, text=" 📂 Batch Queue ")

        self._build_single_editor_tab()
        self._build_batch_tab()

    # ==========================================
    # TAB 1: SINGLE EDITOR & CONTROLS
    # ==========================================
    def _build_single_editor_tab(self):
        main_frame = tk.Frame(self.tab_single, bg="#1E1E2E")
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # --- SCROLLABLE LEFT CONTAINER ---
        left_canvas = tk.Canvas(main_frame, bg="#181825", highlightthickness=0, width=320)
        left_scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=left_canvas.yview)

        left_container = tk.Frame(left_canvas, bg="#181825")
        left_container.bind(
            "<Configure>",
            lambda e: left_canvas.configure(scrollregion=left_canvas.bbox("all"))
        )

        left_canvas.create_window((0, 0), window=left_container, anchor="nw")
        left_canvas.configure(yscrollcommand=left_scrollbar.set)

        left_canvas.pack(side="left", fill="y", expand=False)
        left_scrollbar.pack(side="left", fill="y", padx=(0, 10))

        # Enable Mousewheel Scrolling on Left Panel
        left_canvas.bind_all("<MouseWheel>", lambda e: left_canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"))

        controls_frame = tk.LabelFrame(
            left_container, text=" Controls & Presets ", fg="#CDD6F4", bg="#181825", font=("Arial", 11, "bold"),
            padx=12, pady=10
        )
        controls_frame.pack(fill="both", expand=True)

        # 1. Image File Loader
        btn_load = tk.Button(
            controls_frame, text="📁 Open Base Image", font=("Arial", 10, "bold"),
            bg="#89B4FA", fg="#11111B", relief="flat", padx=10, pady=6, command=self._load_base_image
        )
        btn_load.pack(fill="x", pady=(0, 8))

        # 2. Stage 1: Presets Management Box
        preset_box = tk.LabelFrame(controls_frame, text=" ⚙️ Reusable Presets ", fg="#F9E2AF", bg="#181825",
                                   font=("Arial", 9, "bold"), padx=8, pady=6)
        preset_box.pack(fill="x", pady=(0, 8))

        self.preset_dropdown = ttk.OptionMenu(preset_box, self.selected_preset, self.selected_preset.get(),
                                              *self._get_preset_names(), command=self._apply_preset)
        self.preset_dropdown.pack(fill="x", pady=(0, 4))

        p_btn_bar = tk.Frame(preset_box, bg="#181825")
        p_btn_bar.pack(fill="x")

        tk.Button(p_btn_bar, text="💾 Save Current", font=("Arial", 8, "bold"), bg="#A6E3A1", fg="#11111B",
                  relief="flat", command=self._save_preset).pack(side="left", expand=True, fill="x", padx=(0, 2))
        tk.Button(p_btn_bar, text="🗑 Delete", font=("Arial", 8), bg="#F38BA8", fg="#11111B", relief="flat",
                  command=self._delete_preset).pack(side="right", expand=True, fill="x", padx=(2, 0))

        # 3. Smart Assistant Box
        smart_box = tk.LabelFrame(controls_frame, text=" ✨ Smart Placement ", fg="#A6E3A1", bg="#181825",
                                  font=("Arial", 9, "bold"), padx=8, pady=4)
        smart_box.pack(fill="x", pady=(0, 8))

        btn_smart = tk.Button(
            smart_box, text="⚡ Auto-Detect Quiet Spot", font=("Arial", 9, "bold"),
            bg="#A6E3A1", fg="#11111B", relief="flat", padx=8, pady=4, command=self._run_smart_placement
        )
        btn_smart.pack(fill="x", pady=2)

        # 4. Mode Options (Single / Tiled)
        mode_box = tk.Frame(controls_frame, bg="#181825")
        mode_box.pack(fill="x", pady=2)
        tk.Label(mode_box, text="Type:", fg="#A6ADC8", bg="#181825", font=("Arial", 9, "bold")).pack(side="left")
        ttk.Radiobutton(mode_box, text="Text", variable=self.watermark_type, value="Text",
                        command=self._on_setting_changed).pack(side="left", padx=5)
        ttk.Radiobutton(mode_box, text="Logo", variable=self.watermark_type, value="Logo",
                        command=self._on_setting_changed).pack(side="left")

        cb_tiled = ttk.Checkbutton(controls_frame, text="🔁 Tiled Diagonal Grid Mode", variable=self.is_tiled_mode,
                                   command=self._on_setting_changed)
        cb_tiled.pack(anchor="w", pady=2)

        cb_adaptive = ttk.Checkbutton(controls_frame, text="📐 Relative Adaptive Font Sizing",
                                      variable=self.use_adaptive_sizing, command=self._on_setting_changed)
        cb_adaptive.pack(anchor="w", pady=2)

        # 5. Text Controls
        self.text_group = tk.Frame(controls_frame, bg="#181825")
        self.text_group.pack(fill="x", pady=2)
        tk.Label(self.text_group, text="Text:", fg="#A6ADC8", bg="#181825", font=("Arial", 9)).pack(anchor="w")
        entry_text = tk.Entry(self.text_group, textvariable=self.text_val, font=("Arial", 10), bg="#313244",
                              fg="#CDD6F4", insertbackground="white")
        entry_text.pack(fill="x", pady=(2, 2))
        entry_text.bind("<KeyRelease>", lambda e: self._on_setting_changed())

        tk.Label(self.text_group, text="Font Size:", fg="#A6ADC8", bg="#181825", font=("Arial", 9)).pack(anchor="w")
        tk.Scale(self.text_group, from_=10, to=150, variable=self.font_size_val, orient="horizontal", bg="#181825",
                 fg="#CDD6F4", highlightthickness=0, command=lambda v: self._on_setting_changed()).pack(fill="x")

        # 6. Logo Controls
        self.logo_group = tk.Frame(controls_frame, bg="#181825")
        tk.Button(self.logo_group, text="🖼 Select Logo Image", font=("Arial", 9), bg="#45475A", fg="#CDD6F4",
                  relief="flat", command=self._load_logo_image).pack(fill="x", pady=2)
        tk.Label(self.logo_group, text="Logo Scale:", fg="#A6ADC8", bg="#181825", font=("Arial", 9)).pack(anchor="w")
        tk.Scale(self.logo_group, from_=0.05, to=0.8, resolution=0.05, variable=self.scale_factor_val,
                 orient="horizontal", bg="#181825", fg="#CDD6F4", highlightthickness=0,
                 command=lambda v: self._on_setting_changed()).pack(fill="x")

        # 7. Opacity, Rotation & Positioning
        tk.Label(controls_frame, text="Opacity:", fg="#A6ADC8", bg="#181825", font=("Arial", 9)).pack(anchor="w",
                                                                                                      pady=(2, 0))
        tk.Scale(controls_frame, from_=0.1, to=1.0, resolution=0.05, variable=self.opacity_val, orient="horizontal",
                 bg="#181825", fg="#CDD6F4", highlightthickness=0, command=lambda v: self._on_setting_changed()).pack(
            fill="x")

        tk.Label(controls_frame, text="Rotation (°):", fg="#A6ADC8", bg="#181825", font=("Arial", 9)).pack(anchor="w",
                                                                                                           pady=(2, 0))
        tk.Scale(controls_frame, from_=-180, to=180, variable=self.rotation_val, orient="horizontal", bg="#181825",
                 fg="#CDD6F4", highlightthickness=0, command=lambda v: self._on_setting_changed()).pack(fill="x")

        tk.Label(controls_frame, text="Anchor Position:", fg="#A6ADC8", bg="#181825", font=("Arial", 9)).pack(
            anchor="w", pady=(2, 0))
        anchors = [a.value for a in AnchorPosition]
        ttk.OptionMenu(controls_frame, self.anchor_val, self.anchor_val.get(), *anchors,
                       command=lambda v: self._on_anchor_changed()).pack(fill="x", pady=2)

        tk.Button(controls_frame, text="🎯 Reset Position", font=("Arial", 8), bg="#313244", fg="#A6ADC8", relief="flat",
                  command=self._reset_to_anchor).pack(fill="x", pady=(2, 6))

        # 8. Export Controls & Privacy Control
        export_box = tk.LabelFrame(controls_frame, text=" Export & Privacy ", fg="#A6ADC8", bg="#181825",
                                   font=("Arial", 9, "bold"), padx=8, pady=4)
        export_box.pack(fill="x", pady=(2, 0))

        fmt_frame = tk.Frame(export_box, bg="#181825")
        fmt_frame.pack(fill="x", pady=2)
        tk.Label(fmt_frame, text="Format:", fg="#A6ADC8", bg="#181825", font=("Arial", 9)).pack(side="left")
        ttk.OptionMenu(fmt_frame, self.export_fmt, self.export_fmt.get(), "PNG", "JPEG", "WEBP").pack(side="right")

        cb_exif = ttk.Checkbutton(export_box, text="🔒 Preserve Photo EXIF Metadata", variable=self.keep_exif)
        cb_exif.pack(anchor="w", pady=2)

        btn_export = tk.Button(
            controls_frame, text="💾 Export Single Image", font=("Arial", 10, "bold"),
            bg="#A6E3A1", fg="#11111B", relief="flat", padx=10, pady=6, command=self._export_current_image
        )
        btn_export.pack(fill="x", pady=(6, 0))

        # --- RIGHT PANEL: LIVE CANVAS & STATUS ---
        right_panel = tk.Frame(main_frame, bg="#1E1E2E")
        right_panel.pack(side="right", fill="both", expand=True)

        banner_frame = tk.Frame(right_panel, bg="#313244", padx=10, pady=6)
        banner_frame.pack(fill="x", pady=(0, 8))

        lbl_banner = tk.Label(
            banner_frame, textvariable=self.smart_status_msg, fg="#F9E2AF", bg="#313244", font=("Arial", 9, "bold"),
            anchor="w"
        )
        lbl_banner.pack(fill="x")

        preview_frame = tk.LabelFrame(right_panel, text=" Live Preview Canvas (Drag to Reposition) ", fg="#CDD6F4",
                                      bg="#181825", font=("Arial", 11, "bold"), padx=10, pady=10)
        preview_frame.pack(fill="both", expand=True)

        self.canvas = tk.Canvas(preview_frame, bg="#11111B", highlightthickness=0, cursor="fleur")
        self.canvas.pack(fill="both", expand=True)

    # ==========================================
    # PRESETS HELPERS (STAGE 1)
    # ==========================================
    def _get_preset_names(self) -> list[str]:
        names = self.preset_mgr.list_presets()
        return names if names else ["Default"]

    def _refresh_preset_dropdown(self):
        menu = self.preset_dropdown["menu"]
        menu.delete(0, "end")
        for name in self._get_preset_names():
            menu.add_command(label=name, command=lambda value=name: self._apply_preset(value))

    def _apply_preset(self, preset_name: str):
        config = self.preset_mgr.get_preset(preset_name)
        if not config:
            return

        self.selected_preset.set(preset_name)
        self.watermark_type.set(config.get("watermark_type", "Text"))
        self.text_val.set(config.get("text", "© My Watermark"))
        self.font_size_val.set(config.get("font_size", 36))
        self.opacity_val.set(config.get("opacity", 0.8))
        self.rotation_val.set(config.get("rotation", 0.0))
        self.anchor_val.set(config.get("anchor", "bottom_right"))
        self.margin_x_val.set(config.get("margin_x", 20))
        self.margin_y_val.set(config.get("margin_y", 20))
        self.export_fmt.set(config.get("export_fmt", "PNG"))
        self.export_quality.set(config.get("quality", 95))
        self.custom_pos = None

        self.smart_status_msg.set(f"Loaded Preset: '{preset_name}'")
        self.update_preview()

    def _save_preset(self):
        name = simpledialog.askstring("Save Preset", "Enter a name for this preset:")
        if name:
            config = self._get_current_watermark_config()
            self.preset_mgr.save_preset(name, config)
            self._refresh_preset_dropdown()
            self.selected_preset.set(name)
            messagebox.showinfo("Preset Saved", f"Preset '{name}' saved successfully.")

    def _delete_preset(self):
        name = self.selected_preset.get()
        if name and name in self.preset_mgr.list_presets():
            if messagebox.askyesno("Confirm Delete", f"Delete preset '{name}'?"):
                self.preset_mgr.delete_preset(name)
                self._refresh_preset_dropdown()
                self.selected_preset.set("Select Preset...")
                messagebox.showinfo("Preset Deleted", f"Preset '{name}' removed.")

    # ==========================================
    # SMART PLACEMENT (STAGE 8, 9, 10)
    # ==========================================
    def _run_smart_placement(self):
        if not self.engine:
            messagebox.showwarning("Smart Assistant", "Please load a base image first.")
            return

        layer = self._get_current_watermark_layer()
        if layer is None:
            return

        recommendation = self.engine.recommend_quiet_anchor(
            layer.size,
            margin_x=self.margin_x_val.get(),
            margin_y=self.margin_y_val.get()
        )

        best_anchor = recommendation["anchor"]
        entropy_val = recommendation["entropy"]
        lum_val = recommendation["luminance"]
        style_rec = recommendation["recommended_style"]

        self.anchor_val.set(best_anchor)
        self.custom_pos = None

        if self.enable_auto_contrast.get():
            self.text_color_rgb = style_rec["text_color"]
            self.stroke_color_rgb = style_rec["stroke_color"]
            self.stroke_width_val.set(style_rec["stroke_width"])

        bg_desc = "Dark background" if style_rec["is_dark_background"] else "Light background"
        self.smart_status_msg.set(
            f"✨ Anchor: '{best_anchor.upper()}' | Entropy: {entropy_val:.2f} | {bg_desc} (Luminance: {lum_val:.1f})"
        )

        self.update_preview()

    def _get_current_watermark_layer(self) -> Image.Image | None:
        if not self.engine:
            return None

        if self.is_tiled_mode.get():
            return self.engine.render_tiled_layer(
                text=self.text_val.get(),
                font_size=self.font_size_val.get(),
                opacity=self.opacity_val.get(),
                rotation=self.rotation_val.get()
            )
        elif self.watermark_type.get() == "Text":
            return self.engine.render_text_layer(
                text=self.text_val.get(),
                font_size=self.font_size_val.get(),
                use_adaptive_sizing=self.use_adaptive_sizing.get(),
                color=self.text_color_rgb if self.enable_auto_contrast.get() else (255, 255, 255),
                opacity=self.opacity_val.get(),
                rotation=self.rotation_val.get(),
                stroke_width=self.stroke_width_val.get() if self.enable_auto_contrast.get() else 0,
                stroke_color=self.stroke_color_rgb,
                shadow_offset=(2, 2) if self.enable_auto_contrast.get() else None
            )
        else:
            if not self.logo_path.get():
                return None
            try:
                return self.engine.render_logo_layer(
                    logo_path=self.logo_path.get(),
                    opacity=self.opacity_val.get(),
                    scale_factor=self.scale_factor_val.get(),
                    rotation=self.rotation_val.get()
                )
            except FileNotFoundError:
                return None

    # ==========================================
    # TAB 2: BATCH QUEUE
    # ==========================================
    def _build_batch_tab(self):
        main_frame = tk.Frame(self.tab_batch, bg="#1E1E2E")
        main_frame.pack(fill="both", expand=True, padx=15, pady=15)

        out_frame = tk.Frame(main_frame, bg="#181825", padx=10, pady=10)
        out_frame.pack(fill="x", pady=(0, 10))

        tk.Label(out_frame, text="Destination Folder:", fg="#CDD6F4", bg="#181825", font=("Arial", 10, "bold")).pack(side="left", padx=(0, 10))
        entry_out = tk.Entry(out_frame, textvariable=self.batch_output_dir, font=("Arial", 10), bg="#313244", fg="#CDD6F4", insertbackground="white")
        entry_out.pack(side="left", fill="x", expand=True, padx=(0, 10))

        btn_browse_out = tk.Button(
            out_frame, text="📁 Browse", font=("Arial", 9, "bold"), bg="#89B4FA", fg="#11111B", relief="flat", command=self._select_batch_output_dir
        )
        btn_browse_out.pack(side="right")

        btn_bar = tk.Frame(main_frame, bg="#1E1E2E")
        btn_bar.pack(fill="x", pady=(0, 10))

        tk.Button(btn_bar, text="➕ Add Images", font=("Arial", 10, "bold"), bg="#313244", fg="#CDD6F4", relief="flat", padx=12, pady=6, command=self._add_batch_files).pack(side="left", padx=(0, 8))
        tk.Button(btn_bar, text="🗑 Clear List", font=("Arial", 10), bg="#45475A", fg="#CDD6F4", relief="flat", padx=12, pady=6, command=self._clear_batch_files).pack(side="left", padx=(0, 8))

        self.btn_run_batch = tk.Button(
            btn_bar, text="⚡ Start Batch Processing", font=("Arial", 10, "bold"), bg="#A6E3A1", fg="#11111B", relief="flat", padx=15, pady=6, command=self._start_batch_thread
        )
        self.btn_run_batch.pack(side="right")

        tree_frame = tk.Frame(main_frame, bg="#181825")
        tree_frame.pack(fill="both", expand=True, pady=(0, 10))

        columns = ("filename", "status", "message")
        self.batch_tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=12)
        self.batch_tree.heading("filename", text="File Name")
        self.batch_tree.heading("status", text="Status")
        self.batch_tree.heading("message", text="Details")

        self.batch_tree.column("filename", width=250)
        self.batch_tree.column("status", width=100)
        self.batch_tree.column("message", width=450)

        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.batch_tree.yview)
        self.batch_tree.configure(yscrollcommand=scrollbar.set)

        self.batch_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        progress_box = tk.Frame(main_frame, bg="#181825", padx=10, pady=10)
        progress_box.pack(fill="x")

        self.progress_lbl = tk.Label(progress_box, text="Ready to process queue.", fg="#A6ADC8", bg="#181825", font=("Arial", 9))
        self.progress_lbl.pack(anchor="w", pady=(0, 5))

        self.progress_bar = ttk.Progressbar(progress_box, orient="horizontal", mode="determinate")
        self.progress_bar.pack(fill="x")

    def _select_batch_output_dir(self):
        folder = filedialog.askdirectory(title="Select Destination Directory")
        if folder:
            self.batch_output_dir.set(folder)

    def _add_batch_files(self):
        files = filedialog.askopenfilenames(
            title="Select Images for Batch Queue",
            filetypes=[("Image Files", "*.jpg *.jpeg *.png *.webp")]
        )
        if files:
            for f in files:
                p = Path(f)
                if p not in self.batch_files:
                    self.batch_files.append(p)
                    self.batch_tree.insert("", "end", values=(p.name, "Queued", "Waiting in queue..."))

    def _clear_batch_files(self):
        self.batch_files.clear()
        for item in self.batch_tree.get_children():
            self.batch_tree.delete(item)
        self.progress_lbl.config(text="Ready to process queue.")
        self.progress_bar["value"] = 0

    def _get_current_watermark_config(self):
        return {
            "watermark_type": self.watermark_type.get(),
            "text": self.text_val.get(),
            "font_size": self.font_size_val.get(),
            "opacity": self.opacity_val.get(),
            "rotation": self.rotation_val.get(),
            "logo_path": self.logo_path.get(),
            "scale_factor": self.scale_factor_val.get(),
            "anchor": self.anchor_val.get(),
            "margin_x": self.margin_x_val.get(),
            "margin_y": self.margin_y_val.get(),
            "custom_pos": self.custom_pos,
            "is_tiled": self.is_tiled_mode.get(),
            "keep_exif": self.keep_exif.get(),
            "export_fmt": self.export_fmt.get(),
            "quality": self.export_quality.get()
        }

    def _start_batch_thread(self):
        if not self.batch_files:
            messagebox.showwarning("Empty Queue", "Please add at least one image to the batch queue.")
            return

        self.btn_run_batch.config(state="disabled")
        config = self._get_current_watermark_config()
        output_dir = self.batch_output_dir.get()

        threading.Thread(target=self._run_batch_processing, args=(output_dir, config), daemon=True).start()

    def _run_batch_processing(self, output_dir: str, config: dict):
        processor = BatchProcessor(output_dir)

        def on_progress(current, total, filename, success, message):
            self.root.after(0, self._update_batch_ui, current, total, filename, success, message)

        summary = processor.process_queue(self.batch_files, config, progress_callback=on_progress)
        self.root.after(0, self._finish_batch_ui, summary)

    def _update_batch_ui(self, current, total, filename, success, message):
        pct = (current / total) * 100
        self.progress_bar["value"] = pct
        self.progress_lbl.config(text=f"Processing {current}/{total}: {filename}")

        for item in self.batch_tree.get_children():
            vals = self.batch_tree.item(item, "values")
            if vals[0] == filename:
                status = "Success" if success else "Failed"
                self.batch_tree.item(item, values=(filename, status, message))
                break

    def _finish_batch_ui(self, summary):
        self.btn_run_batch.config(state="normal")
        self.progress_lbl.config(
            text=f"Completed! Success: {summary['successful']} | Failures: {summary['failed']} | Total: {summary['total']}"
        )
        messagebox.showinfo("Batch Complete", f"Batch processing finished.\n\nSuccessful: {summary['successful']}\nFailed: {summary['failed']}")

    # ==========================================
    # EVENT HANDLERS & CANVAS PREVIEW
    # ==========================================
    def _bind_drag_events(self):
        self.canvas.bind("<ButtonPress-1>", self._on_drag_start)
        self.canvas.bind("<B1-Motion>", self._on_drag_motion)
        self.canvas.bind("<ButtonRelease-1>", self._on_drag_end)

    def _load_base_image(self):
        file_path = filedialog.askopenfilename(
            title="Select Base Image",
            filetypes=[("Image Files", "*.jpg *.jpeg *.png *.webp")]
        )
        if file_path:
            try:
                self.engine = WatermarkEngine(file_path)
                self.custom_pos = None
                self.smart_status_msg.set(f"Loaded: {self.engine.image_path.name} ({self.engine.width}x{self.engine.height}px)")
                self.update_preview()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load image: {e}")

    def _load_logo_image(self):
        file_path = filedialog.askopenfilename(
            title="Select Logo Image",
            filetypes=[("PNG/JPEG Images", "*.png *.jpg *.jpeg")]
        )
        if file_path:
            self.logo_path.set(file_path)
            self.watermark_type.set("Logo")
            self._on_setting_changed()

    def _on_setting_changed(self):
        self.update_preview()

    def _on_anchor_changed(self):
        self.custom_pos = None
        self.update_preview()

    def _reset_to_anchor(self):
        self.custom_pos = None
        self.update_preview()

    def _on_drag_start(self, event: tk.Event):
        if not self.engine:
            return
        self.drag_start_mouse = (event.x, event.y)
        self.drag_start_pos = self.current_active_pos if hasattr(self, 'current_active_pos') else (0, 0)

    def _on_drag_motion(self, event: tk.Event):
        if not self.engine or self.drag_start_mouse is None or self.drag_start_pos is None:
            return

        dx_canvas = event.x - self.drag_start_mouse[0]
        dy_canvas = event.y - self.drag_start_mouse[1]

        dx_image = int(dx_canvas * self.display_scale)
        dy_image = int(dy_canvas * self.display_scale)

        new_x = self.drag_start_pos[0] + dx_image
        new_y = self.drag_start_pos[1] + dy_image

        self.custom_pos = (new_x, new_y)
        self.update_preview()

    def _on_drag_end(self, event: tk.Event):
        self.drag_start_mouse = None
        self.drag_start_pos = None

    def update_preview(self):
        if not self.engine:
            return

        layer = self._get_current_watermark_layer()
        if layer is None:
            return

        if self.is_tiled_mode.get() or self.custom_pos is not None:
            active_pos = self.custom_pos if self.custom_pos is not None else (0, 0)
        else:
            active_pos = self.engine.calculate_position(
                layer.size,
                anchor=self.anchor_val.get(),
                margin_x=self.margin_x_val.get(),
                margin_y=self.margin_y_val.get()
            )
        self.current_active_pos = active_pos

        full_result = self.engine.composite_layer(layer, custom_pos=active_pos)
        self.current_preview_img = full_result

        canvas_w = max(100, self.canvas.winfo_width())
        canvas_h = max(100, self.canvas.winfo_height())

        scale_w = self.engine.width / canvas_w
        scale_h = self.engine.height / canvas_h
        self.display_scale = max(scale_w, scale_h)

        disp_w = max(1, int(self.engine.width / self.display_scale))
        disp_h = max(1, int(self.engine.height / self.display_scale))

        preview_copy = full_result.copy()
        preview_copy.thumbnail((disp_w, disp_h), Image.Resampling.LANCZOS)

        self.tk_preview = ImageTk.PhotoImage(preview_copy)
        self.canvas.delete("all")
        self.canvas.create_image(
            canvas_w // 2, canvas_h // 2, anchor="center", image=self.tk_preview
        )

    def _export_current_image(self):
        if not self.engine or self.current_preview_img is None:
            messagebox.showwarning("Export Warning", "Please open an image and create a watermark first.")
            return

        fmt = self.export_fmt.get().lower()
        ext = ".jpg" if fmt in ("jpeg", "jpg") else f".{fmt}"
        default_filename = f"{self.engine.image_path.stem}_watermarked{ext}"

        file_path = filedialog.asksaveasfilename(
            title="Export Watermarked Image",
            initialfile=default_filename,
            defaultextension=ext,
            filetypes=[("PNG Image", "*.png"), ("JPEG Image", "*.jpg *.jpeg"), ("WebP Image", "*.webp")]
        )

        if file_path:
            try:
                saved_path = self.engine.export_image(
                    self.current_preview_img,
                    output_path=file_path,
                    export_format=self.export_fmt.get(),
                    quality=self.export_quality.get(),
                    keep_exif=self.keep_exif.get()
                )
                messagebox.showinfo("Export Success", f"Image exported successfully to:\n{saved_path}")
            except Exception as e:
                messagebox.showerror("Export Error", f"Failed to export image: {e}")


if __name__ == "__main__":
    root = tk.Tk()
    app = WatermarkGUI(root)
    root.bind("<Configure>", lambda e: app.update_preview() if e.widget == root else None)
    root.mainloop()