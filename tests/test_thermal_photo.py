"""Deterministic, synthetic-only checks for photo tones and native dot output."""

import pytest
from PIL import Image, ImageDraw

from backend.reports import thermal_photo


def black_fraction(image):
    return image.convert("L").histogram()[0] / (image.width * image.height)


@pytest.fixture(autouse=True)
def default_gamma(monkeypatch):
    monkeypatch.delenv("KIOSK_PHOTO_GAMMA", raising=False)


@pytest.mark.parametrize("level", [32, 64, 128, 192, 224, 246, 250])
def test_default_darkens_tones_without_erasing_highlights(level):
    source = Image.new("L", (192, 192), level)
    result = thermal_photo(source, source.size)
    assert result.mode == "1" and result.size == source.size
    # Floyd-Steinberg approximates target tone with binary printer dots.
    expected_black = 1 - (level / 255) ** 1.25
    assert abs(black_fraction(result) - expected_black) < 0.025
    if level <= 224:
        assert black_fraction(result) > 1 - level / 255
    if level >= 246:
        assert black_fraction(result) > 0  # previously clipped to paper white


@pytest.mark.parametrize("level,expected", [(0, 1), (255, 0)])
def test_true_black_and_white_stay_endpoints(level, expected):
    assert black_fraction(thermal_photo(Image.new("L", (64, 64), level), (64, 64))) == expected


def test_operator_tuning_is_monotonic_and_neutral_is_available(monkeypatch):
    source = Image.new("L", (192, 192), 160)
    densities = []
    for gamma in ["1.0", "1.25", "1.5", "1.8"]:
        monkeypatch.setenv("KIOSK_PHOTO_GAMMA", gamma)
        densities.append(black_fraction(thermal_photo(source, source.size)))
    assert densities == sorted(set(densities))
    assert abs(densities[0] - (1 - 160 / 255)) < 0.02


@pytest.mark.parametrize("value", ["", "oops", "nan", "inf", "-inf", "0.9", "1.81", "-1"])
def test_bad_operator_setting_uses_safe_default(monkeypatch, value):
    source = Image.linear_gradient("L").resize((192, 192))
    expected = thermal_photo(source, source.size)
    monkeypatch.setenv("KIOSK_PHOTO_GAMMA", value)
    assert thermal_photo(source, source.size).tobytes() == expected.tobytes()


def test_frame_aspect_orientation_and_input_are_preserved():
    source = Image.new("RGB", (800, 600), "white")
    draw = ImageDraw.Draw(source)
    draw.rectangle((0, 0, 799, 40), fill="black")
    draw.rectangle((0, 560, 799, 599), fill="black")
    before = source.tobytes()
    result = thermal_photo(source, (512, 640))
    assert result.size == (512, 384)
    assert result.getpixel((256, 8)) == 0 and result.getpixel((256, 376)) == 0
    assert source.tobytes() == before and source.mode == "RGB"
    assert thermal_photo(source, (512, 640)).tobytes() == result.tobytes()
    source.getexif()[274] = 6
    assert thermal_photo(source, (512, 640)).size == (480, 640)


def test_small_input_retains_existing_aspect_fit_behavior():
    assert thermal_photo(Image.new("RGB", (80, 60)), (512, 640)).size == (512, 384)


def test_souvenir_changes_only_photo_and_keeps_qr_decodable(monkeypatch):
    import cv2
    import numpy as np
    from PIL import ImageFont
    import backend.souvenir as souvenir

    monkeypatch.setattr(souvenir, "_font", lambda size: ImageFont.load_default(size=size))
    source = Image.new("RGB", (800, 600), (190, 180, 170))
    url = "https://example.org/mirrorting"
    monkeypatch.setenv("KIOSK_PHOTO_GAMMA", "1.0")
    neutral = souvenir.render_souvenir(source, url)
    monkeypatch.setenv("KIOSK_PHOTO_GAMMA", "1.25")
    darker = souvenir.render_souvenir(source, url)
    expected = thermal_photo(source, (512, 640))
    x, y = (576 - expected.width) // 2, 152
    box = (x, y, x + expected.width, y + expected.height)
    assert darker.crop(box).tobytes() == expected.tobytes()
    assert darker.crop(box).tobytes() != neutral.crop(box).tobytes()
    # Cover the changed region and compare every remaining bit, including QR.
    for receipt in [neutral, darker]:
        receipt.paste(1, box)
    assert neutral.tobytes() == darker.tobytes()
    qr = souvenir.qr_image(url)
    qr_y = 152 + expected.height + 32
    encoded = darker.crop((24, qr_y, 24 + qr.width, qr_y + qr.height))
    assert encoded.tobytes() == qr.tobytes()
    assert cv2.QRCodeDetector().detectAndDecode(np.array(encoded.convert("L")))[0] == url
