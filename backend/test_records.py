"""Explicit, expiring local fixtures for a registered card's screen preview."""

from __future__ import annotations

import json
import math
import os
import re
import time
from pathlib import Path

from backend.reports import ReportError, normalize_report

TEST_RECORDS = Path(__file__).resolve().parent.parent / "data" / "test_records"


def load_test_report(session_id: str) -> dict | None:
    if os.getenv("KIOSK_TEST_RECORDS") != "1" or not re.fullmatch(r"MW\d{10}", session_id):
        return None
    path = TEST_RECORDS / f"{session_id}.json"
    if not path.is_file():
        return None
    try:
        if path.stat().st_size > 64 * 1024:
            raise ValueError("fixture too large")
        data = json.loads(path.read_text(encoding="utf-8"))
        expires = data["expiresAt"]
        if isinstance(expires, bool) or not isinstance(expires, (int, float)) or not math.isfinite(expires):
            raise ValueError("invalid expiry")
        if expires <= time.time():
            return None
        report = normalize_report(session_id, 1, data["report"])
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise ReportError("INVALID_RESPONSE") from exc
    return {**report, "source": "local_test", "sample": True,
            "reportId": f"TEST-{session_id}", "mirrorSessionId": None}
