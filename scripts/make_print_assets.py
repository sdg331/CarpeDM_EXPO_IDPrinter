#!/usr/bin/env python3
"""캐릭터 8종의 감열 프린터용 흑백 1비트 버전을 만든다.

감열식은 흑백 1비트라 실사 사진을 그대로 보내면 뭉개진다. 그레이스케일 →
대비/감마 보정 → 최종 크기로 리사이즈 → Floyd-Steinberg 디더링 순서로 굽는다.

**순서가 중요하다.** 디더링은 반드시 마지막, 최종 출력 크기에서 해야 한다.
1비트로 만든 뒤에 리사이즈하면 디더 패턴이 뭉개져서 회색이 사라진다.

크기 근거 (80mm 감열지)
    인쇄 폭 72mm × 203dpi = 576도트  → 배지 전체 576 × 808px (72 × 101mm)
    배지 안 초상 비율은 목업 기준 카드 폭의 48.4% → 279 × 372px
    기본값 288 × 384는 여기에 여유를 준 값이고 576의 정확히 절반이라 배치가 깔끔하다.

대비·감마 계수는 화면에서 좋아 보이는 값과 감열지에서 잘 나오는 값이 다르다.
--sweep 으로 계수별 비교 시트를 뽑아 실제로 한 장 출력해보고 고른다.

사용법
    python scripts/make_print_assets.py                    # 기본값으로 8장 생성
    python scripts/make_print_assets.py --sweep            # 계수 비교 시트 생성
    python scripts/make_print_assets.py --contrast 2.1     # 계수 확정 후 재생성
"""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageEnhance, ImageFilter, ImageOps

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "assets" / "characters"
OUT = SRC / "print"

# 감열 프린터는 도트가 번져서 실제 출력이 화면보다 어둡게 나온다.
# 1.0보다 큰 감마로 중간톤을 밝혀 이를 상쇄한다.
DEFAULTS = dict(width=288, contrast=1.8, gamma=1.15, sharpen=True)

SWEEP_CONTRAST = [1.2, 1.5, 1.8, 2.1, 2.4]


def prepare_gray(path: Path, width: int, contrast: float, gamma: float,
                 sharpen: bool) -> Image.Image:
    """1비트로 굽기 직전 상태(최종 크기의 8비트 그레이스케일)까지 만든다."""
    img = Image.open(path).convert("L")

    # 원본이 3:4(1086×1448)라 비율 그대로 줄이면 잘라낼 필요가 없다.
    height = round(width * img.height / img.width)
    img = img.resize((width, height), Image.LANCZOS)

    # 스튜디오 조명이라 히스토그램이 중앙에 몰려 있다. 양 끝 1%를 잘라 폭을 넓힌다.
    img = ImageOps.autocontrast(img, cutoff=1)

    if gamma != 1.0:
        inv = 1.0 / gamma
        img = img.point([round(255 * ((i / 255) ** inv)) for i in range(256)])

    img = ImageEnhance.Contrast(img).enhance(contrast)

    # 디더링은 잔털·눈매 같은 얇은 경계를 잡아먹는다. 살짝 세워두면 살아남는다.
    if sharpen:
        img = img.filter(ImageFilter.UnsharpMask(radius=1.2, percent=90, threshold=3))

    return img


def bake(path: Path, **kw) -> Image.Image:
    """최종 1비트 이미지. Pillow의 convert('1')이 기본으로 Floyd-Steinberg를 쓴다."""
    return prepare_gray(path, **kw).convert("1")


def run_build(args: argparse.Namespace) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    sources = sorted(SRC.glob("char_*.png"))
    if not sources:
        raise SystemExit(f"원본을 찾을 수 없다: {SRC}/char_*.png")

    for src in sources:
        img = bake(src, width=args.width, contrast=args.contrast,
                   gamma=args.gamma, sharpen=not args.no_sharpen)
        dst = OUT / f"{src.stem}_print.png"
        img.save(dst)
        print(f"{dst.relative_to(ROOT)}  {img.size[0]}×{img.size[1]}  mode={img.mode}")

    print(f"\n{len(sources)}장 생성. 계수: contrast={args.contrast} gamma={args.gamma}")
    print("실제 감열지로 한 장 뽑아본 뒤 --sweep 결과와 비교해 확정할 것.")


def run_sweep(args: argparse.Namespace) -> None:
    """대비 계수별 비교 시트. 감열지 폭(576도트)에 맞춰 한 장으로 뽑는다."""
    sweep_dir = OUT / "sweep"
    sweep_dir.mkdir(parents=True, exist_ok=True)

    sources = sorted(SRC.glob("char_*.png"))
    if not sources:
        raise SystemExit(f"원본을 찾을 수 없다: {SRC}/char_*.png")

    # 한 행 = 캐릭터 하나, 한 열 = 대비 계수 하나
    cell_w = 576 // len(SWEEP_CONTRAST)
    cell_h = round(cell_w * 4 / 3)
    label_h = 16

    sheet = Image.new("L", (cell_w * len(SWEEP_CONTRAST),
                            label_h + cell_h * len(sources)), 255)

    for col, contrast in enumerate(SWEEP_CONTRAST):
        for row, src in enumerate(sources):
            cell = prepare_gray(src, width=cell_w, contrast=contrast,
                                gamma=args.gamma, sharpen=not args.no_sharpen)
            cell = cell.resize((cell_w, cell_h), Image.LANCZOS)
            sheet.paste(cell, (col * cell_w, label_h + row * cell_h))

    # 열 머리글은 디더링 전에 그려 넣어야 같이 1비트로 구워진다.
    from PIL import ImageDraw

    draw = ImageDraw.Draw(sheet)
    for col, contrast in enumerate(SWEEP_CONTRAST):
        draw.text((col * cell_w + 4, 3), f"c={contrast}", fill=0)

    dst = sweep_dir / "contrast_sheet.png"
    sheet.convert("1").save(dst)
    print(f"{dst.relative_to(ROOT)}  {sheet.size[0]}×{sheet.size[1]}")
    print(f"대비 계수 {SWEEP_CONTRAST} 비교. 감열지에 그대로 출력해 고를 것.")


def main() -> None:
    p = argparse.ArgumentParser(description="감열 프린터용 흑백 1비트 캐릭터 이미지 생성")
    p.add_argument("--width", type=int, default=DEFAULTS["width"],
                   help=f"출력 폭 px (기본 {DEFAULTS['width']}, 감열 폭 576의 절반)")
    p.add_argument("--contrast", type=float, default=DEFAULTS["contrast"],
                   help=f"대비 계수 (기본 {DEFAULTS['contrast']})")
    p.add_argument("--gamma", type=float, default=DEFAULTS["gamma"],
                   help=f"감마, 1.0보다 크면 밝아짐 (기본 {DEFAULTS['gamma']})")
    p.add_argument("--no-sharpen", action="store_true", help="언샤프 마스크 끄기")
    p.add_argument("--sweep", action="store_true", help="대비 계수 비교 시트만 생성")
    args = p.parse_args()

    run_sweep(args) if args.sweep else run_build(args)


if __name__ == "__main__":
    main()
