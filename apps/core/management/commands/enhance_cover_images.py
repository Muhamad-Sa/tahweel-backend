"""
Clean up and re-frame the product/cover images so they look like real
catalogue cover art instead of raw crops off a PDF page (huge white
margins, stray page-number artifacts, inconsistent framing/resolution).

For each image:
  1. Detect the actual product content (trim near-uniform border/background).
  2. Re-crop with a small uniform padding around the content.
  3. Center it on a clean white canvas at a fixed aspect ratio (matching
     how the frontend actually displays it -- 4:3 for product photos,
     3:4 for document/catalogue covers).
  4. Upscale modestly if the source is low-resolution, then sharpen and
     lift contrast/color slightly (PDF-page renders come out flat/soft).

Originals are copied to a sibling *_originals/ folder the first time a
file is processed, so this is safe to re-run and easy to roll back.
"""
import shutil
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from PIL import Image, ImageChops, ImageEnhance, ImageFilter

TARGETS = [
    # (folder relative to MEDIA_ROOT, aspect_ratio width/height)
    ("products", 4 / 3),
    ("documents/covers", 3 / 4),
]

MIN_LONG_EDGE = 1100
PAD_FRACTION = 0.07
BG_COLOR = (255, 255, 255)


def trim_and_pad(img: Image.Image, ratio: float) -> Image.Image:
    img = img.convert("RGB")

    # Estimate the background color from the four corners (PDF-page crops
    # are white or light grey, not always pure #fff) and trim anything
    # close to it, isolating the actual product artwork.
    w, h = img.size
    corners = [img.getpixel((1, 1)), img.getpixel((w - 2, 1)),
               img.getpixel((1, h - 2)), img.getpixel((w - 2, h - 2))]
    bg = tuple(sum(c[i] for c in corners) // 4 for i in range(3))
    bg_layer = Image.new("RGB", img.size, bg)
    diff = ImageChops.difference(img, bg_layer)
    # Boost small differences so anti-aliased edges count, drop sensor noise.
    mask = diff.convert("L").point(lambda p: 255 if p > 18 else 0)
    # Morphological opening: erode away small stray marks (leftover page
    # numbers, crop registration ticks) that are only a few px wide, then
    # dilate back so the real product silhouette keeps its true size.
    opened = mask.filter(ImageFilter.MinFilter(9)).filter(ImageFilter.MaxFilter(9))
    bbox = opened.getbbox()

    if bbox:
        bw, bh = bbox[2] - bbox[0], bbox[3] - bbox[1]
        pad_x, pad_y = int(bw * PAD_FRACTION), int(bh * PAD_FRACTION)
        left = max(0, bbox[0] - pad_x)
        top = max(0, bbox[1] - pad_y)
        right = min(w, bbox[2] + pad_x)
        bottom = min(h, bbox[3] + pad_y)
        # Guard against a near-empty bbox (near-uniform image) collapsing the crop.
        if (right - left) > w * 0.05 and (bottom - top) > h * 0.05:
            img = img.crop((left, top, right, bottom))

    # Fit onto a clean canvas at the target aspect ratio, content centered.
    w, h = img.size
    if (w / h) > ratio:
        canvas_w, canvas_h = w, int(round(w / ratio))
    else:
        canvas_h, canvas_w = h, int(round(h * ratio))
    canvas = Image.new("RGB", (canvas_w, canvas_h), BG_COLOR)
    canvas.paste(img, ((canvas_w - w) // 2, (canvas_h - h) // 2))

    long_edge = max(canvas.size)
    if long_edge < MIN_LONG_EDGE:
        scale = MIN_LONG_EDGE / long_edge
        canvas = canvas.resize(
            (int(canvas.width * scale), int(canvas.height * scale)), Image.LANCZOS
        )

    canvas = canvas.filter(ImageFilter.UnsharpMask(radius=2, percent=65, threshold=3))
    canvas = ImageEnhance.Contrast(canvas).enhance(1.07)
    canvas = ImageEnhance.Color(canvas).enhance(1.06)
    canvas = ImageEnhance.Brightness(canvas).enhance(1.02)
    return canvas


class Command(BaseCommand):
    help = "Re-frame and enhance product/cover images (trim margins, fix aspect, sharpen)."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, **options):
        media_root = Path(settings.MEDIA_ROOT)
        dry_run = options["dry_run"]

        for rel_dir, ratio in TARGETS:
            folder = media_root / rel_dir
            if not folder.exists():
                continue
            backup_dir = media_root / f"{rel_dir}_originals".replace("/", "_")
            backup_dir.mkdir(parents=True, exist_ok=True)

            for path in sorted(folder.glob("*")):
                if not path.is_file() or path.suffix.lower() not in (".jpg", ".jpeg", ".png", ".webp"):
                    continue
                backup_path = backup_dir / path.name
                if not backup_path.exists():
                    shutil.copy2(path, backup_path)

                try:
                    with Image.open(backup_path) as src:
                        result = trim_and_pad(src, ratio)
                except Exception as exc:  # noqa: BLE001
                    self.stdout.write(self.style.ERROR(f"  failed: {path.name} ({exc})"))
                    continue

                if dry_run:
                    self.stdout.write(f"  would enhance: {rel_dir}/{path.name} -> {result.size}")
                    continue

                # Keep the original filename/extension so the DB's stored
                # file path (ImageField) keeps pointing at a valid file.
                fmt = "PNG" if path.suffix.lower() == ".png" else "JPEG"
                save_kwargs = {"optimize": True} if fmt == "PNG" else {"quality": 90, "optimize": True}
                result.save(path, fmt, **save_kwargs)
                self.stdout.write(f"  enhanced: {rel_dir}/{path.name} -> {result.size}")

        self.stdout.write(self.style.SUCCESS("Done."))
