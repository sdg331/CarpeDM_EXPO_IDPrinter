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
    pictures = (("A / 기존 밝기 보정", before), ("B / 최신 사진 보정", after))
