#!/usr/bin/env python3
"""분포 테스트용 실제 얼굴 사진을 모은다.

**왜 필요한가** — 진단 결과 캐릭터 8종 임베딩의 56%가 '생성 스타일' 공통 성분이었다.
이걸 제거하려면 실제 사람 얼굴 쪽의 공통 성분(μ_real)도 알아야 하는데,
그건 실측 말고는 구할 방법이 없다. 즉 이 사진들은 검증용이 아니라 **엔진의 입력**이다.

두 가지 방법을 지원한다.

  1) 웹캠 촬영
        python scripts/capture_faces.py --label 홍길동
     3초 카운트다운 후 여러 장을 찍어 얼굴 신뢰도가 가장 높은 한 장만 남긴다.
     (opencv-headless라 미리보기 창은 없다. 카메라를 정면으로 보고 있으면 된다.)

  2) 기존 사진 넣기
     data/test_faces/ 아래에 아무 이름으로 넣어도 된다. 한 사람당 한 장이면 충분하다.

개인정보 — 이 사진들은 로컬에서만 쓰고 저장소에 올리지 않는다(.gitignore 처리).
전시에서 관람객 얼굴은 아예 디스크에 쓰지 않는다. 이건 개발용 표본이라 다르다.
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import cv2

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.face import FaceEngine  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "test_faces"

BURST = 7          # 연속 촬영 장수
BURST_GAP = 0.25   # 장당 간격(초)


def capture_one(cap, engine: FaceEngine, label: str, countdown: int):
    """카운트다운 후 연속 촬영해서 얼굴 신뢰도가 가장 높은 한 장만 남긴다."""
    print(f"\n{label} — 카메라를 정면으로 봐 주세요.")
    for i in range(countdown, 0, -1):
        print(f"  {i}...", flush=True)
        time.sleep(1)
    print("  촬영 중", flush=True)

    best = None  # (confidence, frame)
    for _ in range(BURST):
        ok, frame = cap.read()
        if not ok:
            continue
        dets = engine.detect(frame)
        if dets:
            # 뒤에 선 사람이 함께 잡히면 표본이 오염된다. 한 명일 때만 받는다.
            if len(dets) > 1:
                print(f"  ⚠ 얼굴 {len(dets)}개 — 한 분만 서 주세요")
                continue
            if best is None or dets[0].confidence > best[0]:
                best = (dets[0].confidence, frame.copy())
        time.sleep(BURST_GAP)
    return best


def sample_count() -> int:
    return sum(len(list(OUT.glob(f"*{e}"))) for e in (".png", ".jpg", ".jpeg"))


def next_label(prefix: str) -> str:
    """p01, p02 … 이미 있는 번호 다음을 고른다."""
    used = {p.stem for p in OUT.glob("*") if p.stem.startswith(prefix)}
    n = 1
    while f"{prefix}{n:02d}" in used:
        n += 1
    return f"{prefix}{n:02d}"


def main() -> None:
    ap = argparse.ArgumentParser(description="분포 테스트용 얼굴 사진 촬영")
    ap.add_argument("--label", help="파일 이름에 쓸 식별자 (예: p01). --session 이면 자동")
    ap.add_argument("--session", action="store_true",
                    help="여러 명을 이어서 촬영한다. 카메라를 열어 둔 채 반복해 훨씬 빠르다")
    ap.add_argument("--prefix", default="p", help="--session 자동 번호의 접두사 (기본 p)")
    ap.add_argument("--camera", type=int, default=0, help="카메라 인덱스 (기본 0)")
    ap.add_argument("--countdown", type=int, default=3, help="촬영 전 대기 초")
    args = ap.parse_args()

    if not args.session and not args.label:
        raise SystemExit("--label 을 주거나 --session 을 쓸 것.")

    OUT.mkdir(parents=True, exist_ok=True)
    engine = FaceEngine()

    cap = cv2.VideoCapture(args.camera)
    if not cap.isOpened():
        # 맥에서 흔한 함정 — 키오스크(브라우저)는 카메라가 되는데 여기만 막힌다.
        # 브라우저와 터미널이 각각 따로 권한을 받기 때문이다.
        raise SystemExit(
            f"카메라 {args.camera} 를 열 수 없다.\n\n"
            "  맥이라면 시스템 설정 → 개인정보 보호 및 보안 → 카메라 에서\n"
            "  터미널(또는 iTerm)을 켜고, 터미널을 완전히 껐다 다시 열 것.\n"
            "  키오스크 화면에서 카메라가 되는 것과는 별개다 — 권한이 앱마다 따로다.\n\n"
            "  촬영이 여의치 않으면 사진을 직접 넣어도 된다:\n"
            f"    {OUT.relative_to(ROOT)}/ 에 한 사람당 한 장 (정면·얼굴 하나)\n"
        )

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    saved = 0
    try:
        # 자동 노출·화이트밸런스가 안정될 때까지 몇 장 버린다.
        for _ in range(10):
            cap.read()

        if not args.session:
            best = capture_one(cap, engine, args.label, args.countdown)
            if best is None:
                raise SystemExit("얼굴을 찾지 못했다. 조명을 밝게 하고 다시 시도할 것.")
            conf, frame = best
            cv2.imwrite(str(OUT / f"{args.label}.png"), frame)
            print(f"\n저장 {args.label}.png  (얼굴 신뢰도 {conf:.3f})")
            saved = 1
        else:
            # 카메라를 닫지 않고 반복한다 — 한 명마다 다시 열면 초기화에 1~2초씩 걸린다.
            print("\n한 명씩 이어서 촬영한다. Enter=촬영, q+Enter=종료")
            while True:
                label = next_label(args.prefix)
                if input(f"\n[{sample_count()}명 수집됨] {label} 준비되면 Enter > ").strip().lower() == "q":
                    break
                best = capture_one(cap, engine, label, args.countdown)
                if best is None:
                    print("  ❌ 얼굴을 찾지 못했다 — 조명을 밝게 하고 다시. 번호는 유지된다.")
                    continue
                conf, frame = best
                cv2.imwrite(str(OUT / f"{label}.png"), frame)
                print(f"  ✅ 저장 {label}.png  (신뢰도 {conf:.3f})")
                saved += 1
    except (KeyboardInterrupt, EOFError):
        print("\n중단됨.")
    finally:
        cap.release()

    n = sample_count()
    print(f"\n이번에 {saved}명 촬영. 현재 표본 {n}명.")
    if n < 10:
        print(f"  방향 판단까지 {10 - n}명 남았다.")
    elif n < 40:
        print(f"  방향 판단은 가능하다. 확정(캐릭터당 5명)까지 {40 - n}명 남았다.")
    else:
        print("  확정 기준 40명을 채웠다.")
    print("\n다음: ./.venv/bin/python scripts/distribution_test.py --save")


if __name__ == "__main__":
    main()
