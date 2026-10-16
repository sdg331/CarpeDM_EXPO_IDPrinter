"""Write a synthetic grayscale/old/new comparison PNG. Never accesses a printer.

Run from repo root: python -m scripts.preview_thermal_photo --output /tmp/photo-tones.png
No camera, real faces, user files, or network are used.
"""

import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps

from backend.reports import thermal_photo


def synthetic_target():
    image = Image.new("L", (1024, 768), 255)
    draw = ImageDraw.Draw(image)
    # Broad gray steps, including the old pipeline's clipped highlight values.
    levels = [0, 32, 64, 96, 128, 160, 192, 224, 240, 246, 250, 255]
    for i, level in enumerate(levels):
        x = i * image.width // len(levels)
        right = (i + 1) * image.width // len(levels)
        draw.rectangle((x, 0, right - 1, 190), fill=level)
    # Smooth tonal gradient and high-key shapes with fine internal detail.
    ramp = Image.linear_gradient("L").rotate(90).resize((1024, 180))
    image.paste(ramp, (0, 200))
    for i, level in enumerate([160, 200, 224, 240]):
        x = 16 + i * 256
        draw.rectangle((x, 400, x + 230, 740), fill=level)
        draw.ellipse((x + 28, 426, x + 202, 600), fill=min(level + 12, 252))
        for offset in range(0, 144, 12):
            draw.line((x + 35, 630 + offset // 2, x + 195, 630 + offset // 2), fill=level - 24, width=2)
    return image


def previous_photo(photo, size):
    """Frozen d20b859 baseline, for comparison only; not a production path."""
    photo = ImageOps.exif_transpose(photo).convert("L").filter(ImageFilter.MedianFilter(3))
    photo = ImageOps.contain(photo, size, method=Image.Resampling.LANCZOS)
    photo = ImageOps.autocontrast(photo, cutoff=0.5)
    photo = photo.point([round(255 * (i / 255) ** (1 / 1.12)) for i in range(256)])
    photo = ImageEnhance.Contrast(photo).enhance(1.08)
    photo = photo.filter(ImageFilter.UnsharpMask(radius=0.75, percent=125, threshold=3))
    photo = photo.point([255 if i >= 246 else 0 if i <= 5 else i for i in range(256)])
    return photo.convert("1", dither=Image.Dither.FLOYDSTEINBERG)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    source = synthetic_target()
    size = (512, 640)
    panels = [ImageOps.contain(source, size), previous_photo(source, size), thermal_photo(source, size)]
    canvas = Image.new("RGB", (1600, 472), "white")
    draw = ImageDraw.Draw(canvas)
    font = ImageFont.load_default(size=20)
    for i, (label, panel) in enumerate(zip(["Synthetic grayscale input", "Previous: brighter + clipped", "New: configured photo gamma"], panels)):
        x = 16 + i * 528
        draw.text((x, 12), label, fill="black", font=font)
        canvas.paste(panel, (x, 48))
    draw.text((16, 444), "Software pixels only. No real face; physical paper quality is unverified.", fill="black", font=font)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(args.output)
    print(args.output)


if __name__ == "__main__":
    main()
