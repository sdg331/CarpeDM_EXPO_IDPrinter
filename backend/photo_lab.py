"""Explicitly enabled photo experiment: bounded memory input, no session or printing."""

import os

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import Response
from starlette.concurrency import run_in_threadpool

router = APIRouter(prefix="/api/experiments/photo")
MAX_BYTES = 8 * 1024 * 1024


def enabled():
    return os.getenv("KIOSK_PHOTO_LAB") == "1"


@router.get("/status")
def status():
    from backend.app import STATE
    return {"enabled": enabled(), "ready": enabled() and STATE.get("engine") is not None,
            "processing": "local_cv", "generatesFace": False, "generatesSuit": False,
            "externalUpload": False}


@router.post("/compose")
async def compose(request: Request):
    from backend.app import ENGINE_LOCK, STATE, _decode_frame, _error
    from backend.face import MultipleFacesError, NoFaceError
    from backend.profile import ProfileComposer, ProfileQualityError

    if not enabled():
        return _error("PHOTO_LAB_DISABLED", retryable=False, status_code=403)
    if request.headers.get("content-type", "").split(";", 1)[0].lower() not in {"image/jpeg", "image/png", "image/webp"}:
        return _error("INVALID_IMAGE", retryable=False, status_code=400)
    length = request.headers.get("content-length")
    if length:
        try:
            if not 0 <= int(length) <= MAX_BYTES:
                return _error("IMAGE_TOO_LARGE", retryable=False, status_code=413)
        except ValueError:
            return _error("INVALID_IMAGE", retryable=False, status_code=400)
    # No UploadFile/multipart parser: originals cannot spool to temporary disk.
    raw = bytearray()
    async for chunk in request.stream():
        if len(raw) + len(chunk) > MAX_BYTES:
            return _error("IMAGE_TOO_LARGE", retryable=False, status_code=413)
        raw.extend(chunk)
    if not raw:
        return _error("EMPTY_IMAGE", retryable=False, status_code=400)

    def generate():
        with ENGINE_LOCK:
            engine = STATE.get("engine")
            if engine is None:
                return None
            return ProfileComposer().generate(_decode_frame(raw), engine)

    try:
        png = await run_in_threadpool(generate)
    except NoFaceError:
        return _error("NO_PERSON", retryable=True, status_code=422)
    except MultipleFacesError:
        return _error("MULTIPLE_PEOPLE", retryable=True, status_code=422)
    except ProfileQualityError:
        return _error("PHOTO_QUALITY_FAILED", retryable=True, status_code=422)
    except HTTPException:
        raise
    except Exception:
        return _error("PHOTO_PROCESSING_FAILED", retryable=True, status_code=503)
    finally:
        raw.clear()
    if png is None:
        return _error("PHOTO_ENGINE_UNAVAILABLE", retryable=False, status_code=503)
    return Response(png, media_type="image/png", headers={"Cache-Control": "no-store, max-age=0"})
