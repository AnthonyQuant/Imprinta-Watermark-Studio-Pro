"""
watermark_engine.py - Stage 5: Edge-Case & Error Hardening
Provides comprehensive error protection, multi-font fallback cascades,
transparent PNG alpha blending safety, and non-destructive file guards.
"""

from enum import Enum
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageStat, ImageOps, UnidentifiedImageError

# Increase Pillow image safety threshold for ultra-high-resolution photo processing
Image.MAX_IMAGE_PIXELS = 300_000_000


class AnchorPosition(Enum):
    TOP_LEFT = "top_left"
    TOP_CENTER = "top_center"
    TOP_RIGHT = "top_right"
    CENTER_LEFT = "center_left"
    CENTER = "center"
    CENTER_RIGHT = "center_right"
    BOTTOM_LEFT = "bottom_left"
    BOTTOM_CENTER = "bottom_center"
    BOTTOM_RIGHT = "bottom_right"


class WatermarkEngine:
    def __init__(self, image_path: str):
        """
        Loads base image with error catching and EXIF orientation normalization.
        """
        self.image_path = Path(image_path)
        if not self.image_path.exists():
            raise FileNotFoundError(f"Image not found at {self.image_path}")

        try:
            raw_image = Image.open(self.image_path)
            raw_image.verify()  # Verify file integrity

            # Reopen after verify() according to Pillow guidelines
            raw_image = Image.open(self.image_path)
        except UnidentifiedImageError:
            raise ValueError(f"File '{self.image_path.name}' is an unsupported or corrupted image format.")
        except Exception as e:
            raise ValueError(f"Could not read image file '{self.image_path.name}': {e}")

        # Extract EXIF stream for optional metadata preservation
        self.exif_data = raw_image.info.get("exif")

        # Normalize EXIF camera rotation
        normalized_image = ImageOps.exif_transpose(raw_image)
        self.base_image = normalized_image.convert("RGBA")
        self.width, self.height = self.base_image.size

        if self.width <= 0 or self.height <= 0:
            raise ValueError(f"Invalid image dimensions: {self.width}x{self.height}")

    def calculate_position(
        self,
        layer_size: tuple[int, int],
        anchor: AnchorPosition | str = AnchorPosition.BOTTOM_RIGHT,
        margin_x: int = 20,
        margin_y: int = 20
    ) -> tuple[int, int]:
        """Calculates top-left (X, Y) pixel coordinates for 9-grid anchor positions."""
        layer_w, layer_h = layer_size

        if isinstance(anchor, str):
            try:
                anchor = AnchorPosition(anchor.lower())
            except ValueError:
                anchor = AnchorPosition.BOTTOM_RIGHT

        if anchor in (AnchorPosition.TOP_LEFT, AnchorPosition.CENTER_LEFT, AnchorPosition.BOTTOM_LEFT):
            x = margin_x
        elif anchor in (AnchorPosition.TOP_CENTER, AnchorPosition.CENTER, AnchorPosition.BOTTOM_CENTER):
            x = (self.width - layer_w) // 2
        else:
            x = self.width - layer_w - margin_x

        if anchor in (AnchorPosition.TOP_LEFT, AnchorPosition.TOP_CENTER, AnchorPosition.TOP_RIGHT):
            y = margin_y
        elif anchor in (AnchorPosition.CENTER_LEFT, AnchorPosition.CENTER, AnchorPosition.CENTER_RIGHT):
            y = (self.height - layer_h) // 2
        else:
            y = self.height - layer_h - margin_y

        return (max(0, x), max(0, y))

    # ==========================================
    # FONT FALLBACK CASCADE (STAGE 5 HARDENING)
    # ==========================================
    def _get_font(self, font_path: str | None, font_size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
        """
        Attempts loading target font, falling back through system fonts to default font.
        """
        candidates = []
        if font_path:
            candidates.append(font_path)

        # Common system fallbacks across Windows, macOS, and Linux
        candidates.extend(["arial.ttf", "DejaVuSans.ttf", "Helvetica.ttf", "LiberationSans-Regular.ttf"])

        for path in candidates:
            p = Path(path)
            if p.exists() or not p.is_absolute():
                try:
                    return ImageFont.truetype(str(p), font_size)
                except OSError:
                    continue

        return ImageFont.load_default()

    # ==========================================
    # RENDERING & COMPOSITING METHODS
    # ==========================================
    def render_text_layer(
        self,
        text: str,
        font_path: str | None = None,
        font_size: int = 36,
        use_adaptive_sizing: bool = False,
        adaptive_ratio: float = 0.04,
        color: tuple[int, int, int] = (255, 255, 255),
        opacity: float = 0.8,
        rotation: float = 0.0,
        letter_spacing: int = 0,
        stroke_width: int = 0,
        stroke_color: tuple[int, int, int] = (0, 0, 0),
        shadow_offset: tuple[int, int] | None = None,
        shadow_color: tuple[int, int, int] = (0, 0, 0)
    ) -> Image.Image:
        """Renders transformed text layer with adaptive sizing, outlines, and drop shadows."""
        effective_font_size = max(10, int(self.height * adaptive_ratio)) if use_adaptive_sizing else font_size

        font = self._get_font(font_path, effective_font_size)
        alpha_val = int(max(0.0, min(1.0, opacity)) * 255)
        text_fill = (*color[:3], alpha_val)
        stroke_fill = (*stroke_color[:3], alpha_val)
        shadow_fill = (*shadow_color[:3], max(0, int(alpha_val * 0.6)))

        padding = 40 + (stroke_width * 2) + (abs(shadow_offset[0]) + abs(shadow_offset[1]) if shadow_offset else 0)

        if letter_spacing > 0 and len(text) > 1:
            char_widths = []
            max_char_h = 0
            for char in text:
                bbox = font.getbbox(char)
                w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
                char_widths.append(w)
                max_char_h = max(max_char_h, h)
            total_w = sum(char_widths) + letter_spacing * (len(text) - 1) + padding * 2
            total_h = max_char_h + padding * 2
        else:
            bbox = font.getbbox(text)
            total_w = (bbox[2] - bbox[0]) + padding * 2
            total_h = (bbox[3] - bbox[1]) + padding * 2

        temp_img = Image.new("RGBA", (max(1, total_w), max(1, total_h)), (0, 0, 0, 0))
        draw = ImageDraw.Draw(temp_img)

        # Drop Shadow
        if shadow_offset and (shadow_offset[0] != 0 or shadow_offset[1] != 0):
            sx, sy = shadow_offset
            if letter_spacing > 0 and len(text) > 1:
                x_cursor = padding + sx
                for char in text:
                    draw.text((x_cursor, padding + sy), char, fill=shadow_fill, font=font)
                    bbox = font.getbbox(char)
                    x_cursor += (bbox[2] - bbox[0]) + letter_spacing
            else:
                draw.text((padding + sx, padding + sy), text, fill=shadow_fill, font=font)

        # Main Text with Stroke
        if letter_spacing > 0 and len(text) > 1:
            x_cursor = padding
            for char in text:
                draw.text(
                    (x_cursor, padding), char, fill=text_fill, font=font,
                    stroke_width=stroke_width, stroke_fill=stroke_fill if stroke_width > 0 else None
                )
                bbox = font.getbbox(char)
                x_cursor += (bbox[2] - bbox[0]) + letter_spacing
        else:
            draw.text(
                (padding, padding), text, fill=text_fill, font=font,
                stroke_width=stroke_width, stroke_fill=stroke_fill if stroke_width > 0 else None
            )

        bbox_content = temp_img.getbbox()
        if bbox_content:
            temp_img = temp_img.crop(bbox_content)

        if rotation != 0.0:
            temp_img = temp_img.rotate(rotation, resample=Image.Resampling.BICUBIC, expand=True)

        return temp_img

    def render_logo_layer(
        self,
        logo_path: str,
        opacity: float = 0.8,
        scale_factor: float = 0.2,
        rotation: float = 0.0
    ) -> Image.Image:
        """
        Loads and blends transparent PNG logos without dark border artifacts.
        """
        p = Path(logo_path)
        if not p.exists():
            raise FileNotFoundError(f"Logo image not found at {logo_path}")

        try:
            logo = Image.open(p).convert("RGBA")
        except Exception as e:
            raise ValueError(f"Failed to open logo image: {e}")

        target_w = max(10, int(self.width * scale_factor))
        aspect = logo.height / logo.width
        target_h = max(10, int(target_w * aspect))
        logo = logo.resize((target_w, target_h), Image.Resampling.LANCZOS)

        # Transparent alpha blending protection
        r, g, b, alpha = logo.split()
        alpha = alpha.point(lambda val: int(val * max(0.0, min(1.0, opacity))))
        logo.putalpha(alpha)

        if rotation != 0.0:
            logo = logo.rotate(rotation, resample=Image.Resampling.BICUBIC, expand=True)

        return logo

    def render_tiled_layer(
        self,
        text: str,
        font_path: str | None = None,
        font_size: int = 28,
        color: tuple[int, int, int] = (255, 255, 255),
        opacity: float = 0.35,
        rotation: float = -30.0,
        spacing_x: int = 120,
        spacing_y: int = 120
    ) -> Image.Image:
        """Renders repeated semi-transparent diagonal watermark grid overlay."""
        tile_unit = self.render_text_layer(
            text=text,
            font_path=font_path,
            font_size=font_size,
            color=color,
            opacity=opacity,
            rotation=0.0
        )

        tile_w, tile_h = tile_unit.size
        step_x = max(10, tile_w + spacing_x)
        step_y = max(10, tile_h + spacing_y)

        diagonal = int(((self.width ** 2) + (self.height ** 2)) ** 0.5) * 2
        large_canvas = Image.new("RGBA", (diagonal, diagonal), (0, 0, 0, 0))

        for y in range(0, diagonal, step_y):
            x_offset = (step_x // 2) if (y // step_y) % 2 == 1 else 0
            for x in range(-step_x, diagonal, step_x):
                large_canvas.paste(tile_unit, (x + x_offset, y), mask=tile_unit)

        if rotation != 0.0:
            large_canvas = large_canvas.rotate(
                rotation,
                resample=Image.Resampling.BICUBIC,
                center=(diagonal // 2, diagonal // 2)
            )

        crop_left = (diagonal - self.width) // 2
        crop_top = (diagonal - self.height) // 2
        return large_canvas.crop(
            (crop_left, crop_top, crop_left + self.width, crop_top + self.height)
        )

    def composite_layer(
        self,
        layer: Image.Image,
        anchor: AnchorPosition | str = AnchorPosition.BOTTOM_RIGHT,
        margin_x: int = 20,
        margin_y: int = 20,
        custom_pos: tuple[int, int] | None = None
    ) -> Image.Image:
        """Composites watermark layer onto base image."""
        position = custom_pos if custom_pos is not None else self.calculate_position(
            layer.size, anchor=anchor, margin_x=margin_x, margin_y=margin_y
        )

        overlay = Image.new("RGBA", self.base_image.size, (0, 0, 0, 0))
        overlay.paste(layer, position, mask=layer)
        return Image.alpha_composite(self.base_image, overlay)

    def export_image(
        self,
        final_image: Image.Image,
        output_path: str | Path,
        export_format: str = "PNG",
        quality: int = 95,
        keep_exif: bool = False
    ) -> Path:
        """Exports composited image with format conversion and non-destructive overwrite protection."""
        out_p = Path(output_path)

        # Overwrite Safeguard: Never overwrite original source image
        if out_p.resolve() == self.image_path.resolve():
            out_p = out_p.with_name(f"{out_p.stem}_watermarked{out_p.suffix}")

        out_p.parent.mkdir(parents=True, exist_ok=True)
        fmt = export_format.upper()
        save_kwargs = {}

        if keep_exif and self.exif_data:
            save_kwargs["exif"] = self.exif_data

        if fmt in ("JPEG", "JPG"):
            fmt = "JPEG"
            bg = Image.new("RGB", final_image.size, (255, 255, 255))
            if final_image.mode in ("RGBA", "LA"):
                bg.paste(final_image, mask=final_image.split()[-1])
            else:
                bg.paste(final_image)
            export_img = bg
            save_kwargs["quality"] = max(10, min(100, quality))
            save_kwargs["optimize"] = True
        elif fmt == "WEBP":
            export_img = final_image
            save_kwargs["quality"] = max(10, min(100, quality))
        else:
            fmt = "PNG"
            export_img = final_image
            save_kwargs["optimize"] = True

        export_img.save(out_p, format=fmt, **save_kwargs)
        return out_p


if __name__ == "__main__":
    print("Stage 5: Edge-Case & Error Hardening module loaded successfully.")