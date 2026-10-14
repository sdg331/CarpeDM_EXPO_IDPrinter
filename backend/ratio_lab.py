"""Opt-in, local-only comparison. Current badge recommendations stay unchanged."""
import json
import os
import subprocess
import threading
import time
from io import BytesIO
from pathlib import Path

from fastapi import APIRouter, File, Form, UploadFile
from starlette.concurrency import run_in_threadpool
from typing import Literal

from backend.face_ratios import ROOT, RatioError, load_references, load_balance

router = APIRouter(prefix="/api/experiments/matching")
COMPARISON_LOCK = threading.Lock()
ERROR_CODES = {"NO_PERSON", "MULTIPLE_PEOPLE", "FACE_NOT_FRONTAL", "LANDMARK_QUALITY_FAILED",
               "RATIO_REFERENCES_UNAVAILABLE", "LANDMARK_MODEL_UNAVAILABLE", "LANDMARK_ENGINE_UNAVAILABLE"}


def ratio_python() -> Path:
    return Path(os.getenv("KIOSK_FACE_RATIO_PYTHON") or
                ROOT / ".venv-landmarks" / ("Scripts/python.exe" if os.name == "nt" else "bin/python"))


@router.get("/status")
def status():
    configured = ratio_python().is_file()
    try:
        load_references()
        load_balance()
    except RatioError:
        configured = False
    return {"enabled": os.getenv("KIOSK_MATCH_LAB") == "1", "configured": configured,
            "distributionCorrected": configured,
            "experimental": True, "calibrated": False, "externalUpload": False}


def run_ratio_frame(raw: bytes, gender: str, selected=None, *, landmarks_only=False) -> dict:
    try:
        cache = ROOT / ".preview/landmark-cache"
        cache.mkdir(parents=True, exist_ok=True)
        started = time.perf_counter()
        command = [str(ratio_python()), str(ROOT / "scripts/ratio_frame.py"), "--gender", gender]
        if selected:
            command += ["--box", *[str(value) for value in selected["box"]]]
        if landmarks_only:
            command += ["--landmarks-only"]
        result = subprocess.run(command, input=raw, capture_output=True, timeout=8 if landmarks_only else 30,
                                env={**os.environ, "MPLCONFIGDIR": str(cache)}, cwd=ROOT)
        data = json.loads(result.stdout)
        if result.returncode != 0 or not isinstance(data, dict):
            raise ValueError("Invalid subprocess response")
        if not data.get("ok"):
            code = data.get("error")
            raise RatioError(code if code in ERROR_CODES else "LANDMARK_ENGINE_UNAVAILABLE")
        data["elapsedMs"] = round((time.perf_counter() - started) * 1000, 1)
        return data
    except subprocess.TimeoutExpired:
        raise RatioError("LANDMARK_TIMEOUT") from None
    except (OSError, ValueError):
        raise RatioError("LANDMARK_ENGINE_UNAVAILABLE") from None


@router.post("/compare")
async def compare(frame: UploadFile = File(...), character_gender: Literal["any", "male", "female"] = Form("any")):
    from backend.app import _decode_frame, _error, _frame_bytes, match
    if os.getenv("KIOSK_MATCH_LAB") != "1":
        return _error("MATCH_LAB_DISABLED", retryable=False, status_code=403)
    if not status()["configured"]:
        return _error("LANDMARK_ENGINE_UNAVAILABLE", retryable=False, status_code=503)
    raw = await _frame_bytes(frame)
    await run_in_threadpool(_decode_frame, raw)
    if not COMPARISON_LOCK.acquire(blocking=False):
        return _error("MATCH_COMPARISON_BUSY", retryable=True, status_code=409)
    try:
        # Use the real production endpoint so its filtering and error handling
        # cannot drift from the SFace baseline in this experiment.
        sface = await match(UploadFile(file=BytesIO(raw), filename="frame"), character_gender)
        if not isinstance(sface, dict) or not sface.get("ok"):
            return sface
        try:
            ratios = await run_in_threadpool(run_ratio_frame, raw, character_gender, sface.get("face"))
        except RatioError as exc:
            code = str(exc)
            user_error = code in {"NO_PERSON", "MULTIPLE_PEOPLE", "FACE_NOT_FRONTAL", "LANDMARK_QUALITY_FAILED"}
            return _error(code, retryable=user_error or code == "LANDMARK_TIMEOUT",
                          status_code=422 if user_error else 503)
        sface_id = sface["characters"][sface["top"]]["id"]
        return {"ok": True, "experimental": True, "externalUpload": False,
                "characterGender": character_gender,
                "face": sface.get("face"),
                "sface": {"characterId": sface_id, "ranking": [
                    {"characterId": sface["characters"][i]["id"], "score": sface["raw"][i]}
                    for i in sface["order"]], "elapsedMs": sface["elapsed_ms"]},
                "ratios": ratios, "sameRecommendation": sface_id == ratios["characterId"]}
    finally:
        COMPARISON_LOCK.release()
