"""Verify USB endpoint routing without touching a physical printer."""

import sys
from types import ModuleType

import pytest
from PIL import Image

from backend.printing import PrintError, print_badge


@pytest.mark.parametrize("configured,expected_out", [(False, 0x01), (True, 0x02)])
@pytest.mark.parametrize("image_fails", [False, True])
def test_usb_endpoint_and_cleanup(monkeypatch, configured, expected_out, image_fails):
    calls = []

    class FakeUsb:
        def __init__(self, vendor, product, **kwargs):
            calls.append((vendor, product, kwargs))

        def image(self, image, **kwargs):
            calls.append("image")
            assert kwargs == {"impl": "bitImageRaster", "fragment_height": 128,
                              "high_density_vertical": True, "high_density_horizontal": True}
            if image_fails:
                raise OSError("USB write failed")

        def cut(self, **kwargs):
            calls.append("cut")

        def close(self):
            calls.append("close")

    package = ModuleType("escpos")
    module = ModuleType("escpos.printer")
    module.Usb = FakeUsb
    monkeypatch.setitem(sys.modules, "escpos", package)
    monkeypatch.setitem(sys.modules, "escpos.printer", module)
    monkeypatch.setenv("KIOSK_PRINT", "escpos")
    monkeypatch.setenv("KIOSK_ESCPOS_VENDOR", "0x0fe6")
    monkeypatch.setenv("KIOSK_ESCPOS_PRODUCT", "0x811e")
    monkeypatch.delenv("KIOSK_ESCPOS_IN_EP", raising=False)
    monkeypatch.delenv("KIOSK_ESCPOS_OUT_EP", raising=False)
    if configured:
        monkeypatch.setenv("KIOSK_ESCPOS_OUT_EP", "0x02")

    image = Image.new("1", (8, 8))
    if image_fails:
        with pytest.raises(PrintError) as failure:
            print_badge(image)
        assert failure.value.retryable is False
        assert calls[1:] == ["image", "close"]
    else:
        result = print_badge(image)
        assert result["status"] == "submitted"
        assert result["completionConfirmed"] is False
        assert calls[1:] == ["image", "cut", "close"]
    assert calls[0] == (0x0FE6, 0x811E,
                        {"in_ep": 0x82, "out_ep": expected_out, "timeout": 15000})


def test_photo_raster_bands_keep_all_rows_and_cut_only_once(monkeypatch):
    package, module = ModuleType("escpos"), ModuleType("escpos.printer")
    bands, commands = [], []

    class FakeUsb:
        def __init__(self, *args, **kwargs):
            pass

        def image(self, image, **kwargs):
            bands.append(image.copy())
            assert image.height <= 128 and image.width == 576

        def cut(self, **kwargs):
            commands.append("cut")

        def close(self):
            commands.append("close")

    module.Usb = FakeUsb
    monkeypatch.setitem(sys.modules, "escpos", package)
    monkeypatch.setitem(sys.modules, "escpos.printer", module)
    monkeypatch.setenv("KIOSK_PRINT", "escpos")
    monkeypatch.setenv("KIOSK_ESCPOS_VENDOR", "0x0fe6")
    monkeypatch.setenv("KIOSK_ESCPOS_PRODUCT", "0x811e")
    monkeypatch.setattr("backend.printing.time.sleep", lambda _: None)
    source = Image.new("1", (576, 1001), 1)
    for y in range(source.height):
        source.putpixel((y % source.width, y), 0)
    print_badge(source)
    restored = Image.new("1", source.size)
    y = 0
    for band in bands:
        restored.paste(band, (0, y))
        y += band.height
    assert y == source.height and restored.tobytes() == source.tobytes()
    assert commands == ["cut", "close"]
