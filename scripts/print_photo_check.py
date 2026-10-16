"""Render a native-width before/after sheet; print only with explicit --print."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from dotenv import load_dotenv
from PIL import Image, ImageDraw, ImageEnhance, ImageOps

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from backend.badge import _font
from backend.printing import PrintError, backend_name, print_badge
from backend.reports import REPORT_WIDTH, thermal_photo


def render_check(photo: Image.Image) -> Image.Image:
    before = ImageOps.contain(ImageOps.exif_transpose(photo).convert("L"), (512, 640))
    before = ImageEnhance.Brightness(ImageOps.autocontrast(before, cutoff=1)).enhance(1.08)
    before = before.convert("1", dither=Image.Dither.FLOYDSTEINBERG)
    after = thermal_photo(photo, (512, 640))
    assert before.size == after.size and before.mode == after.mode == "1"
    pictures = (("A / 기존 사진 처리", before), ("B / 대비·윤곽 보정", after))
    sheet = Image.new("1", (REPORT_WIDTH, 160 + sum(im.height + 72 for _, im in pictures)), 1)
    draw = ImageDraw.Draw(sheet)
    font = _font(24)
    draw.text((32, 12), "PHOTO QUALITY / TEST", font=font, fill=0)
    draw.rectangle((504, 12, 543, 43), fill=0)
    for index, dots in enumerate((1, 2, 4)):
        top = 64 + index * 24
        draw.text((32, top - 12), f"{dots} dot", font=font, fill=0)
        draw.line((152, top, 544, top), fill=0, width=dots)
    y = 144
    for label, picture in pictures:
        draw.text((32, y), label, font=font, fill=0)
        y += 40
        sheet.paste(picture, ((REPORT_WIDTH - picture.width) // 2, y))
        y += picture.height + 32
    assert sheet.width == 576 and sheet.mode == "1" and y < sheet.height
    return sheet


def main() -> None:
    load_dotenv(ROOT / ".env", override=False)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--photo", type=Path, default=ROOT / "assets/characters/char_05.png",
                        help="Local test image; defaults to a bundled sample character")
    parser.add_argument("--print", action="store_true", dest="send_to_printer",
                        help="Send one sheet to the configured ESC/POS USB printer")
    args = parser.parse_args()
    if args.send_to_printer and backend_name() != "escpos":
        parser.error("--print requires KIOSK_PRINT=escpos; screen is a preview and CUPS may rescale")
    with Image.open(args.photo) as photo:
        sheet = render_check(photo)
    output = ROOT / ".preview/print-quality.png"
    output.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output)
    print(f"576-dot 1-bit comparison: {output}")
    if args.send_to_printer:
        try:
            print_badge(sheet)
        except PrintError as exc:
            parser.exit(1, f"Print failed: {exc}\nCheck the actual paper before retrying.\n")
        print("Submitted once. Check the actual paper; completion is not confirmed.")


if __name__ == "__main__":
    main()
