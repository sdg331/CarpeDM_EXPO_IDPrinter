"""출력 계층 — screen / escpos / cups 세 백엔드를 환경변수 하나로 전환한다.

    KIOSK_PRINT=screen   기본. 메모리에 잠시 보관하는 미리보기 (실물 출력 아님)
    KIOSK_PRINT=escpos   ESC/POS USB 감열 프린터 (전시용, 파이)
    KIOSK_PRINT=cups     CUPS 대기열 (드라이버가 CUPS 로 잡히는 프린터)

왜 계층을 두나 — 프린터가 없는 맥에서도 발급 흐름 전체(/api/issue)가 끝까지
돌아야 프론트를 붙여볼 수 있다. 실제 출력 실패는 오류로 반환하며
미리보기 성공으로 바꾸지 않는다. 장치/대기열 제출은 용지 배출 확인을 뜻하지 않는다.

escpos 백엔드는 하드웨어 없이는 검증할 수 없다 — 프린터가 확보되면
RUN.md 의 5단계 점검 절차대로 실기에서 확인할 것.
"""

from __future__ import annotations

import os
from io import BytesIO
import subprocess
import shutil
import tempfile
from pathlib import Path

from PIL import Image

from backend.profile import ProfileStore

ROOT = Path(__file__).resolve().parent.parent

PREVIEWS = ProfileStore(
    ttl_seconds=int(os.getenv("KIOSK_PREVIEW_TTL_SECONDS", "300")), max_items=8,
)


class PrintError(Exception):
    """Only failures known to occur before device access are safe to retry."""

    def __init__(self, detail: str, *, retryable: bool = False):
        super().__init__(detail)
        self.retryable = retryable


def backend_name() -> str:
    return os.getenv("KIOSK_PRINT", "screen").strip().lower()


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
    raise PrintError(f"모르는 출력 백엔드: {b} (screen/escpos/cups)", retryable=True)


def printer_status() -> dict:
    """운영 점검용 — /api/health 에 실린다. 무거운 검사는 하지 않는다."""
    b = backend_name()
    if b == "screen":
        return {"backend": b, "ready": True,
                "physicalOutput": False, "completionConfirmed": False,
                "detail": "메모리 미리보기 (실물 출력 없음)"}
    if b == "escpos":
        try:
            import escpos  # noqa: F401
            return {"backend": b, "ready": bool(os.getenv("KIOSK_ESCPOS_VENDOR") and os.getenv("KIOSK_ESCPOS_PRODUCT")), "physicalOutput": True, "completionConfirmed": False, "detail": "설정 상태만 확인; USB/용지 상태는 실물 확인 필요"}
        except ImportError:
            return {"backend": b, "ready": False,
                    "detail": "python-escpos 미설치 — pip install -r requirements-hardware.txt"}
    if b == "cups":
        return {"backend": b, "ready": shutil.which("lp") is not None, "physicalOutput": True, "completionConfirmed": False,
                "detail": f"lp -d {os.getenv('KIOSK_CUPS_PRINTER', '(기본 프린터)')}"}
    return {"backend": b, "ready": False, "detail": "모르는 백엔드"}


# ---------- 백엔드 구현 ----------


def _screen(img: Image.Image) -> dict:
    data = BytesIO()
    img.save(data, format="PNG")
    preview_id = PREVIEWS.put(data.getvalue())
    return {
        "backend": "screen", "status": "preview", "physicalOutput": False,
        "completionConfirmed": False, "previewUrl": f"/api/print/previews/{preview_id}",
    }


def _escpos(img: Image.Image) -> dict:
    """ESC/POS USB. 벤더·프로덕트 ID는 `lsusb` 로 확인해 환경변수로 준다.

        KIOSK_ESCPOS_VENDOR=0x04b8 KIOSK_ESCPOS_PRODUCT=0x0e28
    """
    try:
        from escpos.printer import Usb
    except ImportError as exc:
        raise PrintError("python-escpos 미설치 — pip install -r requirements-hardware.txt", retryable=True) from exc

    vendor = os.getenv("KIOSK_ESCPOS_VENDOR")
    product = os.getenv("KIOSK_ESCPOS_PRODUCT")
    if not vendor or not product:
        raise PrintError("KIOSK_ESCPOS_VENDOR / KIOSK_ESCPOS_PRODUCT 를 지정할 것 (lsusb 로 확인)", retryable=True)

    p = Usb(int(vendor, 16), int(product, 16))
    try:
        p.image(img)
        p.cut()
    finally:
        p.close()
    return {"backend": "escpos", "status": "submitted", "physicalOutput": True, "completionConfirmed": False}


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
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        except FileNotFoundError as exc:
            raise PrintError("CUPS lp 명령을 찾을 수 없다", retryable=True) from exc
        if r.returncode != 0:
            raise PrintError(f"lp 실패: {r.stderr.strip()}")
    finally:
        Path(tmp).unlink(missing_ok=True)
    return {"backend": "cups", "printer": printer or "(기본)", "status": "submitted", "physicalOutput": True, "completionConfirmed": False}
