"""사원증 배지 렌더 — 감열 프린터용 576×808 흑백 1비트 이미지.

크기 근거 (80mm 감열지, 203dpi)
    인쇄 폭 72mm = 576도트 → 배지 전체 576×808px (72×101mm)
    프론트 화면의 카드(384×540)와 비율이 같아 화면에서 본 것과 같은 물건이 나온다.

1비트 규율 — 사진과 글자는 다르게 다룬다.
    초상은 make_print_assets.py 가 이미 Floyd-Steinberg 로 디더링한 1비트를 그대로 쓴다.
    글자·선은 디더링하면 지저분해지므로 검정 단색으로 그린 뒤 단순 임계값으로 굽는다.
    둘을 섞어 그린 캔버스를 마지막에 한 번에 threshold 하면 디더 픽셀은 이미 0/255 라
    보존되고, 안티앨리어싱된 글자 가장자리만 정리된다.

부서 구분은 색이 아니라 검은 띠 + 라벨이다 — 감열지에는 색이 없다.
"""

from __future__ import annotations

import os
from datetime import date
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
PRINT_DIR = ROOT / "assets" / "characters" / "print"

W, H = 576, 808          # 72×101mm @ 203dpi
MARGIN = 36

# 한글이 되는 폰트를 위에서부터 찾는다. (경로, ttc 인덱스)
# 파이에는 앞의 둘이 없다 — RUN.md 의 fonts-pretendard 설치 안내 참고.
FONT_CANDIDATES = [
    (str(Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts" / "malgun.ttf"), 0),  # Windows 개발 PC
    ("/System/Library/Fonts/AppleSDGothicNeo.ttc", 0),                     # 맥
    ("/System/Library/Fonts/Supplemental/AppleGothic.ttf", 0),             # 맥 예비
    ("/usr/share/fonts/truetype/pretendard/Pretendard-Regular.ttf", 0),   # 파이 (설치 시)
    ("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc", 1),        # 파이 noto-cjk
]


class BadgeError(Exception):
    """렌더에 필요한 자산(폰트·초상)이 없다."""


def _font_path() -> tuple[str, int]:
    for path, index in FONT_CANDIDATES:
        if Path(path).exists():
            return path, index
    raise BadgeError(
        "한글 폰트를 찾지 못했다. 파이라면: sudo apt install fonts-pretendard"
    )


def _font(size: int) -> ImageFont.FreeTypeFont:
    path, index = _font_path()
    return ImageFont.truetype(path, size, index=index)


def _portrait(char_id: str) -> Image.Image:
    """인쇄용 1비트 초상. 없으면 원본에서 만드는 대신 명확히 실패한다 —
    디더링 계수는 실기로 맞춘 값이라 여기서 즉석 변환하면 품질이 다른 배지가 나온다."""
    path = PRINT_DIR / f"{char_id}_print.png"
    if not path.exists():
        raise BadgeError(
            f"인쇄용 초상이 없다: {path.name}\n"
            "scripts/make_print_assets.py 를 먼저 실행할 것."
        )
    return Image.open(path).convert("L")


def _center(draw: ImageDraw.ImageDraw, text: str, y: int, font, fill=0,
            tracking: int = 0) -> None:
    """가로 중앙 정렬. tracking 은 자간(px) — STAFF ID 같은 라벨용."""
    if tracking:
        widths = [draw.textlength(ch, font=font) for ch in text]
        total = sum(widths) + tracking * (len(text) - 1)
        x = (W - total) / 2
        for ch, w in zip(text, widths):
            draw.text((x, y), ch, font=font, fill=fill)
            x += w + tracking
    else:
        w = draw.textlength(text, font=font)
        draw.text(((W - w) / 2, y), text, font=font, fill=fill)


def render_badge(name: str, dept: str, char_id: str, emp_no: str,
                 issued: str | None = None) -> Image.Image:
    """배지 한 장을 1비트로 렌더한다. 매칭 점수는 찍지 않는다 —
    종이에 남으면 맥락이 사라져 'AI가 매긴 유사도'로만 읽힌다(프론트와 같은 결정)."""
    issued = issued or date.today().strftime("%Y. %m. %d")

    canvas = Image.new("L", (W, H), 255)
    d = ImageDraw.Draw(canvas)

    # ── 상단 검은 띠 ──
    d.rectangle([0, 0, W, 108], fill=0)
    _center(d, "4-Fit MirrorTing", 22, _font(36), fill=255)
    _center(d, "STAFF ID", 72, _font(15), fill=255, tracking=10)

    # ── 초상 (288폭 인쇄 자산, 중앙) ──
    portrait = _portrait(char_id)
    px = (W - portrait.width) // 2
    py = 148
    canvas.paste(portrait, (px, py))
    d.rectangle([px - 1, py - 1, px + portrait.width, py + portrait.height],
                outline=0, width=1)

    # ── 이름 · 부서 ──
    # 이름은 최대 10자 — 58px 로는 8자부터 폭을 넘는다. 맞을 때까지 줄인다.
    y = py + portrait.height + 34
    name_font = _font(58)
    max_w = W - MARGIN * 2
    for size in (58, 50, 44, 38, 33):
        name_font = _font(size)
        if d.textlength(name, font=name_font) <= max_w:
            break
    _center(d, name, y, name_font)
    _center(d, f"{dept} · 사원", y + 78, _font(26))

    # ── 구분선 · 하단 정보 ──
    ry = y + 130
    d.line([MARGIN, ry, W - MARGIN, ry], fill=0, width=1)

    fy = ry + 22
    small, val = _font(15), _font(24)
    d.text((MARGIN, fy), "발급일", font=small, fill=0)
    d.text((MARGIN, fy + 24), issued, font=val, fill=0)
    w1 = d.textlength("사원번호", font=small)
    w2 = d.textlength(emp_no, font=val)
    d.text((W - MARGIN - w1, fy), "사원번호", font=small, fill=0)
    d.text((W - MARGIN - w2, fy + 24), emp_no, font=val, fill=0)

    # 글자 가장자리 정리 + 1비트 확정 (모듈 docstring 참고)
    return canvas.point(lambda p: 255 if p > 127 else 0).convert("1")
