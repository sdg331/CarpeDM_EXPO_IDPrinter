#!/usr/bin/env python3
"""8×8 행렬이 실패했을 때 원인을 가르는 진단.

세 가지를 확인한다.
  1. 파이프라인 자체가 정상인가 (같은 얼굴 = 1.0, 변형 = 높음)
  2. 8종이 임베딩 공간에서 실제로 뭉쳐 있는가 (공통 성분 비율)
  3. 공통 성분을 빼면(centering) 분리가 살아나는가
"""

from __future__ import annotations

import sys
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.face import FaceEngine, Prototypes, l2_normalize  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
CHARS = ROOT / "assets" / "characters"
PROTO = ROOT / "assets" / "prototypes.npz"


def section(t: str) -> None:
    print(f"\n{'─' * 62}\n{t}\n")


def main() -> None:
    engine = FaceEngine()
    p = Prototypes.load(PROTO)
    short = [i.replace("char_", "") for i in p.ids]

    # ---------- 1. 파이프라인 정상성 ----------
    section("1. 파이프라인 정상성 — char_01을 변형해 자기 자신과 비교")

    img = cv2.imread(str(CHARS / "char_01.png"))
    base, _ = engine.embed_single(img, strict=False)

    variants = {
        "동일 이미지": img,
        "좌우 반전": cv2.flip(img, 1),
        "밝기 +25%": cv2.convertScaleAbs(img, alpha=1.25, beta=0),
        "밝기 -25%": cv2.convertScaleAbs(img, alpha=0.75, beta=0),
        "가우시안 블러": cv2.GaussianBlur(img, (9, 9), 0),
        "JPEG 품질 40": cv2.imdecode(
            cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, 40])[1], cv2.IMREAD_COLOR
        ),
        "640px 축소": cv2.resize(img, (480, 640), interpolation=cv2.INTER_AREA),
    }
    for name, v in variants.items():
        emb, _ = engine.embed_single(v, strict=False)
        print(f"  {name:14}  {float(base @ emb):6.3f}")

    print("\n  → 동일 이미지가 1.000이고 나머지가 0.8 이상이면 파이프라인은 정상이다.")

    # ---------- 2. 공통 성분 ----------
    section("2. 8종이 공통으로 갖는 성분의 크기")

    mean_vec = p.vectors.mean(axis=0)
    mean_norm = float(np.linalg.norm(mean_vec))
    print(f"  평균 벡터의 노름          {mean_norm:.3f}   (1.0에 가까울수록 완전히 뭉친 것)")

    cos_to_mean = p.vectors @ l2_normalize(mean_vec)
    print(f"  각 캐릭터–평균 코사인     {cos_to_mean.min():.3f} ~ {cos_to_mean.max():.3f}")

    # 공통 성분이 차지하는 에너지 비율
    energy = mean_norm ** 2
    print(f"  공통 성분 에너지 비율     {energy * 100:.1f}%")
    print("\n  → 이 비율이 크면 임베딩이 '얼굴 차이'가 아니라 '생성 스타일'을 보고 있다.")

    # ---------- 3. centering 후 재분리 ----------
    section("3. 공통 성분을 뺀 뒤(centering) 다시 본 8×8")

    centered = np.array([l2_normalize(v - mean_vec) for v in p.vectors], dtype=np.float32)
    m = centered @ centered.T

    print("      " + "".join(f"{s:>7}" for s in short))
    for i, row in enumerate(m):
        cells = "".join("      ·" if i == j else f"{row[j]:7.3f}" for j in range(len(row)))
        print(f"  {short[i]}  {cells}")

    before = p.vectors @ p.vectors.T
    iu = np.triu_indices(len(short), 1)
    print(f"\n  비대각 최대   {before[iu].max():.3f}  →  {m[iu].max():.3f}")
    print(f"  비대각 평균   {before[iu].mean():.3f}  →  {m[iu].mean():.3f}")
    print("\n  → 크게 떨어지면 centering이 유효한 처방이다. 다만 관람객 임베딩에도")
    print("     같은 보정을 적용해야 하고, 그 효과는 실제 사람 얼굴로 검증해야 한다.")


if __name__ == "__main__":
    main()
