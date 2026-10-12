"""FastAPI 매칭 서버 (포트 8002).

8000은 carpedm-kiosk, 8001은 EXPO poc 백엔드가 쓰므로 8002를 쓴다.

개인정보 — 촬영 프레임은 **메모리에서만** 다루고 디스크에 쓰지 않는다.
화면의 "저장되지 않으며 즉시 폐기됩니다" 문구가 실제로 참이어야 한다.

실행
    ./.venv/bin/uvicorn backend.app:app --host 127.0.0.1 --port 8002 --reload
"""

from __future__ import annotations

import os
import re
import time
from contextlib import asynccontextmanager
from pathlib import Path

import cv2
import numpy as np
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response
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
from backend.printing import PrintError, print_badge, printer_status
from backend.profile import (
    ProfileComposer,
    ProfileQualityError,
    ProfileStore,
)

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
FRONTEND = ROOT / "frontend"
PROTO_PATH = ASSETS / "prototypes.npz"
DOMAIN_PATH = ASSETS / "domain_mean.npz"

# 표시 점수의 부드러움. 작을수록 1위가 도드라진다.
# 1단계 분포 테스트 표본이 모이면 재보정할 값이다 — 지금은 잠정치.
TEMPERATURE = float(os.getenv("KIOSK_TEMPERATURE", "0.08"))

# 업로드 상한. 800×1280 캔버스에서 뽑은 JPEG는 여유롭게 이 안에 들어온다.
MAX_UPLOAD = 8 * 1024 * 1024
MAX_DECODED_PIXELS = 12_000_000
PROFILE_TTL_SECONDS = int(os.getenv("KIOSK_PROFILE_TTL_SECONDS", "600"))
PROFILE_MAX_ITEMS = int(os.getenv("KIOSK_PROFILE_MAX_ITEMS", "8"))
OPERATION_ID = re.compile(r"^[A-Za-z0-9_-]{1,80}$")

STATE: dict = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """모델 로드는 무거우니 기동 시 한 번만 한다."""
    STATE["engine"] = FaceEngine()
    STATE["proto"] = Prototypes.load(PROTO_PATH)
    STATE["profiles"] = ProfileStore(
        ttl_seconds=PROFILE_TTL_SECONDS,
        max_items=PROFILE_MAX_ITEMS,
    )
    STATE["profile_composer"] = ProfileComposer()

    # μ_real 은 실제 얼굴 표본에서 나온다(scripts/distribution_test.py --save).
    # 없어도 순위는 나오지만 특정 캐릭터로 쏠릴 수 있다.
    if DOMAIN_PATH.exists():
        z = np.load(DOMAIN_PATH)
        STATE["mu_real"] = z["mu_real"].astype(np.float32)
        STATE["mu_real_n"] = int(z["sample_size"][0])
    else:
        STATE["mu_real"] = None
        STATE["mu_real_n"] = 0
    yield
    STATE["profiles"].clear()
    STATE.clear()


app = FastAPI(title="4-Fit MirrorTing 사원증 키오스크", lifespan=lifespan)

# 프론트를 file:// 로 열어보는 경우까지 허용한다. 전시에서는 동일 출처로 서빙된다.
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)


def char_meta() -> list[dict]:
    p: Prototypes = STATE["proto"]
    return [
        {"id": cid, "no": cid.replace("char_", ""), "group": g,
         "image": f"/assets/characters/{cid}.png"}
        for cid, g in zip(p.ids, p.groups)
    ]


@app.get("/api/health")
def health() -> dict:
    p: Prototypes = STATE["proto"]
    return {
        "ok": True,
        "models": {
            "yunet": True,
            "sface": True,
            "profile_composite": STATE.get("profile_composer") is not None,
        },
        "characters": len(p.ids),
        "style_set_n": p.style_n,
        "mu_real_n": STATE["mu_real_n"],
        "calibrated": STATE["mu_real"] is not None,
        "temperature": TEMPERATURE,
        "printer": printer_status(),
        # 운영자 진단용 — 이 값이 크면 8종이 서로 붙어 있다는 뜻이다.
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
    """프리뷰 전용 — 얼굴 유무만 본다. SFace 임베딩(파이에서 가장 비싼 단계)을 건너뛴다."""
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
    """촬영 프레임 한 장 → 8종 점수. 이미지는 저장하지 않는다."""
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
        return {"ok": False, "error": "no_face",
                "message": "얼굴이 보이지 않아요. 화면 안으로 들어와 주세요."}
    except MultipleFacesError as exc:
        return {"ok": False, "error": "multiple_faces", "count": exc.count,
                "message": "여러 명이 보여요. 한 분만 서 주세요."}
    finally:
        # 원본 프레임을 최대한 빨리 놓는다.
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
        # 화면에 쓰는 값 — "8종 중 상대적으로 어디에 가까운가"
        "display": [round(float(v) * 100, 1) for v in display],
        "order": [int(i) for i in order],
        # 운영자 진단용 원시 코사인. 화면에는 노출하지 않는다.
        "raw": [round(float(v), 4) for v in scores],
        "margin": round(float(scores[order[0]] - scores[order[1]]), 4),
        "confidence": round(float(det.confidence), 3),
        "elapsed_ms": round(elapsed, 1),
        "calibrated": STATE["mu_real"] is not None,
    }


def _profile_response(profile_id: str, elapsed_ms: float, *, reused: bool) -> dict:
    return {
        "ok": True,
        "profileId": profile_id,
        "previewUrl": f"/api/profile/{profile_id}/image",
        "expiresIn": PROFILE_TTL_SECONDS,
        "elapsed_ms": round(elapsed_ms, 1),
        "reused": reused,
    }


@app.post("/api/profile")
async def generate_profile(
    frame: UploadFile = File(...), operation_id: str | None = Form(default=None)
) -> dict:
    """Mode B: one captured frame to a memory-only local profile composite."""

    if operation_id and not OPERATION_ID.fullmatch(operation_id):
        return {"ok": False, "error": "invalid_request"}

    store: ProfileStore = STATE["profiles"]
    previous = store.find_operation(operation_id)
    if previous:
        return _profile_response(previous, 0.0, reused=True)

    raw = await frame.read()
    if not raw or len(raw) > MAX_UPLOAD:
        return {"ok": False, "error": "invalid_image"}
    img = cv2.imdecode(np.frombuffer(raw, np.uint8), cv2.IMREAD_COLOR)
    del raw
    if img is None or img.shape[0] * img.shape[1] > MAX_DECODED_PIXELS:
        return {"ok": False, "error": "invalid_image"}

    composer: ProfileComposer | None = STATE.get("profile_composer")
    if composer is None:
        del img
        return {"ok": False, "error": "profile_unavailable"}

    started = time.perf_counter()
    try:
        png = composer.generate(img, STATE["engine"])
    except NoFaceError:
        return {"ok": False, "error": "no_face"}
    except MultipleFacesError as exc:
        return {"ok": False, "error": "multiple_faces", "count": exc.count}
    except ProfileQualityError as exc:
        return {"ok": False, "error": exc.code}
    except cv2.error:
        return {"ok": False, "error": "composition_failed"}
    finally:
        # No original frame or face feature is persisted beyond this request.
        del img

    profile_id = store.put(png, operation_id)
    del png
    elapsed = (time.perf_counter() - started) * 1000
    return _profile_response(profile_id, elapsed, reused=False)


@app.get("/api/profile/{profile_id}/image")
def profile_image(profile_id: str) -> Response:
    png = STATE["profiles"].get(profile_id)
    if png is None:
        raise HTTPException(404, "프로필이 없거나 만료됐다")
    return Response(
        content=png,
        media_type="image/png",
        headers={
            "Cache-Control": "no-store, max-age=0",
            "Pragma": "no-cache",
            "X-Content-Type-Options": "nosniff",
        },
    )


@app.delete("/api/profile/{profile_id}")
def delete_profile(profile_id: str) -> dict:
    # Deletion is idempotent so browser reset can safely call it more than once.
    STATE["profiles"].delete(profile_id)
    return {"ok": True}


class IssueRequest(BaseModel):
    """배지 발급 요청. 얼굴 이미지는 받지 않는다 — 매칭은 이미 끝났고,
    여기 오는 건 화면에서 확인한 텍스트와 캐릭터 선택뿐이다."""

    name: str = Field(min_length=1, max_length=10)
    dept: str = Field(min_length=1, max_length=20)
    char_id: str
    emp_no: str = Field(min_length=1, max_length=12)


@app.post("/api/issue")
def issue(req: IssueRequest) -> dict:
    """배지 렌더 → 출력. 이름은 인쇄에만 쓰고 저장하지 않는다
    (screen 백엔드는 개발용으로 마지막 한 장만 덮어쓴다 — printing.py 참고)."""
    proto: Prototypes = STATE["proto"]
    if req.char_id not in proto.ids:
        raise HTTPException(400, f"모르는 캐릭터: {req.char_id}")

    try:
        img = render_badge(req.name.strip(), req.dept, req.char_id, req.emp_no)
    except BadgeError as exc:
        # 자산·폰트 문제 — 운영자가 고쳐야 하는 종류라 메시지를 그대로 올린다.
        return {"ok": False, "error": "render_failed", "message": str(exc)}

    try:
        result = print_badge(img)
    except PrintError as exc:
        # 용지 없음·단선 등. 프론트는 이걸 받아 화면 폴백으로 넘긴다.
        return {"ok": False, "error": "print_failed", "message": str(exc)}

    return {"ok": True, **result}


# ---------- 정적 파일 ----------

app.mount("/assets", StaticFiles(directory=ASSETS), name="assets")

if FRONTEND.is_dir():
    app.mount("/static", StaticFiles(directory=FRONTEND), name="static")


@app.get("/")
def index():
    page = FRONTEND / "kiosk.html"
    if not page.exists():
        return {"message": "프론트엔드가 아직 없다. 3단계에서 만든다.",
                "api": ["/api/health", "/api/characters", "/api/match"]}
    return FileResponse(page)
