"""MirrorTing report transport, source validation, and thermal receipt rendering.

The upstream owns the report. This module accepts only the real MirrorTing
``/api/sessions/{id}/report`` schema; it never fills a missing live result with
the frontend's demonstration copy. Kiosk visitor identity comes from our local
session and is passed separately to ``render_report``.
"""

from __future__ import annotations

import math
import os
from collections.abc import Mapping
from urllib.parse import urlsplit

import httpx
    """Prepare photo-only, native-dot black/white pixels before receipt assembly.

    Gamma is an exponent: values above 1 darken midtones. Keep true white/black
    endpoints, without clipping pale face detail or stretching each histogram.
    Operator tuning never changes the camera, text, QR, or printer heat settings.
    """
    try:
        gamma = float(os.getenv("KIOSK_PHOTO_GAMMA", "1.25"))
    except ValueError:
        gamma = 1.25
    if not math.isfinite(gamma) or not 1.0 <= gamma <= 1.8:
        gamma = 1.25

    photo = ImageOps.exif_transpose(photo).convert("L")
    # Reduce camera grain before downsampling; sharpen only at the final dot size
    # so edge detail survives without turning sensor noise into black flecks.
    photo = photo.filter(ImageFilter.MedianFilter(3))
    photo = ImageOps.contain(photo, size, method=Image.Resampling.LANCZOS)
    photo = photo.point([round(255 * (i / 255) ** gamma) for i in range(256)])
    photo = photo.filter(ImageFilter.UnsharpMask(radius=0.75, percent=125, threshold=3))
    # Dither once, at final size. Receipt assembly and USB bands retain these
    # exact binary pixels; never resample/dither the complete receipt afterward.
