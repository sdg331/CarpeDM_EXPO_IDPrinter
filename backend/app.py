"""FastAPI backend for the 4-Fit MirrorTing employee-badge kiosk.

Port 8002 is used because 8000/8001 are reserved by other EXPO services.

Privacy:
- captured frames are processed in memory only;
- raw face images and embeddings are never written to the local session DB;
- pending thermal print images stay in the private DB until submission or expiry;
- card UID/session mappings stay on the kiosk.

Run:
    ./.venv/bin/uvicorn backend.app:app --host 127.0.0.1 --port 8002 --reload
"""

from __future__ import annotations

import asyncio
import hashlib
import ipaddress
import os
import re
import secrets
import sqlite3
import threading
from contextlib import suppress
from io import BytesIO
from urllib.parse import urlsplit
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated, Literal

import cv2
import numpy as np
from fastapi import FastAPI, File, Form, Header, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.exceptions import RequestValidationError
from starlette.concurrency import run_in_threadpool
from PIL import Image, UnidentifiedImageError
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from backend.badge import BadgeError, render_badge
from backend.career_tips import career_tip
from backend.face import (
    FaceEngine,
    MultipleFacesError,
    NoFaceError,
    Prototypes,
    display_scores,
)
from backend.nfc import NfcError, nfc_status, read_card_uid
from backend.printing import PREVIEWS, PrintError, print_badge, printer_status
from backend.profile import ProfileComposer, ProfileQualityError, ProfileStore
from backend.photo_lab import router as photo_lab_router
from backend.reports import ReportError, fetch_mirrorting_report, render_report
from backend.souvenir import introduction_url, qr_image, render_souvenir
from backend.store import (
    TEAM_LABELS,
    KioskStore,
    OperationConflict,
    SessionNotFound,
    StoreError,
)

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
FRONTEND = ROOT / "frontend"
PROTO_PATH = ASSETS / "prototypes.npz"
DOMAIN_PATH = ASSETS / "domain_mean.npz"

TEMPERATURE = float(os.getenv("KIOSK_TEMPERATURE", "0.08"))
MAX_UPLOAD = 8 * 1024 * 1024
NFC_TIMEOUT_SECONDS = float(os.getenv("KIOSK_NFC_TIMEOUT", "10"))

STATE: dict = {}
STORE = KioskStore()
ENGINE_LOCK = threading.RLock()
NFC_LOCK = threading.Lock()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """One model instance; raw frames in memory and pending receipts in private storage."""
    STORE.init()
    STORE.recover_interrupted_operations()
    retention_hours = float(os.getenv("KIOSK_SESSION_RETENTION_HOURS", "24"))
    STORE.purge_expired(retention_hours)
    try:
        STATE["engine"] = FaceEngine()
    except (OSError, RuntimeError, FileNotFoundError, cv2.error):
        STATE["engine"] = None
    try:
        STATE["proto"] = Prototypes.load(PROTO_PATH)
    except (OSError, ValueError):
        STATE["proto"] = None
    STATE["profiles"] = ProfileStore(
        ttl_seconds=int(os.getenv("KIOSK_PROFILE_TTL_SECONDS", "600")),
        max_items=int(os.getenv("KIOSK_PROFILE_MAX_ITEMS", "8")),
    )
    STATE["profile_composer"] = ProfileComposer()
    STATE["souvenirs"] = ProfileStore(ttl_seconds=600, max_items=8)
    STATE["mu_real"] = None
    STATE["mu_real_n"] = 0
    if DOMAIN_PATH.exists():
        with np.load(DOMAIN_PATH) as z:
            STATE["mu_real"] = z["mu_real"].astype(np.float32)
            STATE["mu_real_n"] = int(z["sample_size"][0])

    async def prune_images():
        while True:
            await asyncio.sleep(15)
            STATE["profiles"].prune()
            STATE["souvenirs"].prune()
            PREVIEWS.prune()
            await run_in_threadpool(STORE.purge_expired, retention_hours)

    task = asyncio.create_task(prune_images())
    try:
        yield
    finally:
        task.cancel()
        with suppress(asyncio.CancelledError):
            await task
        STATE["profiles"].clear()
        STATE["souvenirs"].clear()
        PREVIEWS.clear()
        STATE.clear()


app = FastAPI(title="4-Fit MirrorTing 사원증 키오스크", lifespan=lifespan)


@app.middleware("http")
async def same_origin_and_privacy(request: Request, call_next):
    # The visitor browser lives on this kiosk. Only the authenticated bridge
    # may be reached from another device; forwarded headers are never trusted.
    if request.url.path.startswith('/api/') and not request.url.path.startswith('/api/integrations/mirrorting/'):
        try:
            address = ipaddress.ip_address(request.client.host) if request.client else None
            local = address is not None and (address.is_loopback or bool(getattr(address, 'ipv4_mapped', None) and address.ipv4_mapped.is_loopback))
        except ValueError:
            local = False
        if not local:
            return _error('LOCAL_ACCESS_REQUIRED', retryable=False, status_code=403)
    # A third-party page must not issue a badge or bind a card on localhost.
    origin = request.headers.get("origin")
    if request.method not in {"GET", "HEAD", "OPTIONS"} and origin:
        if urlsplit(origin).netloc != request.url.netloc:
            return _error("ORIGIN_NOT_ALLOWED", retryable=False, status_code=403)
    response = await call_next(request)
    # Always load the current HTML entrypoint; its versioned assets may change.
    if request.url.path.startswith("/api/") or request.url.path == "/" or request.url.path.endswith(".html"):
        response.headers["Cache-Control"] = "no-store, max-age=0"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "same-origin"
    return response


def _error(
    code: str,
    *,
    retryable: bool,
    status_code: int,
    detail: str | None = None,
    operation_id: str | None = None,
) -> JSONResponse:
    payload: dict = {
        "ok": False,
        "error": {
            "code": code,
            "retryable": retryable,
        },
    }
    if operation_id:
        payload["error"]["operationId"] = operation_id
    return JSONResponse(status_code=status_code, content=payload)


@app.exception_handler(HTTPException)
async def http_error(request: Request, exc: HTTPException):
    code = exc.detail if isinstance(exc.detail, str) and re.fullmatch(r'[A-Z_]+', exc.detail) else 'REQUEST_FAILED'
    return _error(code, retryable=exc.status_code >= 500, status_code=exc.status_code)


@app.exception_handler(RequestValidationError)
async def invalid_request(request: Request, exc: RequestValidationError):
    # Do not echo visitor names or bridge capabilities in validation payloads.
    return _error('INVALID_REQUEST', retryable=False, status_code=422)


def char_meta() -> list[dict]:
    p: Prototypes | None = STATE.get("proto")
    if p is None:
        return []
    return [
        {
            "id": cid,
            "no": cid.replace("char_", ""),
            "group": group,
            "image": f"/assets/characters/{cid}.png",
        }
        for cid, group in zip(p.ids, p.groups)
    ]


@app.get("/api/health")
def health() -> dict:
    p = STATE.get("proto")
    engine_ready = STATE.get("engine") is not None
    return {
        "ok": engine_ready and p is not None,
        "models": {"yunet": engine_ready, "sface": engine_ready,
                   "profile_composite": engine_ready and STATE.get("profile_composer") is not None},
        "characters": len(p.ids) if p else 0,
        "style_set_n": p.style_n if p else 0,
        "mu_real_n": STATE.get("mu_real_n", 0),
        "calibrated": STATE.get("mu_real") is not None,
        "temperature": TEMPERATURE,
        "printer": printer_status(), "nfc": nfc_status(), "database": STORE.health(),
        "max_pair": float(_max_pair()) if p and len(p.ids) > 1 else None,
        "profile": {"engine": "local_cv", "changesClothes": False, "externalUpload": False},
        "mirrorting": {"configured": bool(os.getenv('KIOSK_MIRRORTING_URL')) and len(os.getenv('KIOSK_BRIDGE_TOKEN', '')) >= 32},
        "souvenir": {"configured": _souvenir_configured(), "externalUpload": False},
    }


def _max_pair() -> float:
    r = STATE["proto"].residuals()
    m = r @ r.T
    return m[np.triu_indices(len(m), 1)].max()


async def _frame_bytes(frame: UploadFile) -> bytes:
    data = await frame.read(MAX_UPLOAD + 1)
    if not data:
        raise HTTPException(400, "EMPTY_IMAGE")
    if len(data) > MAX_UPLOAD:
        raise HTTPException(413, "IMAGE_TOO_LARGE")
    return data


def _decode_frame(raw: bytes) -> np.ndarray:
    # Reject decompression bombs before OpenCV allocates the full image.
    try:
        with Image.open(BytesIO(raw)) as header:
            if header.format not in {"JPEG", "PNG", "WEBP"}:
                raise HTTPException(400, "INVALID_IMAGE")
            width, height = header.size
            if width * height > 12_000_000 or min(width, height) < 16:
                raise HTTPException(413, "IMAGE_DIMENSIONS_INVALID")
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError):
        raise HTTPException(400, "INVALID_IMAGE") from None
    image = cv2.imdecode(np.frombuffer(raw, np.uint8), cv2.IMREAD_COLOR)
    if image is None:
        raise HTTPException(400, "INVALID_IMAGE")
    return image


def _detect_frame(raw: bytes):
    with ENGINE_LOCK:
        engine = STATE.get("engine")
        if engine is None:
            raise HTTPException(503, "PROFILE_ENGINE_UNAVAILABLE")
        return engine.detect(_decode_frame(raw))


@app.get("/api/characters")
def characters() -> dict:
    return {"characters": char_meta()}


@app.post("/api/detect")
async def detect(frame: UploadFile = File(...)) -> dict:
    """Preview-only face count. SFace embedding is deliberately skipped."""
    raw = await _frame_bytes(frame)
    dets = await run_in_threadpool(_detect_frame, raw)
    return {
        "ok": len(dets) == 1,
        "count": len(dets),
        "confidence": round(float(dets[0].confidence), 3) if dets else 0.0,
    }


@app.post("/api/match")
async def match(frame: UploadFile = File(...)) -> dict:
    """One captured frame -> current-character relative scores. Image is not saved."""
    raw = await _frame_bytes(frame)
    proto = STATE.get("proto")
    if proto is None:
        return _error("AI_UNAVAILABLE", retryable=True, status_code=503)
    t0 = time.perf_counter()
    def infer():
        with ENGINE_LOCK:
            engine = STATE.get("engine")
            if engine is None:
                raise HTTPException(503, "AI_UNAVAILABLE")
            return engine.embed_single(_decode_frame(raw), strict=True)
    try:
        emb, det = await run_in_threadpool(infer)
    except NoFaceError:
        return {"ok": False, "error": "no_face"}
    except MultipleFacesError as exc:
        return {"ok": False, "error": "multiple_faces", "count": exc.count}
    scores = proto.match_scores(emb, STATE.get("mu_real"))
    display = display_scores(scores, TEMPERATURE)
    top = int(np.argmax(scores))
    order = np.argsort(scores)[::-1]
    elapsed = (time.perf_counter() - t0) * 1000

    return {
        "ok": True,
        "top": top,
        "characters": char_meta(),
        "display": [round(float(v) * 100, 1) for v in display],
        "order": [int(i) for i in order],
        "raw": [round(float(v), 4) for v in scores],
        "margin": round(float(scores[order[0]] - scores[order[1]]), 4),
        "confidence": round(float(det.confidence), 3),
        "elapsed_ms": round(elapsed, 1),
        "calibrated": STATE.get("mu_real") is not None,
    }


def _profile_response(profile_id: str, elapsed_ms: float, *, reused: bool) -> dict:
    url = f"/api/profile/{profile_id}/image"
    return {"ok": True, "kind": "B", "profileId": profile_id, "image": url,
            "previewUrl": url, "elapsedMs": round(elapsed_ms, 1), "reused": reused,
            "expiresInSeconds": STATE["profiles"].ttl_seconds}


def _compose_profile(raw: bytes, operation_id: str):
    fingerprint = hashlib.sha256(raw).hexdigest()
    with ENGINE_LOCK:
        profiles = STATE.get("profiles")
        engine = STATE.get("engine")
        composer = STATE.get("profile_composer")
        if profiles is None or engine is None or composer is None:
            return _error("PROFILE_ENGINE_UNAVAILABLE", retryable=True, status_code=503)
        try:
            previous = profiles.find_operation(operation_id, fingerprint)
        except ValueError:
            return _error("OPERATION_CONFLICT", retryable=False, status_code=409)
        if previous:
            return _profile_response(previous, 0, reused=True)
        started = time.perf_counter()
        try:
            png = composer.generate(_decode_frame(raw), engine)
        except NoFaceError:
            return _error("NO_PERSON", retryable=True, status_code=422)
        except MultipleFacesError:
            return _error("MULTIPLE_PEOPLE", retryable=True, status_code=422)
        except ProfileQualityError:
            return _error("PROFILE_QUALITY_FAILED", retryable=True, status_code=422)
        except (cv2.error, OSError, ValueError):
            return _error("PROFILE_COMPOSITE_FAILED", retryable=True, status_code=500)
        profile_id = profiles.put(png, operation_id, fingerprint=fingerprint)
        return _profile_response(profile_id, (time.perf_counter() - started) * 1000, reused=False)


@app.post("/api/profile")
@app.post("/api/profile/generate")
async def generate_profile(frame: UploadFile = File(...), operationId: str = Form(...)):
    if not isinstance(operationId, str) or not 8 <= len(operationId) <= 128:
        return _error("INVALID_OPERATION_ID", retryable=False, status_code=400)
    return await run_in_threadpool(_compose_profile, await _frame_bytes(frame), operationId)


@app.get("/api/profile/{profile_id}/image")
def profile_image(profile_id: str):
    profiles = STATE.get("profiles")
    png = profiles.get(profile_id) if profiles is not None else None
    if png is None:
        return _error("PROFILE_EXPIRED", retryable=True, status_code=410)
    return Response(png, media_type="image/png", headers={"Cache-Control": "no-store, max-age=0"})


@app.delete("/api/profile/{profile_id}")
def delete_profile(profile_id: str):
    profiles = STATE.get("profiles")
    if profiles is not None:
        profiles.delete(profile_id)
    return {"ok": True}


@app.get("/api/print/previews/{preview_id}")
def print_preview(preview_id: str):
    png = PREVIEWS.get(preview_id)
    if png is None:
        return _error("PREVIEW_EXPIRED", retryable=False, status_code=410)
    return Response(png, media_type="image/png", headers={"Cache-Control": "no-store, max-age=0"})


class MatchResultPayload(BaseModel):
    kind: Literal["A", "B"]
    characterId: str | None = None
    profileId: str | None = None


class NfcRegisterRequest(BaseModel):
    operationId: str = Field(min_length=8, max_length=128)
    name: str = Field(min_length=1, max_length=10)
    teamId: str = Field(min_length=1, max_length=32)
    aiMode: Literal["A", "B"]
    result: MatchResultPayload


class OperationRequest(BaseModel):
    operationId: str = Field(min_length=8, max_length=128)
    purpose: Literal["checkout", "souvenir"] = "checkout"


def _souvenir_card() -> str:
    uid = re.sub(r"[\s:-]", "", os.getenv("KIOSK_SOUVENIR_CARD_UID", "")).upper()
    return uid if re.fullmatch(r"(?:[0-9A-F]{2}){4,10}", uid) else ""


def _souvenir_configured() -> bool:
    try:
        introduction_url(os.getenv("KIOSK_SOUVENIR_QR_URL", ""))
        return bool(_souvenir_card())
    except ValueError:
        return False


def _souvenir_pass(photo_pass: str) -> dict:
    return {"ok": True, "kind": "souvenir", "photoPass": photo_pass,
            "printJobId": f"souvenir-{photo_pass}", "qrPreviewUrl": f"/api/souvenirs/{photo_pass}/qr"}


class BadgePrintRequest(BaseModel):
    operationId: str = Field(min_length=8, max_length=128)
    sessionId: str = Field(min_length=1, max_length=32)


def _validate_registration(req: NfcRegisterRequest, *, require_profile: bool = True):
    if req.teamId not in TEAM_LABELS:
        return _error("INVALID_TEAM", retryable=False, status_code=400)
    if not req.name.strip() or any(ord(ch) < 32 for ch in req.name):
        return _error("INVALID_NAME", retryable=False, status_code=400)
    if req.result.kind != req.aiMode:
        return _error("INVALID_AI_RESULT", retryable=False, status_code=400)
    if req.aiMode == "A":
        proto = STATE.get("proto")
        if not proto or req.result.characterId not in proto.ids or req.result.profileId:
            return _error("INVALID_AI_RESULT", retryable=False, status_code=400)
        return req.result.characterId, None
    if not req.result.profileId or req.result.characterId:
        return _error("INVALID_AI_RESULT", retryable=False, status_code=400)
    profiles = STATE.get("profiles")
    if require_profile and (profiles is None or profiles.get(req.result.profileId) is None):
        return _error("PROFILE_EXPIRED", retryable=True, status_code=410)
    return None, req.result.profileId


def _previous_operation(op):
    if op["status"] == "success" and op["result"]:
        return {"ok": True, **op["result"]}
    code = "OPERATION_IN_PROGRESS" if op["status"] == "running" else op["error_code"] or "UNKNOWN_OUTCOME"
    return _error(code, retryable=bool(op["retryable"]), status_code=409, operation_id=op["operation_id"])


@app.post("/api/nfc/register")
def register_nfc(req: NfcRegisterRequest):
    """One durable operation/session per request; safely bind the NFC UID."""
    try:
        previous = STORE.get_operation(req.operationId, "nfc_register")
        validated = _validate_registration(req, require_profile=not (previous and previous['status'] == 'success'))
        if isinstance(validated, JSONResponse):
            return validated
        char_id, profile_id = validated
        session = STORE.create_session(
            name=req.name, team_id=req.teamId, ai_mode=req.aiMode,
            char_id=char_id, profile_id=profile_id, operation_id=req.operationId,
        )
        session_id = session['session_id']
        if not session['claimed']:
            op = STORE.get_operation(req.operationId, "nfc_register")
            binding = STORE.binding_for_operation(req.operationId)
            if binding:
                result = {'status': 'verified', 'sessionId': session_id, 'nfcBackend': nfc_status()['backend']}
                if not binding['active']:
                    return _error('SESSION_REPLACED', retryable=False, status_code=409)
                STORE.finish_operation(req.operationId, kind='nfc_register', status='success', result=result)
                return {'ok': True, **result}
            op = STORE.claim_operation(req.operationId, kind='nfc_register', session_id=session_id)
            if not op['claimed']:
                return _previous_operation(op)
        if profile_id:
            try:
                claimed = STATE['profiles'].claim(profile_id, session_id)
            except ValueError:
                STORE.finish_operation(req.operationId, kind='nfc_register', status='error', error_code='PROFILE_ALREADY_USED')
                return _error('PROFILE_ALREADY_USED', retryable=False, status_code=409)
            if not claimed:
                STORE.finish_operation(req.operationId, kind='nfc_register', status='retryable_error', error_code='PROFILE_EXPIRED', retryable=True)
                return _error('PROFILE_EXPIRED', retryable=True, status_code=410)
    except OperationConflict:
        return _error("OPERATION_CONFLICT", retryable=False, status_code=409)
    except ValueError:
        return _error("INVALID_SESSION", retryable=False, status_code=400)

    try:
        with NFC_LOCK:
            uid = read_card_uid(NFC_TIMEOUT_SECONDS)
    except NfcError as exc:
        STORE.finish_operation(req.operationId, kind="nfc_register",
            status="retryable_error" if exc.retryable else "error", error_code=exc.code, retryable=exc.retryable)
        return _error(exc.code, retryable=exc.retryable, status_code=408 if exc.code == 'NFC_TIMEOUT' else 503)
    try:
        if uid == _souvenir_card():
            STORE.finish_operation(req.operationId, kind="nfc_register", status="retryable_error", error_code="SOUVENIR_CARD", retryable=True)
            return _error("SOUVENIR_CARD", retryable=True, status_code=409)
        STORE.bind_card(session_id=session_id, card_uid=uid, operation_id=req.operationId)
    except Exception:
        STORE.finish_operation(req.operationId, kind="nfc_register", status="unknown", error_code="UNKNOWN_OUTCOME")
        return _error("UNKNOWN_OUTCOME", retryable=False, status_code=500)
    result = {"status": "verified", "sessionId": session_id, "nfcBackend": nfc_status()['backend']}
    STORE.finish_operation(req.operationId, kind="nfc_register", status="success", result=result)
    return {"ok": True, **result}


@app.post("/api/nfc/resolve")
def resolve_checkout(req: OperationRequest):
    """Read a card and resolve its currently active visitor session."""
    souvenirs = STATE.get("souvenirs")
    previous = souvenirs.find_operation(req.operationId) if souvenirs else None
    if previous:
        return _souvenir_pass(previous)
    try:
        with NFC_LOCK:
            uid = read_card_uid(NFC_TIMEOUT_SECONDS)
    except NfcError as exc:
        status = 408 if exc.code == "NFC_TIMEOUT" else 503
        return _error(
            exc.code,
            retryable=exc.retryable,
            status_code=status,
            detail=str(exc),
        )

    if uid == _souvenir_card():
        if STORE.unresolved_souvenir_print():
            return _error("SOUVENIR_PRINT_PENDING", retryable=False, status_code=409)
        if not _souvenir_configured() or souvenirs is None:
            return _error("SOUVENIR_NOT_CONFIGURED", retryable=False, status_code=503)
        url = os.getenv("KIOSK_SOUVENIR_QR_URL", "")
        try:
            qr_image(url)  # Fail before offering a photo if the configured QR cannot render.
        except (ValueError, cv2.error):
            return _error("SOUVENIR_NOT_CONFIGURED", retryable=False, status_code=503)
        return _souvenir_pass(souvenirs.put(url.encode("utf-8"), req.operationId))
    if req.purpose == "souvenir":
        return _error("SOUVENIR_CARD_REQUIRED", retryable=True, status_code=403)
    session = STORE.resolve_card(uid)
    if not session:
        return _error("UNKNOWN_CARD", retryable=True, status_code=404)

    return {
        "ok": True,
        "sessionId": session["session_id"],
        "name": session["name"],
        "teamId": session["team_id"],
    }


@app.get("/api/souvenirs/{photo_pass}/qr")
def souvenir_qr(photo_pass: str):
    grants = STATE.get("souvenirs")
    url = grants.get(photo_pass) if grants else None
    if url is None:
        return _error("SOUVENIR_PASS_EXPIRED", retryable=False, status_code=410)
    data = BytesIO()
    qr_image(url.decode("utf-8")).save(data, format="PNG")
    return Response(data.getvalue(), media_type="image/png", headers={"Cache-Control": "no-store"})


@app.delete("/api/souvenirs/{photo_pass}")
def delete_souvenir(photo_pass: str):
    grants = STATE.get("souvenirs")
    if grants:
        grants.delete(photo_pass)
    operation = STORE.get_operation(f"souvenir-{photo_pass}", "souvenir_print")
    preview = (operation or {}).get("result") or {}
    if preview.get("previewUrl", "").startswith("/api/print/previews/"):
        PREVIEWS.delete(preview["previewUrl"].rsplit("/", 1)[-1])
    return {"ok": True}


def _print_souvenir(photo_pass: str, raw: bytes):
    operation_id = f"souvenir-{photo_pass}"
    try:
        previous = STORE.get_operation(operation_id, "souvenir_print")
        if previous and previous["status"] != "retryable_error":
            return _previous_operation(previous)
        grants = STATE.get("souvenirs")
        url = grants.get(photo_pass) if grants else None
        if url is None:
            return _error("SOUVENIR_PASS_EXPIRED", retryable=False, status_code=410)
        bgr = _decode_frame(raw)
        photo = Image.fromarray(cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB))
        try:
            image = render_souvenir(photo, url.decode("utf-8"))
        except (BadgeError, OSError, ValueError, cv2.error):
            return _error("SOUVENIR_RENDER_FAILED", retryable=True, status_code=500)
        with STORE.card_access():
            if STORE.unresolved_souvenir_print():
                return _error("SOUVENIR_PRINT_PENDING", retryable=False, status_code=409)
            op = STORE.claim_operation(operation_id, kind="souvenir_print", session_id=None)
            if not op["claimed"]:
                return _previous_operation(op)
            return _submit_print(operation_id, "souvenir_print", image)
    except OperationConflict:
        return _error("OPERATION_CONFLICT", retryable=False, status_code=409)


@app.post("/api/souvenirs/{photo_pass}/print")
async def print_souvenir(photo_pass: str, frame: UploadFile = File(...)):
    if not re.fullmatch(r"p_[A-Za-z0-9_-]{24}", photo_pass):
        return _error("SOUVENIR_PASS_EXPIRED", retryable=False, status_code=410)
    return await run_in_threadpool(_print_souvenir, photo_pass, await _frame_bytes(frame))


class SessionProfileRequest(BaseModel):
    profileId: str = Field(min_length=8, max_length=128)


@app.post("/api/sessions/{session_id}/profile")
def replace_session_profile(session_id: str, req: SessionProfileRequest):
    """Recovery after an unprinted portrait expires; keep the registered card."""
    try:
        session = STORE.get_session(session_id)
    except SessionNotFound:
        return _error("SESSION_NOT_FOUND", retryable=False, status_code=404)
    operation = STORE.print_operation(session_id)
    if session['ai_mode'] != 'B' or not STORE.active_card(session_id):
        return _error('INVALID_SESSION', retryable=False, status_code=409)
    if operation and operation['status'] != 'retryable_error':
        return _error('PRINT_ALREADY_STARTED', retryable=False, status_code=409)
    profiles = STATE.get('profiles')
    try:
        if profiles is None or not profiles.claim(req.profileId, session_id):
            return _error('PROFILE_EXPIRED', retryable=True, status_code=410)
    except ValueError:
        return _error('PROFILE_ALREADY_USED', retryable=False, status_code=409)
    old_profile = session['profile_id']
    STORE.set_profile_result(session_id, profile_id=req.profileId)
    if old_profile and old_profile != req.profileId:
        profiles.delete(old_profile)
    return {'ok': True, 'sessionId': session_id, 'profileId': req.profileId}


def _print_result(printed: dict, operation_id: str) -> dict:
    physical = printed.get('backend') != 'screen'
    return {**printed, 'status': 'submitted' if physical else 'preview',
            'physicalOutput': physical, 'completionConfirmed': False, 'printJobId': operation_id}


def _submit_session_print(session_id: str, operation_id: str, kind: str, image, *, extra: dict | None = None):
    """Recheck identity at device submission while card rebinding is excluded."""
    with STORE.card_access():
        if not STORE.active_card(session_id):
            STORE.finish_operation(operation_id, kind=kind, status='error', error_code='SESSION_REPLACED')
            return _error('SESSION_REPLACED', retryable=False, status_code=409)
        return _submit_print(operation_id, kind, image, extra=extra)


def _submit_print(operation_id: str, kind: str, image, *, extra: dict | None = None):
    """Save the exact receipt before touching the device, including photo and QR."""
    try:
        data = BytesIO()
        image.save(data, format="PNG")
        STORE.save_print_payload(operation_id, data.getvalue(), extra)
    except (sqlite3.Error, OSError):
        STORE.finish_operation(operation_id, kind=kind, status="retryable_error", error_code="PRINT_QUEUE_UNAVAILABLE", retryable=True)
        return _error("PRINT_QUEUE_UNAVAILABLE", retryable=True, status_code=503)
    try:
        printed = print_badge(image)
    except PrintError as exc:
        code = "PRINT_UNAVAILABLE" if exc.retryable else "UNKNOWN_OUTCOME"
        STORE.finish_operation(operation_id, kind=kind, status="retryable_error" if exc.retryable else "unknown", error_code=code, retryable=exc.retryable)
        return _error(code, retryable=exc.retryable, status_code=503)
    result = {**_print_result(printed, operation_id), **(extra or {})}
    STORE.finish_operation(operation_id, kind=kind, status="success", result=result)
    return {"ok": True, **result}


@app.post("/api/badge/print")
def print_session_badge(req: BadgePrintRequest):
    """Atomic per-session print ownership; never automatically repeat unknown output."""
    try:
        session = STORE.get_session(req.sessionId)
    except SessionNotFound:
        return _error('SESSION_NOT_FOUND', retryable=False, status_code=404)
    previous = STORE.print_operation(req.sessionId)
    if not STORE.active_card(req.sessionId) and (not previous or previous['status'] == 'retryable_error'):
        return _error('SESSION_REPLACED', retryable=False, status_code=409)
    try:
        op = STORE.claim_operation(req.operationId, kind='badge_print', session_id=req.sessionId, unique_session=True)
    except OperationConflict:
        return _error('OPERATION_CONFLICT', retryable=False, status_code=409)
    if not op['claimed']:
        return _previous_operation(op)
    operation_id = op['operation_id']
    profile_png = None
    if session['ai_mode'] == 'B':
        profiles = STATE.get('profiles')
        profile_png = profiles.get(session['profile_id']) if profiles is not None else None
        if profile_png is None:
            STORE.finish_operation(operation_id, kind='badge_print', status='retryable_error', error_code='PROFILE_EXPIRED', retryable=True)
            return _error('PROFILE_EXPIRED', retryable=True, status_code=410)
    try:
        image = render_badge(session['name'], TEAM_LABELS[session['team_id']], session['char_id'], session['session_id'], profile_png=profile_png)
    except (BadgeError, OSError, ValueError):
        STORE.finish_operation(operation_id, kind='badge_print', status='retryable_error', error_code='BADGE_RENDER_FAILED', retryable=True)
        return _error('BADGE_RENDER_FAILED', retryable=True, status_code=500)
    response = _submit_session_print(req.sessionId, operation_id, 'badge_print', image)
    if isinstance(response, dict) and response.get('ok') and session['profile_id']:
        STATE['profiles'].delete(session['profile_id'])
    return response


def _bridge_authorized(token: str | None):
    expected = os.getenv('KIOSK_BRIDGE_TOKEN', '')
    if len(expected) < 32:
        return _error('INTEGRATION_PENDING', retryable=False, status_code=503)
    if not isinstance(token, str) or not secrets.compare_digest(token, expected):
        return _error('INTEGRATION_UNAUTHORIZED', retryable=False, status_code=403)
    return None


@app.get('/api/integrations/mirrorting/cards/{card_uid}')
def bridge_card(card_uid: str, x_bridge_token: str | None = Header(default=None)):
    denied = _bridge_authorized(x_bridge_token)
    if denied is not None:
        return denied
    uid = card_uid.strip().upper()
    if not re.fullmatch(r'[0-9A-F]{4,64}', uid) or len(uid) % 2:
        return _error('INVALID_CARD', retryable=False, status_code=400)
    session = STORE.resolve_card(uid)
    if session is None:
        return _error('UNKNOWN_CARD', retryable=True, status_code=404)
    return {'ok': True, 'sessionId': session['session_id'], 'cardUid': uid}


class MirrorTingLinkRequest(BaseModel):
    sessionId: str = Field(min_length=1, max_length=32)
    cardUid: str = Field(min_length=4, max_length=64, pattern=r'^[0-9A-Fa-f]+$')
    mirrorSessionId: int = Field(gt=0, strict=True)
    accessToken: str = Field(min_length=1, max_length=512)


@app.post('/api/integrations/mirrorting/link')
def bridge_link(req: MirrorTingLinkRequest, x_bridge_token: str | None = Header(default=None)):
    denied = _bridge_authorized(x_bridge_token)
    if denied is not None:
        return denied
    try:
        linked = STORE.link_mirrorting(session_id=req.sessionId, card_uid=req.cardUid,
            mirror_session_id=req.mirrorSessionId, access_token=req.accessToken)
    except OperationConflict:
        return _error('OPERATION_CONFLICT', retryable=False, status_code=409)
    except ValueError:
        return _error('INVALID_SESSION', retryable=False, status_code=400)
    return {'ok': True, 'status': 'linked', **linked}


def _report_error(exc: ReportError):
    status = {'REPORT_NOT_FOUND': 404, 'REPORT_PENDING': 409, 'REPORT_TIMEOUT': 504,
              'INTEGRATION_PENDING': 503, 'INTEGRATION_UNAUTHORIZED': 502, 'SESSION_REPLACED': 409}.get(exc.code, 502)
    return _error(exc.code, retryable=exc.retryable, status_code=status)


def _linked_report(session_id: str):
    session = STORE.get_session(session_id)
    if not STORE.active_card(session_id):
        raise ReportError('SESSION_REPLACED')
    if not os.getenv('KIOSK_MIRRORTING_URL'):
        raise ReportError('INTEGRATION_PENDING')
    link = STORE.get_mirrorting_link(session_id)
    if link is None:
        raise ReportError('REPORT_NOT_FOUND', retryable=True)
    report = fetch_mirrorting_report(session_id, link['mirror_session_id'], link['access_token'],
                                    base_url=os.getenv('KIOSK_MIRRORTING_URL', ''))
    # Upstream processing may outlast a new visitor's card registration.
    with STORE.card_access():
        if not STORE.active_card(session_id):
            raise ReportError('SESSION_REPLACED')
    return session, {**report, 'careerTip': career_tip(session_id)}


@app.get('/api/reports/{session_id}')
def get_report(session_id: str):
    try:
        _, report = _linked_report(session_id)
    except SessionNotFound:
        return _error('SESSION_NOT_FOUND', retryable=False, status_code=404)
    except ReportError as exc:
        return _report_error(exc)
    return {'ok': True, **report}


class ReportPrintRequest(BadgePrintRequest):
    reportId: str = Field(min_length=1, max_length=64)


@app.post('/api/reports/print')
def print_session_report(req: ReportPrintRequest):
    return _print_session_report(req)


@app.post('/api/reports/print-photo')
async def print_report_photo(
    operationId: str = Form(min_length=8, max_length=128),
    sessionId: str = Form(min_length=1, max_length=32),
    reportId: str = Form(min_length=1, max_length=64),
    frame: UploadFile = File(...),
):
    req = ReportPrintRequest(operationId=operationId, sessionId=sessionId, reportId=reportId)
    return await run_in_threadpool(_print_session_report, req, await _frame_bytes(frame))


def _print_session_report(req: ReportPrintRequest, raw_photo: bytes | None = None):
    try:
        original = STORE.get_operation(req.operationId, 'report_print')
        if original and original['session_id'] != req.sessionId:
            raise OperationConflict('print session changed')
        link = STORE.get_mirrorting_link(req.sessionId)
        if not link or req.reportId != str(link['mirror_session_id']):
            return _error('REPORT_NOT_FOUND', retryable=False, status_code=404)
        previous = original or STORE.print_operation(req.sessionId, 'report_print')
        if previous and previous['status'] != 'retryable_error':
            return _previous_operation(previous)
        session, report = _linked_report(req.sessionId)
        # Fetch/render before the irreversible claim: failures here cannot print.
        photo = None
        if raw_photo is not None:
            bgr = _decode_frame(raw_photo)
            photo = Image.fromarray(cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB))
        try:
            image = render_report(report, name=session['name'], team=TEAM_LABELS[session['team_id']],
                                  **({'photo': photo} if photo is not None else {}))
        except ReportError as exc:
            if exc.code != 'REPORT_RENDER_FAILED':
                raise
            return _error('REPORT_RENDER_FAILED', retryable=True, status_code=500)
        except (BadgeError, OSError, ValueError, TypeError):
            return _error('REPORT_RENDER_FAILED', retryable=True, status_code=500)
        op = STORE.claim_operation(req.operationId, kind='report_print', session_id=req.sessionId, unique_session=True)
    except OperationConflict:
        return _error('OPERATION_CONFLICT', retryable=False, status_code=409)
    except SessionNotFound:
        return _error('SESSION_NOT_FOUND', retryable=False, status_code=404)
    except ReportError as exc:
        return _report_error(exc)
    if not op['claimed']:
        return _previous_operation(op)
    operation_id = op['operation_id']
    return _submit_session_print(req.sessionId, operation_id, 'report_print', image, extra={'reportId': req.reportId})


@app.get("/api/print/recovery")
def pending_print_recovery():
    pending = []
    for row in STORE.pending_prints():
        active = row["kind"] == "souvenir_print" or bool(STORE.active_card(row["session_id"]))
        pending.append({"operationId": row["operation_id"], "kind": row["kind"], "status": row["status"],
                        "hasImage": bool(row["has_image"]), "recoverable": active and row["status"] != "running",
                        "revision": _print_revision(row)})
    return {"ok": True, "pending": pending}


def _print_revision(row: dict) -> str:
    value = f"{row['status']}:{row['updated_at']}:{row['resolution_count']}"
    return hashlib.sha256(value.encode()).hexdigest()


class PrintRecoveryRequest(BaseModel):
    operationId: str = Field(min_length=8, max_length=128)
    operationIds: list[Annotated[str, Field(min_length=8, max_length=128)]] = Field(min_length=1, max_length=100)
    outcome: Literal["not_printed", "printed"]
    confirmed: Literal[True]
    revisions: dict[str, str]


@app.post("/api/print/recovery")
def recover_pending_prints(req: PrintRecoveryRequest):
    """Explicit local operator confirmation; one batch ID never submits twice."""
    if (len(set(req.operationIds)) != len(req.operationIds) or req.operationId in req.operationIds
            or set(req.revisions) != set(req.operationIds)):
        return _error("INVALID_PRINT_RECOVERY", retryable=False, status_code=400)
    with STORE.card_access():
        try:
            batch = STORE.claim_operation(req.operationId, kind="print_recovery", session_id=None)
        except OperationConflict:
            return _error("OPERATION_CONFLICT", retryable=False, status_code=409)
        if not batch["claimed"]:
            if batch["result"] and (batch["result"]["operationIds"] != req.operationIds or batch["result"]["outcome"] != req.outcome):
                return _error("OPERATION_CONFLICT", retryable=False, status_code=409)
            return _previous_operation(batch)
        pending = {row["operation_id"]: row for row in STORE.pending_prints()}
        results = []
        for operation_id in req.operationIds:
            op = STORE.get_operation(operation_id)
            if (not op or op["kind"] not in {"badge_print", "report_print", "souvenir_print"}
                    or op["status"] not in {"unknown", "retryable_error"}
                    or operation_id not in pending or req.revisions[operation_id] != _print_revision(pending[operation_id])
                    or (op["kind"] != "souvenir_print" and not STORE.active_card(op["session_id"]))):
                results.append({"operationId": operation_id, "status": "skipped"})
                continue
            if op["status"] == "unknown":
                STORE.resolve_unknown_operation(operation_id, outcome=req.outcome)
                if req.outcome == "printed":
                    results.append({"operationId": operation_id, "status": "confirmed"})
                    continue
            elif req.outcome == "printed":
                results.append({"operationId": operation_id, "status": "skipped"})
                continue
            payload = STORE.print_payload(operation_id)
            if payload is None:
                results.append({"operationId": operation_id, "status": "missing_image"})
                continue
            png, extra = payload
            try:
                with Image.open(BytesIO(png)) as source:
                    image = source.copy()
            except (OSError, ValueError):
                results.append({"operationId": operation_id, "status": "missing_image"})
                continue
            claimed = STORE.claim_operation(operation_id, kind=op["kind"], session_id=op["session_id"])
            if not claimed["claimed"]:
                results.append({"operationId": operation_id, "status": "skipped"})
                continue
            if op["kind"] == "souvenir_print":
                response = _submit_print(operation_id, op["kind"], image, extra=extra)
            else:
                response = _submit_session_print(op["session_id"], operation_id, op["kind"], image, extra=extra)
            current = STORE.get_operation(operation_id)
            results.append({"operationId": operation_id, "status": response["status"] if isinstance(response, dict) else current["status"]})
            if not isinstance(response, dict):
                break  # A device failure stops this batch; the remaining jobs keep their original state.
        result = {"operationIds": req.operationIds, "outcome": req.outcome, "results": results}
        STORE.finish_operation(req.operationId, kind="print_recovery", status="success", result=result)
        return {"ok": True, **result}


@app.get("/api/operations/{operation_id}")
def operation_status(operation_id: str):
    """Operator/reconciliation endpoint for an idempotent side effect."""
    op = STORE.get_operation(operation_id)
    if not op:
        return _error("OPERATION_NOT_FOUND", retryable=False, status_code=404)
    return {
        "ok": True,
        "operationId": operation_id,
        "kind": op["kind"],
        "sessionId": op["session_id"],
        "status": op["status"],
        "errorCode": op["error_code"],
        "retryable": op["retryable"],
        "result": op["result"],
    }


class IssueRequest(BaseModel):
    name: str = Field(min_length=1, max_length=10)
    dept: str = Field(min_length=1, max_length=20)
    char_id: str
    emp_no: str = Field(min_length=1, max_length=12)


@app.post("/api/issue")
def issue(req: IssueRequest) -> dict:
    """Legacy non-idempotent badge endpoint kept for existing tests/tools."""
    if os.getenv('KIOSK_ENABLE_LEGACY_ISSUE') != '1' or os.getenv('KIOSK_PRINT', 'screen') != 'screen':
        return _error('LEGACY_ENDPOINT_DISABLED', retryable=False, status_code=410)
    proto: Prototypes = STATE["proto"]
    if req.char_id not in proto.ids:
        raise HTTPException(400, f"모르는 캐릭터: {req.char_id}")

    try:
        img = render_badge(req.name.strip(), req.dept, req.char_id, req.emp_no)
    except BadgeError as exc:
        return _error("BADGE_RENDER_FAILED", retryable=True, status_code=500)

    try:
        result = print_badge(img)
    except PrintError as exc:
        return _error("UNKNOWN_OUTCOME", retryable=False, status_code=503)

    return {"ok": True, **_print_result(result, "legacy")}


app.include_router(photo_lab_router)
app.mount("/assets", StaticFiles(directory=ASSETS), name="assets")
if FRONTEND.is_dir():
    app.mount("/static", StaticFiles(directory=FRONTEND), name="static")


@app.get("/")
def index():
    page = FRONTEND / "kiosk.html"
    if not page.exists():
        return {
            "message": "프론트엔드가 아직 없다.",
            "api": ["/api/health", "/api/characters", "/api/match"],
        }
    return FileResponse(page)
