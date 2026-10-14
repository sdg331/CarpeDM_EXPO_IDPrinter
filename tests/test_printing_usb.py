"""Offline encoder regression; no USB device access."""

import pytest
from PIL import Image


def test_escpos_encoder_preserves_preprocessed_photo_bits():
    # Optional hardware extra, but encoding itself needs no USB device.
    encoder = pytest.importorskip("escpos.image")
    from PIL import ImageOps
    from backend.reports import thermal_photo

    photo = thermal_photo(Image.linear_gradient("L"), (512, 640))
    receipt = Image.new("1", (576, photo.height + 180), 1)
    receipt.paste(photo, (32, 152))
    raw = b"".join(
        encoder.EscposImage(receipt.crop((0, top, 576, min(top + 128, receipt.height)))).to_raster_format()
        for top in range(0, receipt.height, 128)
    )
    # ESC/POS uses a set bit for black, inverse of Pillow's white-set bits.
    expected = ImageOps.invert(receipt.convert("L")).convert("1", dither=Image.Dither.NONE)
    assert len(raw) == 72 * receipt.height
    assert raw == expected.tobytes()
