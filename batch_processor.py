"""
batch_processor.py - Stage 5: Hardened Batch Queue Engine
Processes queue items independently, isolating errors on corrupted/unsupported files
and keeping the main batch execution active.
"""

from pathlib import Path
from typing import Callable, Any
from watermark_engine import WatermarkEngine, AnchorPosition


class BatchProcessor:
    def __init__(self, output_dir: str | Path):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def process_queue(
        self,
        image_paths: list[str | Path],
        config: dict[str, Any],
        progress_callback: Callable[[int, int, str, bool, str], None] | None = None
    ) -> dict[str, Any]:
        """Applies watermark config across batch queue with isolated exception handling."""
        total = len(image_paths)
        successful = 0
        failed = 0
        logs = []

        for index, img_p in enumerate(image_paths, start=1):
            path_obj = Path(img_p)
            try:
                # Stage 5 Hardening: Catch individual file open errors
                engine = WatermarkEngine(str(path_obj))

                # Render watermark based on requested mode (Tiled vs Single)
                if config.get("is_tiled", False):
                    layer = engine.render_tiled_layer(
                        text=config.get("text", "Watermark"),
                        font_size=config.get("font_size", 28),
                        opacity=config.get("opacity", 0.35),
                        rotation=config.get("rotation", -30.0)
                    )
                    full_result = engine.composite_layer(layer, custom_pos=(0, 0))
                elif config.get("watermark_type") == "Text":
                    layer = engine.render_text_layer(
                        text=config.get("text", "Watermark"),
                        font_size=config.get("font_size", 36),
                        opacity=config.get("opacity", 0.8),
                        rotation=config.get("rotation", 0.0)
                    )
                    full_result = engine.composite_layer(
                        layer,
                        anchor=config.get("anchor", AnchorPosition.BOTTOM_RIGHT.value),
                        margin_x=config.get("margin_x", 20),
                        margin_y=config.get("margin_y", 20),
                        custom_pos=config.get("custom_pos")
                    )
                else:
                    layer = engine.render_logo_layer(
                        logo_path=config.get("logo_path", ""),
                        opacity=config.get("opacity", 0.8),
                        scale_factor=config.get("scale_factor", 0.2),
                        rotation=config.get("rotation", 0.0)
                    )
                    full_result = engine.composite_layer(
                        layer,
                        anchor=config.get("anchor", AnchorPosition.BOTTOM_RIGHT.value),
                        margin_x=config.get("margin_x", 20),
                        margin_y=config.get("margin_y", 20),
                        custom_pos=config.get("custom_pos")
                    )

                fmt = config.get("export_fmt", "PNG").lower()
                ext = ".jpg" if fmt in ("jpeg", "jpg") else f".{fmt}"
                dest_file = self.output_dir / f"{path_obj.stem}_watermarked{ext}"

                saved_path = engine.export_image(
                    final_image=full_result,
                    output_path=dest_file,
                    export_format=config.get("export_fmt", "PNG"),
                    quality=config.get("quality", 95),
                    keep_exif=config.get("keep_exif", False)
                )

                successful += 1
                msg = f"Saved to {saved_path.name}"
                logs.append({"file": path_obj.name, "status": "Success", "message": msg})

                if progress_callback:
                    progress_callback(index, total, path_obj.name, True, msg)

            except Exception as e:
                failed += 1
                msg = str(e)
                logs.append({"file": path_obj.name, "status": "Failed", "message": msg})

                if progress_callback:
                    progress_callback(index, total, path_obj.name, False, msg)

        return {
            "total": total,
            "successful": successful,
            "failed": failed,
            "logs": logs
        }


if __name__ == "__main__":
    print("Stage 5: Batch Processor hardened module loaded successfully.")