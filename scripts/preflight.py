"""Read-only local readiness checks. Never captures a face or prints a page."""

from __future__ import annotations

import argparse
import importlib.util
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


def main() -> int:
    parser = argparse.ArgumentParser(description="기동 전 점검 (출력/촬영하지 않음)")
    parser.add_argument("--hardware", action="store_true", help="PC/SC 및 프린터 설정도 필수로 확인")
    args = parser.parse_args()
    try:
        from dotenv import load_dotenv
        load_dotenv(ROOT / ".env", override=False)
    except ImportError:
        print("FAIL 실행 의존성이 없습니다: pip install -r requirements.txt")
        return 1

    failures = []

    def check(label: str, ready: bool, hint: str = "") -> None:
        print(f"{'PASS' if ready else 'FAIL'} {label}" + (f" — {hint}" if hint else ""))
        if not ready:
            failures.append(label)

    check("Python 3.12 이상", sys.version_info >= (3, 12))
    modules = ("fastapi", "uvicorn", "cv2", "numpy", "PIL", "httpx", "multipart")
    for module in modules:
        check(f"모듈 {module}", importlib.util.find_spec(module) is not None)
    for filename, minimum in (("face_detection_yunet_2023mar.onnx", 100_000),
                              ("face_recognition_sface_2021dec.onnx", 30_000_000)):
        path = ROOT / "models" / filename
        check(filename, path.is_file() and path.stat().st_size >= minimum,
              "없으면 bash scripts/fetch_models.sh")
    expected = [f"char_{i:02d}" for i in range(1, 9)]
    prototype_path = ROOT / "assets/prototypes.npz"
    if importlib.util.find_spec("numpy") and prototype_path.is_file():
        import numpy as np
        try:
            with np.load(prototype_path, allow_pickle=False) as data:
                ready = data["ids"].tolist() == expected and data["vectors"].shape == (8, 128)
        except (OSError, ValueError, KeyError):
            ready = False
    else:
        ready = False
    check("8명 캐릭터 프로토타입", ready, "불일치 시 scripts/build_prototypes.py 실행")
    check("8개 컬러·미리보기·인쇄 자산", all(
        (ROOT / f"assets/characters/{cid}.{ext}").is_file()
        for cid in expected for ext in ("png", "webp")
    ) and all((ROOT / f"assets/characters/print/{cid}_print.png").is_file() for cid in expected))
    if importlib.util.find_spec("PIL"):
        from backend.badge import BadgeError, _font_path
        try:
            _font_path()
            check("한글 인쇄 폰트", True)
        except BadgeError:
            check("한글 인쇄 폰트", False, "Pi: sudo apt install fonts-noto-cjk")

    if args.hardware:
        from backend.nfc import nfc_status
        status = nfc_status()
        check("실제 NFC 리더", status.get("backend") == "pcsc" and bool(status.get("ready")),
              "KIOSK_NFC=pcsc, PC/SC 서비스와 리더 연결 확인")
        printer = os.getenv("KIOSK_PRINT", "screen")
        if printer == "escpos":
            check("ESC/POS 드라이버", importlib.util.find_spec("escpos") is not None)
            check("USB 장치 ID 설정", bool(os.getenv("KIOSK_ESCPOS_VENDOR") and os.getenv("KIOSK_ESCPOS_PRODUCT")))
        elif printer == "cups":
            import shutil
            check("CUPS 명령", shutil.which("lp") is not None)
        else:
            check("실물 출력 설정", False, "screen은 미리보기입니다. escpos 또는 cups를 설정하세요")
        print("NOTE 위 점검은 실물 출력·커터·용지 상태 검증을 대체하지 않습니다.")
    else:
        print("NOTE 장치 연결 점검은 --hardware 옵션을 사용하세요.")
    print("NOTE 실제 AI 품질·카메라 권한·터치·MirrorTing 연결은 시연에서 확인하세요.")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
