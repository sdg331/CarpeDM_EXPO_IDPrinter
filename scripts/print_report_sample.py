"""Prepare a clearly labelled report example and optionally submit one copy."""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


def main() -> None:
    from dotenv import load_dotenv
    load_dotenv(ROOT / ".env")
    from PIL import Image, ImageDraw, ImageEnhance, ImageOps
    from backend.badge import _font
    from backend.printing import PrintError, print_badge
    from backend.reports import normalize_report, render_report, thermal_photo
    from backend.souvenir import render_souvenir

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--print", dest="submit", action="store_true")
    parser.add_argument("--output-dir", type=Path,
                        default=Path.home() / "idprinter-quality-20261013")
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    photo = Image.open(ROOT / "assets/characters/char_05.png").convert("RGB")
    from backend.rehearsal import example_report
    report = example_report()
    # Include the same photo processing used by real checkout receipts.
    image = render_report(report, name="김미래 (예시)", team="AI팀", photo=photo, photo_is_sample=True)
    image.save(args.output_dir / "sample-report.png")
    render_souvenir(photo).save(args.output_dir / "sample-photo-memory.png")
    old = ImageOps.contain(photo.convert("L"), (256, 384))
    old = ImageEnhance.Brightness(ImageOps.autocontrast(old, cutoff=1)).enhance(1.08).convert("1")
    improved = thermal_photo(photo, (256, 384))
    compare = Image.new("RGB", (576, max(old.height, improved.height) + 100), "white")
    draw = ImageDraw.Draw(compare)
    draw.text((24, 16), "기존 처리", font=_font(22), fill="black")
    draw.text((312, 16), "선명도 개선", font=_font(22), fill="black")
    compare.paste(old, (16, 60))
    compare.paste(improved, (304, 60))
    compare.save(args.output_dir / "photo-before-after.png")
    print(json.dumps({"prepared": str(args.output_dir), "width": image.width, "height": image.height}, ensure_ascii=False), flush=True)
    if not args.submit:
        return
    if os.getenv("KIOSK_PRINT") not in {"escpos", "cups"}:
        raise SystemExit("Physical printer backend is required; no data sent")
    record_path = args.output_dir / "sample-report-submission.json"
    record = {"status": "submitting", "copies": 1, "sample": True,
              "physicalCompletionConfirmed": False}
    # An exclusive record prevents an accidental second sample on rerun,
    # including when device delivery becomes uncertain.
    with record_path.open("x") as file:
        json.dump(record, file)
    try:
        result = print_badge(image)
        record.update(result)
    except PrintError as exc:
        record["status"] = "failed_before_submission" if exc.retryable else "unknown_outcome"
        record_path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n")
        raise SystemExit("Sample submission did not complete; inspect the printer before retrying") from exc
    record_path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(record, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
