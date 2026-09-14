#!/usr/bin/env python3
"""실제 얼굴 표본으로 매칭 분포를 보고, 도메인 보정값을 확정한다.

진단(scripts/diagnose_embedding.py)에서 드러난 문제는 이렇다.
캐릭터 8종 임베딩의 56%가 서로 공유하는 '생성 스타일' 성분이라, 원시 코사인으로는
8종이 전부 붙어 버린다(최대 쌍 0.810). 관람객 얼굴 쪽에도 같은 종류의 공통 성분
(실사·웹캠·조명)이 있고, 그건 캐릭터 쪽과 방향이 다르다.

**처방 — 도메인별 평균 제거.**
    캐릭터:  p'ᵢ = normalize(pᵢ − μ_char)
    관람객:  v'  = normalize(v  − μ_real)
    점수  =  v' · p'ᵢ

각 도메인에서 '평균 얼굴로부터 어느 방향으로 벗어났는가'만 남겨 비교한다.
이게 사람이 말하는 "닮았다"에 훨씬 가깝다. μ_char은 이미 있고, μ_real은
이 스크립트가 표본에서 계산해 assets/domain_mean.npz 에 저장한다.

사용법
    python scripts/distribution_test.py                 # data/test_faces/ 전부
    python scripts/distribution_test.py --save          # 보정값까지 저장
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.face import FaceEngine, Prototypes, l2_normalize  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
FACES = ROOT / "data" / "test_faces"
PROTO = ROOT / "assets" / "prototypes.npz"
DOMAIN = ROOT / "assets" / "domain_mean.npz"

EXTS = {".png", ".jpg", ".jpeg", ".webp"}


def load_faces(engine: FaceEngine, faces_dir: Path) -> tuple[list[str], np.ndarray]:
    paths = sorted(p for p in faces_dir.rglob("*") if p.suffix.lower() in EXTS)
    if not paths:
        raise SystemExit(
            f"표본이 없다: {faces_dir}\n"
            "scripts/capture_faces.py 로 찍거나, 사진을 이 폴더에 넣을 것."
        )

    names, embs = [], []
    for path in paths:
        img = cv2.imread(str(path))
        if img is None:
            print(f"  ⚠ 읽기 실패 {path.name}")
            continue
        try:
            emb, det = engine.embed_single(img, strict=False)
        except Exception as exc:
            print(f"  ⚠ {path.name}: {exc}")
            continue
        names.append(path.stem)
        embs.append(emb)

    if not embs:
        raise SystemExit("얼굴을 추출한 표본이 하나도 없다.")
    return names, np.array(embs, dtype=np.float32)


def report(title: str, scores: np.ndarray, proto: Prototypes, names: list[str]) -> dict:
    """scores: (표본수, 8). 분포·마진·그룹 쏠림을 요약한다."""
    short = [i.replace("char_", "") for i in proto.ids]
    top = scores.argmax(axis=1)

    order = np.sort(scores, axis=1)[:, ::-1]
    margin = order[:, 0] - order[:, 1]

    counts = Counter(top.tolist())
    n = len(names)
    ideal = n / len(short)

    print(f"\n── {title} " + "─" * (52 - len(title)))
    print(f"\n  매칭 분포 (표본 {n}명, 균등하면 각 {ideal:.1f}명)")
    for i, s in enumerate(short):
        c = counts.get(i, 0)
        bar = "█" * c
        flag = "  ←쏠림" if c > ideal * 2.5 else ("  ←미매칭" if c == 0 else "")
        print(f"    {s} [{proto.groups[i]}]  {c:2}  {bar}{flag}")

    used = len(counts)
    print(f"\n  사용된 캐릭터   {used}/{len(short)}종")
    print(f"  1–2위 마진      평균 {margin.mean():.4f}  최소 {margin.min():.4f}")
    print(f"  1위 점수        {order[:, 0].min():.3f} ~ {order[:, 0].max():.3f}")

    # 마진이 촬영 변동(진단 기준 코사인 0.95 수준 흔들림)보다 작으면 순위가 뒤집힌다.
    fragile = int((margin < 0.02).sum())
    print(f"  마진 0.02 미만  {fragile}명  ({fragile / n * 100:.0f}%) — 촬영마다 결과가 바뀔 수 있음")

    return dict(used=used, margin=float(margin.mean()),
                fragile=fragile, counts=counts, n=n)


def main() -> None:
    ap = argparse.ArgumentParser(description="실제 얼굴 표본으로 매칭 분포 검증")
    ap.add_argument("--save", action="store_true",
                    help="도메인 보정값을 assets/domain_mean.npz 에 저장")
    ap.add_argument("--dir", type=Path, default=FACES,
                    help=f"표본 폴더 (기본 {FACES.relative_to(ROOT)})")
    args = ap.parse_args()

    engine = FaceEngine()
    proto = Prototypes.load(PROTO)

    names, faces = load_faces(engine, args.dir)
    print(f"표본 {len(names)}명 로드 완료")
    if proto.style_n:
        print(f"캐릭터 쪽 중심화는 μ_style (독립 {proto.style_n}장) 을 쓴다")
    else:
        print("⚠ μ_style 이 없다 — 8종 자기 평균으로 대체되며 분리도가 왜곡된다(PLAN.md §7.4)")

    mu_char = proto.vectors.mean(axis=0)
    mu_real = faces.mean(axis=0)

    print(f"\n도메인 간 거리")
    print(f"  μ_char · μ_real  {float(l2_normalize(mu_char) @ l2_normalize(mu_real)):.3f}")
    print("  (1.0에 가까우면 두 도메인이 같은 방향 — 보정 효과가 크다)")

    # 두 분석 모두 **백엔드가 실제로 부르는 함수**를 그대로 쓴다.
    # 여기서 로직을 따로 구현하면 게이트에서 본 수치와 전시에서 도는 수치가 갈라진다
    # (backend/face.py 첫머리 참고). 예전에는 B 를 8종 자기 평균으로 중심화해서
    # 프로덕션(μ_style)과 다른 값을 보고 판단하고 있었다.
    raw = np.array([proto.raw_scores(v) for v in faces], dtype=np.float32)
    a = report("A. 원시 코사인 (보정 없음)", raw, proto, names)

    calibrated = np.array([proto.match_scores(v, mu_real) for v in faces], dtype=np.float32)
    b = report("B. 도메인별 평균 제거 (전시에서 쓰는 경로)", calibrated, proto, names)

    # ---------- 판정 ----------
    print("\n" + "═" * 62)
    print("판정\n")
    for tag, r in (("A 보정없음", a), ("B 평균제거", b)):
        ok = r["used"] >= 6 and r["fragile"] / r["n"] < 0.25
        print(f"  {tag}   사용 {r['used']}/8종   마진 {r['margin']:.4f}   "
              f"불안정 {r['fragile']}/{r['n']}   {'✅' if ok else '❌'}")

    print("\n  통과 기준 — 8종 중 6종 이상이 쓰이고, 마진 0.02 미만 표본이 25% 미만")
    if len(names) < 40:
        print(f"  ※ 표본 {len(names)}명은 방향 판단용이다. 확정하려면 40명이 필요하다")
        print("     (캐릭터당 5명이 되어야 쏠림을 해석할 수 있다).")

    if args.save:
        if args.dir != FACES:
            raise SystemExit(
                f"\n❌ --dir 로 다른 폴더를 보면서 --save 하지 않는다.\n"
                f"   μ_real 은 {FACES.relative_to(ROOT)} 의 실제 얼굴에서만 나와야 한다.\n"
                "   --dir 은 배관 점검용이다."
            )
        np.savez(DOMAIN, mu_char=mu_char, mu_real=mu_real,
                 sample_size=np.array([len(names)]))
        print(f"\n저장 {DOMAIN.relative_to(ROOT)}  (표본 {len(names)}명 기준)")
        if len(names) < 10:
            print(f"  ⚠ 표본 {len(names)}명은 방향 판단에도 모자란다. 10명은 채울 것.")
        print("  표본이 늘어나면 다시 실행해 갱신할 것.")
        print("  **백엔드를 재시작해야 적용된다** — 기동 시 한 번만 읽는다.")


if __name__ == "__main__":
    main()
