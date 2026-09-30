"""FastAPI backend for the 4-Fit MirrorTing employee-badge kiosk.

Port 8002 is used because 8000/8001 are reserved by other EXPO services.

Privacy:
- captured frames are processed in memory only;
- raw face images and embeddings are never written to the local session DB;
- card UID/session mappings stay on the kiosk.

Run:
    ./.venv/bin/uvicorn backend.app:app --host 127.0.0.1 --port 8002 --reload
"""

from __future__ import annotations

import os
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Literal

import cv2
import numpy as np
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from backend.badge import BadgeError, render_badge
from backend.face import (
    FaceEngine,
    MultipleFacesError,
    NoFaceError,
    Prototypes,
    display_scores,
)
from backend.nfc import NfcError, nfc_status, read_card_uid
from backend.printing import PrintError, print_badge, printer_status
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


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load heavyweight face models once and initialize durable local state."""
    STORE.init()
    STATE["engine"] = FaceEngine()
    STATE["proto"] = Prototypes.load(PROTO_PATH)

    if DOMAIN_PATH.exists():
        z = np.load(DOMAIN_PATH)
        STATE["mu_real"] = z["mu_real"].astype(np.float32)
        STATE["mu_real_n"] = int(z["sample_size"][0])
    else:
        STATE["mu_real"] = None
        STATE["mu_real_n"] = 0
    yield
    STATE.clear()


app = FastAPI(title="4-Fit MirrorTing 사원증 키오스크", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)


def _error(
    code: str,
    *,
    retryable: bool,
    status_code: int,
    detail: str | None = None,
) -> JSONResponse:
    payload: dict = {
        "ok": False,
        "error": {
            "code": code,
            "retryable": retryable,
        },
    }
    if detail:
        payload["error"]["detail"] = detail
    return JSONResponse(status_code=status_code, content=payload)


def char_meta() -> list[dict]:
    p: Prototypes = STATE["proto"]
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
    p: Prototypes = STATE["proto"]
    return {
        "ok": True,
        "models": {"yunet": True, "sface": True},
        "characters": len(p.ids),
        "style_set_n": p.style_n,
        "mu_real_n": STATE["mu_real_n"],
        "calibrated": STATE["mu_real"] is not None,
        "temperature": TEMPERATURE,
        "printer": printer_status(),
        "nfc": nfc_status(),
        "database": STORE.health(),
        "max_pair": float(_max_pair()),
    }


def _max_pair() -> float:
    r = STATE["proto"].residuals()
    m = r @ r.T
    return m[np.triu_indices(len(m), 1)].max()


@app.get("/api/characters")
def characters() -> dict:
    return {"characters": char_meta()}


@app.post("/api/detect")
async def detect(frame: UploadFile = File(...)) -> dict:
    """Preview-only face count. SFace embedding is deliberately skipped."""
    raw = await frame.read()
    if not raw or len(raw) > MAX_UPLOAD:
        raise HTTPException(400, "이미지가 올바르지 않다")
    img = cv2.imdecode(np.frombuffer(raw, np.uint8), cv2.IMREAD_COLOR)
    del raw
    if img is None:
        raise HTTPException(400, "이미지를 해석할 수 없다")

    dets = STATE["engine"].detect(img)
    del img
    return {
        "ok": len(dets) == 1,
        "count": len(dets),
        "confidence": round(float(dets[0].confidence), 3) if dets else 0.0,
    }


@app.post("/api/match")
async def match(frame: UploadFile = File(...)) -> dict:
    """One captured frame -> 8-character relative scores. Image is not saved."""
    raw = await frame.read()
    if not raw:
        raise HTTPException(400, "빈 이미지다")
    if len(raw) > MAX_UPLOAD:
        raise HTTPException(413, "이미지가 너무 크다")

    img = cv2.imdecode(np.frombuffer(raw, np.uint8), cv2.IMREAD_COLOR)
    del raw
    if img is None:
        raise HTTPException(400, "이미지를 해석할 수 없다")

    engine: FaceEngine = STATE["engine"]
    proto: Prototypes = STATE["proto"]

    t0 = time.perf_counter()
    try:
        emb, det = engine.embed_single(img, strict=True)
    except NoFaceError:
        return {
            "ok": False,
            "error": "no_face",
            "message": "얼굴이 보이지 않아요. 화면 안으로 들어와 주세요.",
        }
    except MultipleFacesError as exc:
        return {
            "ok": False,
            "error": "multiple_faces",
            "count": exc.count,
            "message": "여러 명이 보여요. 한 분만 서 주세요.",
        }
    finally:
        del img

    scores = proto.match_scores(emb, STATE["mu_real"])
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
        "calibrated": STATE["mu_real"] is not None,
    }


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


class BadgePrintRequest(BaseModel):
    operationId: str = Field(min_length=8, max_length=128)
    sessionId: str = Field(min_length=1, max_length=32)


def _validate_registration(req: NfcRegisterRequest) -> tuple[str | None, str | None] | JSONResponse:
    if req.teamId not in TEAM_LABELS:
        return _error("INVALID_TEAM", retryable=False, status_code=400)

    if req.aiMode == "A":
        if req.result.kind != "A" or not req.result.characterId:
            return _error("INVALID_AI_RESULT", retryable=False, status_code=400)
        proto: Prototypes = STATE["proto"]
        if req.result.characterId not in proto.ids:
            return _error("INVALID_AI_RESULT", retryable=False, status_code=400)
        return req.result.characterId, None

    return _error("MODE_B_NOT_READY", retryable=False, status_code=501)


@app.post("/api/nfc/register")
def register_nfc(req: NfcRegisterRequest):
    """Bind a physical NFC card UID to one locally persisted kiosk session."""
    try:
        op = STORE.get_operation(req.operationId, "nfc_register")
    except OperationConflict as exc:
        return _error(
            "OPERATION_CONFLICT", retryable=False, status_code=409, detail=str(exc)
        )

    if op:
        if op["status"] == "success" and op["result"]:
            return {"ok": True, **op["result"]}

        binding = STORE.binding_for_operation(req.operationId)
        if binding:
            result = {"status": "verified", "sessionId": binding["session_id"]}
            STORE.finish_operation(
                req.operationId,
                kind="nfc_register",
                status="success",
                result=result,
            )
            return {"ok": True, **result}

        if op["status"] == "retryable_error":
            STORE.restart_operation(req.operationId, kind="nfc_register")
            session_id = op["session_id"]
        else:
            return _error(
                "UNKNOWN_OUTCOME",
                retryable=False,
                status_code=409,
                detail=f"operation status={op['status']}",
            )
    else:
        validated = _validate_registration(req)
        if isinstance(validated, JSONResponse):
            return validated
        char_id, profile_id = validated
        try:
            session = STORE.create_session(
                name=req.name,
                team_id=req.teamId,
                ai_mode=req.aiMode,
                char_id=char_id,
                profile_id=profile_id,
            )
        except (ValueError, StoreError) as exc:
            return _error(
                "SESSION_CREATE_FAILED",
                retryable=False,
                status_code=500,
                detail=str(exc),
            )
        session_id = session["session_id"]
        STORE.begin_operation(
            req.operationId,
            kind="nfc_register",
            session_id=session_id,
        )

    try:
        uid = read_card_uid(NFC_TIMEOUT_SECONDS)
    except NfcError as exc:
        STORE.finish_operation(
            req.operationId,
            kind="nfc_register",
            status="retryable_error" if exc.retryable else "error",
            error_code=exc.code,
            retryable=exc.retryable,
        )
        status = 408 if exc.code == "NFC_TIMEOUT" else 503
        return _error(
            exc.code,
            retryable=exc.retryable,
            status_code=status,
            detail=str(exc),
        )

    try:
        STORE.bind_card(
            session_id=session_id,
            card_uid=uid,
            operation_id=req.operationId,
        )
    except Exception as exc:
        STORE.finish_operation(
            req.operationId,
            kind="nfc_register",
            status="unknown",
            error_code="UNKNOWN_OUTCOME",
            retryable=False,
        )
        return _error(
            "UNKNOWN_OUTCOME",
            retryable=False,
            status_code=500,
            detail=str(exc),
        )

    result = {"status": "verified", "sessionId": session_id}
    STORE.finish_operation(
        req.operationId,
        kind="nfc_register",
        status="success",
        result=result,
    )
    return {"ok": True, **result}


@app.post("/api/nfc/resolve")
def resolve_checkout(req: OperationRequest):
    """Read a card and resolve its currently active visitor session."""
    try:
        uid = read_card_uid(NFC_TIMEOUT_SECONDS)
    except NfcError as exc:
        status = 408 if exc.code == "NFC_TIMEOUT" else 503
        return _error(
            exc.code,
            retryable=exc.retryable,
            status_code=status,
            detail=str(exc),
        )

    session = STORE.resolve_card(uid)
    if not session:
        return _error("UNKNOWN_CARD", retryable=True, status_code=404)

    return {
        "ok": True,
        "sessionId": session["session_id"],
        "name": session["name"],
        "teamId": session["team_id"],
    }


@app.post("/api/badge/print")
def print_session_badge(req: BadgePrintRequest):
    """Render and print one badge with persistent duplicate protection."""
    try:
        op = STORE.get_operation(req.operationId, "badge_print")
    except OperationConflict as exc:
        return _error(
            "OPERATION_CONFLICT", retryable=False, status_code=409, detail=str(exc)
        )

    if op:
        if op["status"] == "success" and op["result"]:
            return {"ok": True, **op["result"]}
        return _error(
            "UNKNOWN_OUTCOME",
            retryable=False,
            status_code=409,
            detail=f"operation status={op['status']}",
        )

    try:
        session = STORE.get_session(req.sessionId)
    except SessionNotFound:
        return _error("SESSION_NOT_FOUND", retryable=False, status_code=404)

    if session["ai_mode"] != "A" or not session["char_id"]:
        return _error("BADGE_DATA_INCOMPLETE", retryable=False, status_code=409)

    STORE.begin_operation(
        req.operationId,
        kind="badge_print",
        session_id=req.sessionId,
    )

    try:
        image = render_badge(
            session["name"],
            TEAM_LABELS[session["team_id"]],
            session["char_id"],
            session["session_id"],
        )
    except BadgeError as exc:
        STORE.finish_operation(
            req.operationId,
            kind="badge_print",
            status="error",
            error_code="BADGE_RENDER_FAILED",
            retryable=False,
        )
        return _error(
            "BADGE_RENDER_FAILED",
            retryable=False,
            status_code=500,
            detail=str(exc),
        )

    try:
        printed = print_badge(image)
    except PrintError as exc:
        STORE.finish_operation(
            req.operationId,
            kind="badge_print",
            status="unknown",
            error_code="UNKNOWN_OUTCOME",
            retryable=False,
        )
        return _error(
            "UNKNOWN_OUTCOME",
            retryable=False,
            status_code=503,
            detail=str(exc),
        )

    result = {
        "status": "success",
        "printJobId": req.operationId,
        **printed,
    }
    STORE.finish_operation(
        req.operationId,
        kind="badge_print",
        status="success",
        result=result,
    )
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
    proto: Prototypes = STATE["proto"]
    if req.char_id not in proto.ids:
        raise HTTPException(400, f"모르는 캐릭터: {req.char_id}")

    try:
        img = render_badge(req.name.strip(), req.dept, req.char_id, req.emp_no)
    except BadgeError as exc:
        return {"ok": False, "error": "render_failed", "message": str(exc)}

    try:
        result = print_badge(img)
    except PrintError as exc:
        return {"ok": False, "error": "print_failed", "message": str(exc)}

    return {"ok": True, **result}


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
