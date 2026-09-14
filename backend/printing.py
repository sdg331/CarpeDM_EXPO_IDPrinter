"""출력 계층 — screen / escpos / cups 세 백엔드를 환경변수 하나로 전환한다.

    KIOSK_PRINT=screen   기본. 파일로 저장만 한다 (개발·8/1 데모용)
    KIOSK_PRINT=escpos   ESC/POS USB 감열 프린터 (전시용, 파이)
    KIOSK_PRINT=cups     CUPS 대기열 (드라이버가 CUPS 로 잡히는 프린터)

왜 계층을 두나 — 프린터가 없는 맥에서도 발급 흐름 전체(/api/issue)가 끝까지
돌아야 프론트를 붙여볼 수 있고, 전시 중 프린터가 죽어도 오류를 한 곳에서 잡아
화면 폴백으로 넘길 수 있다.

escpos 백엔드는 하드웨어 없이는 검증할 수 없다 — 프린터가 확보되면
RUN.md 의 5단계 점검 절차대로 실기에서 확인할 것.
"""

from __future__ import annotations

import os
import subprocess
import tempfile
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent

# screen 백엔드의 저장 위치. 마지막 한 장만 남기고 덮어쓴다 —
# 배지에는 이름이 들어가므로(PII) 발급 이력을 파일로 쌓지 않는다.
SCREEN_OUT = ROOT / "data" / "last_badge.png"


class PrintError(Exception):
    """출력 실패 — 호출자는 이걸 잡아 화면 폴백으로 넘긴다."""


def backend_name() -> str:
    return os.getenv("KIOSK_PRINT", "screen")


def print_badge(img: Image.Image) -> dict:
    """배지 이미지를 현재 백엔드로 내보낸다. 실패는 전부 PrintError 로 승격."""
    b = backend_name()
    try:
        if b == "screen":
            return _screen(img)
        if b == "escpos":
            return _escpos(img)
        if b == "cups":
            return _cups(img)
    except PrintError:
        raise
    except Exception as exc:                       # USB 단선·권한 등 무엇이든
        raise PrintError(f"{b} 출력 실패: {exc}") from exc
    raise PrintError(f"모르는 출력 백엔드: {b} (screen/escpos/cups)")


def printer_status() -> dict:
    """운영 점검용 — /api/health 에 실린다. 무거운 검사는 하지 않는다."""
    b = backend_name()
    if b == "screen":
        return {"backend": b, "ready": True,
                "detail": f"파일 저장 ({SCREEN_OUT.relative_to(ROOT)})"}
    if b == "escpos":
        try:
            import escpos  # noqa: F401
            return {"backend": b, "ready": True, "detail": "escpos 모듈 로드됨"}
        except ImportError:
            return {"backend": b, "ready": False,
                    "detail": "python-escpos 미설치 — requirements.txt 주석 해제"}
    if b == "cups":
        return {"backend": b, "ready": True,
                "detail": f"lp -d {os.getenv('KIOSK_CUPS_PRINTER', '(기본 프린터)')}"}
    return {"backend": b, "ready": False, "detail": "모르는 백엔드"}


# ---------- 백엔드 구현 ----------


def _screen(img: Image.Image) -> dict:
    SCREEN_OUT.parent.mkdir(parents=True, exist_ok=True)
    img.save(SCREEN_OUT)
    return {"backend": "screen", "path": str(SCREEN_OUT.relative_to(ROOT))}


def _escpos(img: Image.Image) -> dict:
    """ESC/POS USB. 벤더·프로덕트 ID는 `lsusb` 로 확인해 환경변수로 준다.

        KIOSK_ESCPOS_VENDOR=0x04b8 KIOSK_ESCPOS_PRODUCT=0x0e28
    """
    try:
        from escpos.printer import Usb
    except ImportError as exc:
        raise PrintError("python-escpos 미설치 — requirements.txt 주석 해제") from exc

    vendor = os.getenv("KIOSK_ESCPOS_VENDOR")
    product = os.getenv("KIOSK_ESCPOS_PRODUCT")
    if not vendor or not product:
        raise PrintError("KIOSK_ESCPOS_VENDOR / KIOSK_ESCPOS_PRODUCT 를 지정할 것 (lsusb 로 확인)")

    p = Usb(int(vendor, 16), int(product, 16))
    try:
        p.image(img)
        p.cut()
    finally:
        p.close()
    return {"backend": "escpos"}


def _cups(img: Image.Image) -> dict:
    """CUPS 대기열. KIOSK_CUPS_PRINTER 미지정이면 기본 프린터."""
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        img.save(f.name)
        tmp = f.name
    cmd = ["lp"]
    printer = os.getenv("KIOSK_CUPS_PRINTER")
    if printer:
        cmd += ["-d", printer]
    cmd.append(tmp)
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        if r.returncode != 0:
            raise PrintError(f"lp 실패: {r.stderr.strip()}")
    finally:
        Path(tmp).unlink(missing_ok=True)
    return {"backend": "cups", "printer": printer or "(기본)"}
