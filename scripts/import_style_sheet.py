#!/usr/bin/env python3
"""그리드 시트(콘택트 시트) 한 장에서 얼굴을 잘라 assets/style_set/ 에 넣는다.

이미지 생성 도구가 40장을 개별 파일이 아니라 5×4 격자 한 장으로 내주는 경우가 있다.
격자 좌표를 하드코딩하지 않고 YuNet으로 얼굴을 찾아 자른다 — 캡션 유무나 여백
차이에 영향을 받지 않는다.

읽기 순서(왼→오, 위→아래)로 번호를 매기므로 style_set_prompts.md 의 묘사 번호와
그대로 대응된다.

사용법
    python scripts/import_style_sheet.py 남자시트.png --start 1
    python scripts/import_style_sheet.py 여자시트.png --start 21
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.face import FaceEngine  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "style_set"


def detect_full_res(engine: FaceEngine, img: np.ndarray):
    """시트의 얼굴은 작아서(150px 안팎) 축소 검출을 쓰면 놓친다. 원본 해상도로 본다."""
    h, w = img.shape[:2]
    engine._det.setInputSize((w, h))
    _, faces = engine._det.detect(img)
    return [] if faces is None else [f.astype(np.float32) for f in faces]


def reading_order(faces: list[np.ndarray], cols: int) -> list[np.ndarray]:
    """행 단위로 묶은 뒤 각 행을 왼→오로 정렬한다."""
    faces = sorted(faces, key=lambda f: f[1] + f[3] / 2)  # y 중심
    rows = [faces[i:i + cols] for i in range(0, len(faces), cols)]
    out = []
    for row in rows:
        out.extend(sorted(row, key=lambda f: f[0] + f[2] / 2))  # x 중심
    return out


def grid_pitch(faces: list[np.ndarray], cols: int) -> tuple[float, float]:
    """격자 한 칸의 크기를 얼굴 중심 간격에서 추정한다. 좌표를 하드코딩하지 않으려는 것.

    시트는 칸 사이에 여백이 거의 없어서, 이 간격을 넘겨 자르면 곧바로 이웃 칸의
    어깨나 캡션 숫자가 딸려 들어온다.
    """
    ordered = reading_order(faces, cols)
    cy = np.array([f[1] + f[3] / 2 for f in ordered])
    cx = np.array([f[0] + f[2] / 2 for f in ordered])

    # 같은 행 안의 가로 간격, 행과 행 사이의 세로 간격
    dx = np.diff(cx.reshape(-1, cols), axis=1).ravel()
    dy = np.diff(cy.reshape(-1, cols), axis=0).ravel()
    return float(np.median(dx)), float(np.median(dy))


def crop_portrait(engine: FaceEngine, img: np.ndarray, face: np.ndarray,
                  pitch: tuple[float, float] | None = None) -> np.ndarray | None:
    """얼굴 하나만 담긴 3:4 세로 크롭.

    두 가지를 지킨다.

    **비율을 깨지 않는다.** 창이 시트 밖으로 나가면 잘라내는 게 아니라 안쪽으로
    민다. 예전에는 경계에서 clamp 해서 3:4가 무너진 크롭이 섞여 나왔다.

    **이웃 칸을 물지 않는다.** 격자 간격이 주어지면 창을 그 안쪽으로 제한한다.
    캡션 숫자는 칸 좌상단에 있어서, 폭이 넓어지는 순간 왼쪽 끝에 딸려 들어온다.
    """
    ih, iw = img.shape[:2]
    x, y, w, h = face[:4]
    cx, cy = x + w / 2, y + h / 2

    # 칸을 넘지 않는 상한. 여백 없이 붙은 격자라 조금 안쪽으로 잡는다.
    max_h = min(ih, pitch[1] * 0.88) if pitch else ih
    max_w = min(iw, pitch[0] * 0.72) if pitch else iw

    for scale in (1.8, 1.65, 1.5, 1.35, 1.2):
        ch = min(h * scale, max_h, max_w / 0.75)
        cw = ch * 0.75

        # 증명사진 프레이밍 — 정수리를 위에서 약 8% 지점에 둔다.
        # 이보다 여백을 더 주면 칸 좌상단의 캡션 숫자가 왼쪽 위에 걸린다.
        left, top = cx - cw / 2, cy - ch * 0.42

        # 경계 밖이면 밀어 넣는다 (자르지 않는다 — 비율 유지)
        left = min(max(0.0, left), iw - cw)
        top = min(max(0.0, top), ih - ch)

        x0, y0 = int(round(left)), int(round(top))
        crop = img[y0:y0 + int(round(ch)), x0:x0 + int(round(cw))]
        if crop.shape[0] < 40 or crop.shape[1] < 40:
            continue

        if len(engine.detect(crop)) == 1:
            return crop

    return None


def main() -> None:
    ap = argparse.ArgumentParser(description="그리드 시트에서 얼굴을 잘라 스타일 세트로 저장")
    ap.add_argument("sheet", type=Path, help="시트 이미지 경로")
    ap.add_argument("--start", type=int, required=True, help="시작 번호 (예: 1, 21)")
    ap.add_argument("--cols", type=int, default=5, help="격자 열 수 (기본 5)")
    ap.add_argument("--expect", type=int, default=20, help="기대하는 얼굴 수 (기본 20)")
    ap.add_argument("--out", default="style_set",
                    help="assets/ 아래 출력 폴더명 (기본 style_set, 후보 풀은 pool)")
    ap.add_argument("--prefix", default=None, help="파일 접두사 (기본은 출력 폴더명)")
    args = ap.parse_args()

    global OUT
    OUT = ROOT / "assets" / args.out
    prefix = args.prefix or args.out

    img = cv2.imread(str(args.sheet))
    if img is None:
        raise SystemExit(f"읽을 수 없다: {args.sheet}")
    print(f"시트 {img.shape[1]}×{img.shape[0]}")

    engine = FaceEngine()
    faces = detect_full_res(engine, img)
    print(f"얼굴 {len(faces)}개 검출")

    if len(faces) != args.expect:
        print(f"⚠ 기대 {args.expect}개와 다르다. --cols/--expect 를 확인할 것.")

    OUT.mkdir(parents=True, exist_ok=True)
    saved, failed = 0, []

    pitch = grid_pitch(faces, args.cols) if len(faces) % args.cols == 0 else None
    if pitch:
        print(f"격자 간격 {pitch[0]:.0f}×{pitch[1]:.0f}px")

    for i, face in enumerate(reading_order(faces, args.cols)):
        idx = args.start + i
        crop = crop_portrait(engine, img, face, pitch)
        if crop is None:
            failed.append(idx)
            continue
        dst = OUT / f"{prefix}_{idx:02d}.png"
        cv2.imwrite(str(dst), crop)
        saved += 1

    print(f"\n저장 {saved}장  →  {OUT.relative_to(ROOT)}")
    if failed:
        print(f"⚠ 실패 {failed} — 이웃 얼굴이 겹쳐 단독 크롭이 안 됐다. 수동 확인 필요.")

    total = len(list(OUT.glob("*.png")))
    print(f"현재 스타일 세트 {total}장")


if __name__ == "__main__":
    main()
