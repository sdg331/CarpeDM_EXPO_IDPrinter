#!/usr/bin/env python3
"""캐릭터 8종이 '유난히 붙어 있는가', 아니면 '생성 얼굴이 원래 다 붙어 있는가'.

이 질문의 답에 따라 처방이 완전히 갈린다.

  (A) 8종만 유난히 붙어 있다  → 40장 풀에서 더 벌어진 8종을 골라 재생성하면 된다
  (B) 생성 얼굴이 원래 다 붙어 있다 → 어떤 8종을 골라도 마찬가지다.
                                    SFace 축 자체를 바꿔야 한다

스타일 세트 40장은 '같은 방식으로 만든 서로 다른 40명'이라 이 비교의 기준이 된다.
"""

from __future__ import annotations

import sys
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.face import FaceEngine, Prototypes, l2_normalize  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
STYLE_SET = ROOT / "assets" / "style_set"
PROTO = ROOT / "assets" / "prototypes.npz"
EXTS = {".png", ".jpg", ".jpeg", ".webp"}


def offdiag(m: np.ndarray) -> np.ndarray:
    return m[np.triu_indices(len(m), 1)]


def summarize(name: str, vals: np.ndarray) -> None:
    q = np.percentile(vals, [50, 90, 99])
    print(f"  {name:22}  중앙 {q[0]:6.3f}   90% {q[1]:6.3f}   "
          f"99% {q[2]:6.3f}   최대 {vals.max():6.3f}")


def greedy_maxmin(vecs: np.ndarray, k: int) -> list[int]:
    """가장 서로 먼 k개를 탐욕적으로 고른다 (max-min diversity)."""
    sim = vecs @ vecs.T
    # 가장 먼 쌍에서 시작
    i, j = np.unravel_index(np.argmin(sim + np.eye(len(sim)) * 9), sim.shape)
    chosen = [int(i), int(j)]
    while len(chosen) < k:
        # 이미 고른 것들과의 최대 유사도가 가장 작은 후보
        worst = sim[:, chosen].max(axis=1)
        worst[chosen] = 9
        chosen.append(int(np.argmin(worst)))
    return chosen


def main() -> None:
    engine = FaceEngine()
    proto = Prototypes.load(PROTO)

    paths = sorted(p for p in STYLE_SET.iterdir() if p.suffix.lower() in EXTS)
    if not paths:
        raise SystemExit(f"스타일 세트가 없다: {STYLE_SET}")

    style = []
    for p in paths:
        img = cv2.imread(str(p))
        try:
            emb, _ = engine.embed_single(img, strict=False)
        except Exception as exc:
            print(f"  ⚠ {p.name}: {exc}")
            continue
        style.append(emb)
    style = np.array(style, dtype=np.float32)
    print(f"스타일 세트 {len(style)}명 · 캐릭터 {len(proto.vectors)}종\n")

    mu_style = style.mean(axis=0)
    mu_char = proto.vectors.mean(axis=0)

    print("═" * 66)
    print("1. 스타일 세트가 캐릭터와 같은 스타일인가")
    print("═" * 66)
    cos_mu = float(l2_normalize(mu_style) @ l2_normalize(mu_char))
    print(f"\n  μ_style · μ_char      {cos_mu:.3f}")
    print(f"  ‖μ_style‖             {np.linalg.norm(mu_style):.3f}")
    print(f"  ‖μ_char‖              {np.linalg.norm(mu_char):.3f}")
    print("\n  → 0.9 이상이면 같은 스타일로 봐도 된다. 낮으면 스타일 세트가")
    print("     캐릭터와 다른 조건(의상·해상도·생성 회차)으로 만들어진 것이다.")

    print("\n" + "═" * 66)
    print("2. 생성 얼굴끼리는 원래 얼마나 붙어 있는가")
    print("═" * 66 + "\n")

    s_raw = offdiag(style @ style.T)
    c_raw = offdiag(proto.vectors @ proto.vectors.T)

    sc = np.array([l2_normalize(v - mu_style) for v in style], dtype=np.float32)
    pc = proto.residuals()
    s_res = offdiag(sc @ sc.T)
    c_res = offdiag(pc @ pc.T)

    print("  [원시 코사인]")
    summarize("스타일 40명끼리", s_raw)
    summarize("캐릭터 8종끼리", c_raw)
    print("\n  [스타일 성분 제거 후]")
    summarize("스타일 40명끼리", s_res)
    summarize("캐릭터 8종끼리", c_res)

    # 캐릭터 쌍이 생성 얼굴 분포에서 어느 위치인가
    pct = float((s_res < c_res.max()).mean() * 100)
    print(f"\n  캐릭터 최대 쌍({c_res.max():.3f})은 생성 얼굴 쌍 분포의 상위 {100 - pct:.1f}%")

    print("\n" + "═" * 66)
    print("3. 40장 풀에서 가장 벌어진 8명을 고르면 얼마나 나아지는가")
    print("═" * 66 + "\n")

    best = greedy_maxmin(sc, 8)
    best_res = offdiag(sc[best] @ sc[best].T)
    print(f"  선택된 번호   {[paths[i].stem.replace('style_', '') for i in best]}")
    print(f"  최대 쌍       {best_res.max():.3f}   (현재 캐릭터 {c_res.max():.3f})")
    print(f"  평균 쌍       {best_res.mean():.3f}   (현재 캐릭터 {c_res.mean():.3f})")

    print("\n" + "═" * 66)
    print("판정")
    print("═" * 66 + "\n")

    gain = c_res.max() - best_res.max()
    if gain > 0.15:
        print(f"  (A) 재선정이 유효하다 — 최대 쌍이 {gain:.3f} 낮아진다.")
        print("      위 번호의 얼굴을 고해상도로 재생성해 캐릭터로 교체하는 것을 검토한다.")
    else:
        print(f"  (B) 재선정 효과가 작다 ({gain:+.3f}). 이 생성기의 얼굴은 원래 붙어 있다.")
        print("      어떤 8종을 골라도 SFace 코사인으로는 이 이상 벌릴 수 없다.")
        print("      → 매칭 축을 바꾸는 쪽을 검토해야 한다 (랜드마크 기하 특징 등).")

    print("\n  ※ 최종 판단은 실제 사람 얼굴로 해야 한다. 캐릭터끼리 붙어 있어도")
    print("     사람이 8종에 고르게 퍼지면 전시로는 성립할 수 있다.")


if __name__ == "__main__":
    main()
