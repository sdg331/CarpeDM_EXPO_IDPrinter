#!/usr/bin/env python3
"""후보 풀에서 서로 가장 먼 8명을 골라 캐릭터로 확정한다.

**1단계에서 배운 것** — 얼굴 특징 축(얼굴 길이 × 하관 폭 × 이목구비 간격)을
설계해서 8종을 만들면, SFace 임베딩에서는 오히려 **무작위보다 나쁘게** 뭉친다.
두 축을 공유하는 쌍(예: 03·04는 이목구비 간격만 다름)이 사실상 같은 벡터가 되기
때문이다. SFace가 '이목구비 간격'을 거의 인코딩하지 않는다.

그래서 8종을 **설계로 정하지 않고 측정해서 고른다.** 후보를 넉넉히 만든 뒤
임베딩 공간에서 max-min(서로 가장 먼 조합)으로 선정한다.

μ_style 은 **선정되지 않은 나머지**로 계산한다. 선정된 8종이 자기 평균에 끼면
잔차 상관이 인위적으로 눌리기 때문이다.

사용법
    python scripts/select_characters.py                    # 선정 결과만 확인
    python scripts/select_characters.py --apply            # assets/characters/ 에 반영
    python scripts/select_characters.py --balance 4 4      # 남녀 4:4 강제 (기본)
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.face import FaceEngine, l2_normalize  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
POOL = ROOT / "assets" / "pool"
CHARS = ROOT / "assets" / "characters"
EXTS = {".png", ".jpg", ".jpeg", ".webp"}

# style_set_prompts.md 규약 — 01~20 남성, 21~40 여성.
# 파일명의 숫자로 그룹을 추정한다. 다른 규약이면 --split 으로 바꾼다.
DEFAULT_SPLIT = 20


def load_pool(engine: FaceEngine) -> tuple[list[Path], np.ndarray]:
    if not POOL.is_dir():
        raise SystemExit(
            f"후보 풀이 없다: {POOL}\n"
            "scripts/style_set_prompts.md 의 프롬프트로 생성한 이미지를 넣을 것."
        )
    paths = sorted(p for p in POOL.iterdir() if p.suffix.lower() in EXTS)
    if len(paths) < 16:
        raise SystemExit(f"후보가 {len(paths)}장뿐이다. 최소 24장, 권장 40장 이상.")

    kept, embs = [], []
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
        kept.append(path)
        embs.append(emb)
    return kept, np.array(embs, dtype=np.float32)


def file_index(path: Path) -> int:
    digits = "".join(c for c in path.stem if c.isdigit())
    return int(digits) if digits else 0


def greedy_maxmin(vecs: np.ndarray, k: int, groups: np.ndarray | None,
                  quota: dict | None) -> list[int]:
    """서로 가장 먼 k개를 탐욕적으로 고른다. quota 가 있으면 그룹별 정원을 지킨다."""
    sim = vecs @ vecs.T
    n = len(vecs)
    taken: dict = {} if quota is None else {g: 0 for g in quota}

    def allowed(i: int) -> bool:
        if quota is None:
            return True
        g = groups[i]
        return taken.get(g, 0) < quota.get(g, 0)

    # 가장 먼 쌍에서 시작하되 정원을 넘지 않는 조합으로
    best, chosen = 9.0, []
    for i in range(n):
        for j in range(i + 1, n):
            if sim[i, j] < best:
                cand = [i, j]
                if quota is not None:
                    c: dict = {}
                    for x in cand:
                        c[groups[x]] = c.get(groups[x], 0) + 1
                    if any(c[g] > quota.get(g, 0) for g in c):
                        continue
                best, chosen = float(sim[i, j]), cand
    if quota is not None:
        for x in chosen:
            taken[groups[x]] += 1

    while len(chosen) < k:
        worst = sim[:, chosen].max(axis=1)
        order = np.argsort(worst)
        for i in order:
            i = int(i)
            if i in chosen or not allowed(i):
                continue
            chosen.append(i)
            if quota is not None:
                taken[groups[i]] += 1
            break
        else:
            raise SystemExit("정원 제약을 만족하는 조합을 찾지 못했다. --balance 를 조정할 것.")
    return chosen


def offdiag(m: np.ndarray) -> np.ndarray:
    return m[np.triu_indices(len(m), 1)]


def main() -> None:
    ap = argparse.ArgumentParser(description="후보 풀에서 캐릭터 8종 선정")
    ap.add_argument("-k", type=int, default=8, help="선정 수 (기본 8)")
    ap.add_argument("--balance", nargs=2, type=int, metavar=("A", "B"),
                    default=[4, 4], help="그룹별 정원 (기본 4 4). 0 0 이면 무제한")
    ap.add_argument("--split", type=int, default=DEFAULT_SPLIT,
                    help=f"이 번호 이하를 그룹 A로 본다 (기본 {DEFAULT_SPLIT})")
    ap.add_argument("--apply", action="store_true",
                    help="선정 결과를 assets/characters/ 에 복사한다")
    args = ap.parse_args()

    engine = FaceEngine()
    paths, embs = load_pool(engine)
    print(f"후보 {len(paths)}장 로드\n")

    groups = np.array(["A" if file_index(p) <= args.split else "B" for p in paths])
    quota = None
    if any(args.balance):
        quota = {"A": args.balance[0], "B": args.balance[1]}
        print(f"그룹 정원  A {quota['A']}명 · B {quota['B']}명 "
              f"(풀 구성 A {int((groups == 'A').sum())} · B {int((groups == 'B').sum())})")

    # μ 추정과 선정이 서로를 참조하므로 몇 번 반복해 수렴시킨다.
    chosen = list(range(args.k))
    for _ in range(4):
        rest = [i for i in range(len(embs)) if i not in chosen]
        mu = embs[rest].mean(axis=0) if rest else embs.mean(axis=0)
        centered = np.array([l2_normalize(v - mu) for v in embs], dtype=np.float32)
        new = greedy_maxmin(centered, args.k, groups, quota)
        if sorted(new) == sorted(chosen):
            break
        chosen = new

    rest = [i for i in range(len(embs)) if i not in chosen]
    mu = embs[rest].mean(axis=0)
    centered = np.array([l2_normalize(v - mu) for v in embs], dtype=np.float32)
    sel = centered[chosen]
    pairs = offdiag(sel @ sel.T)

    print("\n선정 결과\n")
    for rank, i in enumerate(chosen, 1):
        print(f"  {rank}  {paths[i].name}   그룹 {groups[i]}")

    print(f"\n  최대 쌍  {pairs.max():6.3f}")
    print(f"  평균 쌍  {pairs.mean():6.3f}")
    print(f"  μ_style  나머지 {len(rest)}장으로 추정")

    # 무작위 선정 대비 얼마나 좋은지
    # 한 번 뽑은 표본 **안에서의** 쌍을 봐야 한다. 서로 다른 두 표본을 교차 곱하면
    # 같은 후보가 양쪽에 들어갈 때 자기 자신과의 1.000 이 섞여 기준선이 무너진다.
    rng = np.random.default_rng(0)
    rand = np.empty(2000)
    for t in range(2000):
        s = centered[rng.choice(len(centered), args.k, replace=False)]
        rand[t] = offdiag(s @ s.T).max()
    print(f"  무작위 선정 중앙값 {np.median(rand):.3f} — 이번 선정이 상위 "
          f"{(rand > pairs.max()).mean() * 100:.1f}%")

    print("\n판정")
    if pairs.max() >= 0.36:
        print(f"  ❌ 최대 쌍 {pairs.max():.3f} — 후보 풀을 더 늘려야 한다.")
    elif pairs.max() >= 0.30:
        print(f"  ⚠ 최대 쌍 {pairs.max():.3f} — 쓸 수는 있으나 그 쌍은 자주 헷갈린다.")
    else:
        print(f"  ✅ 최대 쌍 {pairs.max():.3f} — 충분히 벌어졌다.")

    if not args.apply:
        print("\n반영하려면 --apply 를 붙여 다시 실행할 것.")
        return

    # ---------- 반영 ----------
    CHARS.mkdir(parents=True, exist_ok=True)
    backup = CHARS / "_previous"
    old = sorted(CHARS.glob("char_*.png"))
    if old:
        backup.mkdir(exist_ok=True)
        for p in old:
            shutil.move(str(p), str(backup / p.name))
        print(f"\n기존 8종을 {backup.relative_to(ROOT)} 로 옮겼다")

    style_dir = ROOT / "assets" / "style_set"
    if style_dir.is_dir():
        for p in style_dir.glob("*.png"):
            p.unlink()
    style_dir.mkdir(parents=True, exist_ok=True)

    # char_01~08 은 max-min 선정 순서로 다시 매겨진다. 파일명만으로는 그룹을
    # 알 수 없으므로(풀에서의 번호가 사라진다) 대응표를 함께 남긴다.
    # build_prototypes.py 가 backend.face.load_groups() 로 이걸 읽는다.
    group_map = {f"char_{n:02d}": str(groups[i]) for n, i in enumerate(chosen, 1)}

    for n, i in enumerate(chosen, 1):
        shutil.copy2(paths[i], CHARS / f"char_{n:02d}.png")
    for i in rest:
        shutil.copy2(paths[i], style_dir / f"style_{file_index(paths[i]):02d}.png")
    (CHARS / "groups.json").write_text(
        json.dumps(group_map, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    print(f"캐릭터 {len(chosen)}종 → {CHARS.relative_to(ROOT)}")
    print(f"그룹 대응표 → {(CHARS / 'groups.json').relative_to(ROOT)}  "
          + " ".join(f"{k.replace('char_', '')}:{v}" for k, v in group_map.items()))
    print(f"μ_style 표본 {len(rest)}장 → {style_dir.relative_to(ROOT)}")
    print("\n다음: build_prototypes.py → similarity_matrix.py → make_print_assets.py")


if __name__ == "__main__":
    main()
