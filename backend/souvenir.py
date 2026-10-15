"""One thermal photo and a public introduction QR; no analysis or photo hosting."""

from datetime import datetime
from urllib.parse import urlsplit

import cv2
from PIL import Image, ImageDraw

from backend.badge import _font
from backend.reports import KEEPSAKE_HEIGHT, REPORT_WIDTH, draw_keepsake, thermal_photo


def introduction_url(value: str) -> str:
    """Only the operator supplies this URL, never a visitor upload."""
    try:
        parsed = urlsplit(value)
        parsed.port
        valid = (
            parsed.scheme in {"http", "https"} and parsed.hostname
            and not parsed.username and not parsed.password
            and not any(char.isspace() or ord(char) < 32 or char == "\\" for char in value)
            and len(value.encode("utf-8")) <= 200
        )
    except ValueError:
        valid = False
    if not valid:
        raise ValueError("SOUVENIR_NOT_CONFIGURED")
    return value


def qr_image(url: str) -> Image.Image:
    params = cv2.QRCodeEncoder_Params()
    params.correction_level = cv2.QRCodeEncoder_CORRECT_LEVEL_Q
    matrix = cv2.QRCodeEncoder_create(params).encode(introduction_url(url))
    # Keep a white quiet zone and integer modules; never dither the QR itself.
    matrix = cv2.copyMakeBorder(matrix, 4, 4, 4, 4, cv2.BORDER_CONSTANT, value=255)
    scale = 304 // matrix.shape[0]
    if scale < 4:
        raise ValueError("SOUVENIR_NOT_CONFIGURED")
    return Image.fromarray(matrix).resize(
        (matrix.shape[1] * scale, matrix.shape[0] * scale), Image.Resampling.NEAREST
    ).convert("1")


def render_souvenir(photo: Image.Image, url: str) -> Image.Image:
    """Preserve the complete captured frame, including hair and clothing."""
    qr = qr_image(url)
    photo = thermal_photo(photo, (512, 640))
    photo_y = 152
    message_y = photo_y + photo.height + 36
    qr_y = message_y + KEEPSAKE_HEIGHT + 40
    image = Image.new("1", (REPORT_WIDTH, qr_y + qr.height + 74), 1)
    draw = ImageDraw.Draw(image)
    draw.rectangle((24, 16, 551, 126), outline=0, width=4)
    draw.text((40, 25), "MIRRORTING", font=_font(38), fill=0)
    draw.text((40, 76), "오늘, 여기의 나. / PHOTO MEMORY", font=_font(20), fill=0)
    x = (REPORT_WIDTH - photo.width) // 2
    image.paste(photo, (x, photo_y))
    draw.rectangle((x - 3, photo_y - 3, x + photo.width + 2, photo_y + photo.height + 2), outline=0, width=3)
    draw_keepsake(draw, message_y)
    draw.line((24, qr_y - 16, 552, qr_y - 16), fill=0, width=4)
    image.paste(qr, (24, qr_y))
    draw.text((346, qr_y + 50), "SCAN & MEET", font=_font(20), fill=0)
    draw.text((346, qr_y + 89), "MirrorTing", font=_font(24), fill=0)
    draw.text((346, qr_y + 124), "더 알아보기", font=_font(22), fill=0)
    draw.text((346, qr_y + 172), "사진 다운로드가", font=_font(18), fill=0)
    draw.text((346, qr_y + 198), "아닌 소개 QR", font=_font(18), fill=0)
    draw.line((24, image.height - 54, 552, image.height - 54), fill=0, width=4)
    draw.text((32, image.height - 43), datetime.now().strftime("%Y.%m.%d") + " / KEEP THIS MOMENT", font=_font(17), fill=0)
    return image
