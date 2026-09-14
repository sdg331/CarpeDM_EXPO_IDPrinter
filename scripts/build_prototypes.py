#!/usr/bin/env python3
"""캐릭터 8종의 프로토타입 벡터를 만들어 assets/prototypes.npz 에 저장한다.

변형 이미지가 있으면 함께 평균낸다. 기대하는 배치는 이렇다.

    assets/characters/char_01.png              ← 표시용 원본 (필수)
    assets/characters/variants/char_01/*.png   ← i2i 변형 (있으면 자동 사용)

변형이 없으면 원본 1장만으로 프로토타입을 만든다. character-prompts.md 가 지적한
대로 1장짜리는 뾰족해서 매칭이 불안정할 수 있지만, 먼저 8×8 행렬을 보고
문제 있는 캐릭터만 골라 변형을 뽑는 쪽이 싸다.
"""

from __future__ import annotations

import sys
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.face import FaceEngine, Prototypes, l2_normalize, load_groups  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
CHARS = ROOT / "assets" / "characters"
VARIANTS = CHARS / "variants"
STYLE_SET = ROOT / "assets" / "style_set"
OUT = ROOT / "assets" / "prototypes.npz"

EXTS = {".png", ".jpg", ".jpeg", ".webp"}


def images_for(char_id: str) -> list[Path]:
    """원본 + 변형 전부. 원본이 항상 첫 번째다."""
    paths = [CHARS / f"{char_id}.png"]
    vdir = VARIANTS / char_id
    if vdir.is_dir():
        paths += sorted(p for p in vdir.iterdir()
                        if p.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"})
    return paths


def build_style_mean(engine: FaceEngine) -> tuple[np.ndarray | None, int]:
    """스타일 추정 세트로 μ_style을 구한다 (scripts/style_set_prompts.md 참고).

    캐릭터 8종과 **독립된** 표본이어야 한다. 8종 자기 평균으로 센터링하면
    잔차 사이에 −1/(n−1)의 음의 상관이 강제돼 분리도를 잘못 읽게 된다.
    """
    if not STYLE_SET.is_dir():
        return None, 0

    paths = sorted(p for p in STYLE_SET.iterdir() if p.suffix.lower() in EXTS)
    if not paths:
        return None, 0

    embeddings = []
    for path in paths:
        img = cv2.imread(str(path))
        if img is None:
            print(f"  ⚠ 읽기 실패 {path.name}")
            continue
        try:
            emb, _ = engine.embed_single(img, strict=False)
        except Exception as exc:
            print(f"  ⚠ {path.name}: {exc}")
            continue
        embeddings.append(emb)

    if not embeddings:
        return None, 0
    return np.mean(embeddings, axis=0).astype(np.float32), len(embeddings)


def main() -> None:
    engine = FaceEngine()

    char_ids = sorted(p.stem for p in CHARS.glob("char_*.png"))
    if not char_ids:
        raise SystemExit(f"캐릭터 원본이 없다: {CHARS}/char_*.png")

    ids, vectors, counts, groups = [], [], [], []
    group_map = load_groups()

    for char_id in char_ids:
        embeddings = []
        for path in images_for(char_id):
            img = cv2.imread(str(path))
            if img is None:
                print(f"  ⚠ 읽기 실패 {path.name}")
                continue
            try:
                # 캐릭터 원본은 신뢰할 수 있는 입력이라 다중 얼굴 검사를 끈다.
                emb, det = engine.embed_single(img, strict=False)
            except Exception as exc:
                print(f"  ⚠ {path.name}: {exc}")
                continue
            embeddings.append(emb)

        if not embeddings:
            raise SystemExit(f"{char_id}: 쓸 수 있는 이미지가 하나도 없다")

        # 정규화된 벡터들을 평균낸 뒤 다시 정규화해야 코사인이 내적과 같아진다.
        proto = l2_normalize(np.mean(embeddings, axis=0))

        ids.append(char_id)
        vectors.append(proto)
        counts.append(len(embeddings))
        groups.append(group_map.get(char_id, "?"))

        note = "원본만" if len(embeddings) == 1 else f"원본+변형 {len(embeddings)}장 평균"
        print(f"{char_id}  그룹 {groups[-1]}  {note}")

    mu_style, style_n = build_style_mean(engine)
    if style_n:
        print(f"\n스타일 세트 {style_n}장으로 μ_style 추정")
    else:
        print("\n스타일 세트 없음 — 8종 자기 평균으로 대체한다")

    Prototypes(ids=ids, vectors=np.array(vectors, dtype=np.float32),
               counts=counts, groups=groups,
               mu_style=mu_style, style_n=style_n).save(OUT)

    print(f"저장 {OUT.relative_to(ROOT)}  ({len(ids)}종 × 128차원)")

    if all(c == 1 for c in counts):
        print("주의: 변형 이미지가 없다. 지금은 보류가 맞다 — PLAN.md §7 참고.")
    if style_n == 0:
        print("주의: μ_style이 8종 자기 평균이라 잔차 상관이 −1/7로 강제된다.")
        print("      scripts/style_set_prompts.md 로 40장을 만들어 넣을 것.")
    elif style_n < 24:
        print(f"주의: 스타일 세트가 {style_n}장뿐이다. 24장 이상을 권장한다.")


if __name__ == "__main__":
    main()
