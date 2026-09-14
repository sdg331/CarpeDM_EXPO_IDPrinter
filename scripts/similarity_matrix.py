#!/usr/bin/env python3
"""8×8 코사인 유사도 행렬 — 1단계 게이트의 첫 관문.

특정 쌍이 유독 높으면 시스템이 그 둘을 구분하지 못한다는 뜻이다. 관람객이
어느 쪽에 매칭돼도 사실상 동전 던지기가 되므로, 그 캐릭터는 얼굴형을 더 벌려
재생성하거나 변형 이미지를 붙여 프로토타입을 옮겨야 한다.

판정 기준 — SFace 코사인의 통상적 감각
    ~0.36 이상   동일인으로 취급되는 구간. 캐릭터 쌍이 여기 들어오면 치명적이다.
    0.30~0.36   위험. 구분이 흔들린다.
    0.20~0.30   주의. 성별·안경 같은 공통 요소가 끌어당기는 정도.
    ~0.20 미만   충분히 벌어져 있다.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.face import Prototypes  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
PROTO = ROOT / "assets" / "prototypes.npz"

CRITICAL, RISKY, WATCH = 0.36, 0.30, 0.20


def band(v: float) -> str:
    if v >= CRITICAL:
        return "치명"
    if v >= RISKY:
        return "위험"
    if v >= WATCH:
        return "주의"
    return "양호"


def show_matrix(m: np.ndarray, short: list[str], groups: list[str]) -> list[tuple]:
    print("      " + "".join(f"{s:>7}" for s in short) + "   그룹")
    for i, row in enumerate(m):
        cells = "".join("      ·" if i == j else f"{row[j]:7.3f}"
                        for j in range(len(row)))
        print(f"  {short[i]}  {cells}    {groups[i]}")

    pairs = [(m[i, j], short[i], short[j], groups[i] == groups[j])
             for i in range(len(short)) for j in range(i + 1, len(short))]
    pairs.sort(reverse=True)

    print("\n  가장 가까운 쌍")
    for v, a, b, same in pairs[:5]:
        print(f"    {a}–{b}  {v:6.3f}  {band(v):4}  {'동일그룹' if same else '다른그룹'}")

    within = [v for v, _, _, same in pairs if same]
    between = [v for v, _, _, same in pairs if not same]
    print(f"\n  그룹 내 평균 {np.mean(within):6.3f}   "
          f"그룹 간 평균 {np.mean(between):6.3f}   "
          f"차이 {np.mean(within) - np.mean(between):6.3f}")
    return pairs


def main() -> None:
    if not PROTO.exists():
        raise SystemExit("prototypes.npz 가 없다. scripts/build_prototypes.py 를 먼저 실행할 것.")

    p = Prototypes.load(PROTO)
    short = [i.replace("char_", "") for i in p.ids]
    n = len(short)

    print("═" * 64)
    print("A. 원시 코사인 (보정 없음)")
    print("═" * 64 + "\n")
    raw_pairs = show_matrix(p.vectors @ p.vectors.T, short, p.groups)
    print(f"\n  공통 성분 에너지 비율  {p.style_energy * 100:.1f}%")

    print("\n" + "═" * 64)
    if p.style_n:
        print(f"B. 스타일 성분 제거 (독립 표본 {p.style_n}장으로 추정)")
    else:
        print("B. 스타일 성분 제거 (⚠ 8종 자기 평균 — 아래 주의 참고)")
    print("═" * 64 + "\n")

    res = p.residuals()
    res_pairs = show_matrix(res @ res.T, short, p.groups)

    if not p.style_n:
        artifact = -1.0 / (n - 1)
        actual = float(np.mean([v for v, _, _, _ in res_pairs]))
        print(f"\n  ⚠ 자기 평균 센터링이라 잔차 평균이 {artifact:.3f}로 강제된다"
              f" (실측 {actual:.3f}).")
        print("     이 값은 정보가 아니라 항등식이다. 최대 쌍과 구조만 읽을 것.")
        print("     scripts/style_set_prompts.md 로 독립 표본을 만들면 해소된다.")

    # ---------- 판정 ----------
    raw_worst, res_worst = raw_pairs[0][0], res_pairs[0][0]

    print("\n" + "═" * 64)
    print("판정\n")
    print(f"  A 원시 최대 쌍   {raw_worst:.3f}  {band(raw_worst)}")
    print(f"  B 잔차 최대 쌍   {res_worst:.3f}  {band(res_worst)}")

    # 전시에서 실제로 쓰는 건 B다. A는 공통 성분 때문에 언제나 높게 나온다.
    if res_worst >= CRITICAL:
        print(f"\n  ❌ 실패 — 잔차에서도 {res_worst:.3f}. 매칭 축을 다시 봐야 한다.")
    elif res_worst >= RISKY:
        print(f"\n  ⚠ 조건부 — 잔차 {res_worst:.3f}. 해당 쌍은 실제로 자주 헷갈린다.")
    else:
        print(f"\n  ✅ 통과 — 잔차 {res_worst:.3f}. 8종이 충분히 벌어져 있다.")

    if not p.style_n:
        print("\n  ※ 스타일 세트가 없어 이 판정은 잠정이다.")
    print("  ※ 이 행렬은 캐릭터끼리의 거리만 본다. 실제 사람이 8종에 고르게")
    print("     퍼지는지는 distribution_test.py 로 따로 확인해야 한다.")


if __name__ == "__main__":
    main()
