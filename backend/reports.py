"""MirrorTing report transport, source validation, and thermal receipt rendering.

The upstream owns the report. This module accepts only the real MirrorTing
``/api/sessions/{id}/report`` schema; it never fills a missing live result with
the frontend's demonstration copy. Kiosk visitor identity comes from our local
session and is passed separately to ``render_report``.
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from urllib.parse import urlsplit

import httpx
from PIL import Image, ImageDraw

from backend.badge import BadgeError, _font

REPORT_WIDTH = 576
_FITS = ("response", "voice", "expression", "posture", "eye")
_SCORED_FITS = ("response", "voice", "expression", "posture")


class ReportError(Exception):
    """Stable kiosk-facing error without upstream body, URL, or credentials."""

    def __init__(self, code: str, *, retryable: bool = False):
        super().__init__(code)
        self.code = code
        self.retryable = retryable


def _trusted_base_url(value: str) -> str:
    if not value:
        raise ReportError("INTEGRATION_PENDING")
    try:
        parsed = urlsplit(value)
        parsed.port  # Reject malformed ports before making a network request.
    except ValueError as exc:
        raise ReportError("INTEGRATION_PENDING") from exc
    if (
        parsed.scheme not in {"http", "https"}
        or not parsed.hostname
        or parsed.username
        or parsed.password
        or parsed.path not in {"", "/"}
        or parsed.query
        or parsed.fragment
    ):
        raise ReportError("INTEGRATION_PENDING")
    return value.rstrip("/")


def _text(value: object, *, limit: int = 500) -> str:
    return value.strip()[:limit] if isinstance(value, str) else ""


def _score(value: object) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ReportError("INVALID_RESPONSE")
    number = float(value)
    if not math.isfinite(number) or not 0 <= number <= 100:
        raise ReportError("INVALID_RESPONSE")
    return number


def _text_list(value: object) -> list[str]:
    if not isinstance(value, list):
        raise ReportError("INVALID_RESPONSE")
    if any(not isinstance(item, str) for item in value):
        raise ReportError("INVALID_RESPONSE")
    return [clean for item in value[:8] if (clean := _text(item))]


def normalize_report(
    kiosk_session_id: str, mirror_session_id: int, payload: Mapping[str, object]
) -> dict:
    """Keep only observed ReportOut fields and reject another session's body.

    MirrorTing has one report per roleplay session. ``reportId`` is therefore
    the source ``session_id`` serialized for the kiosk UI, not a fabricated ID.
    """
    if not isinstance(kiosk_session_id, str) or not kiosk_session_id:
        raise ReportError("INVALID_RESPONSE")
    if isinstance(mirror_session_id, bool) or not isinstance(mirror_session_id, int) or mirror_session_id < 1:
        raise ReportError("INVALID_RESPONSE")
    if not isinstance(payload, Mapping):
        raise ReportError("INVALID_RESPONSE")
    source_id = payload.get("session_id")
    if isinstance(source_id, bool) or not isinstance(source_id, int) or source_id != mirror_session_id:
        raise ReportError("INVALID_RESPONSE")

    raw_fits = payload.get("fit_scores")
    if not isinstance(raw_fits, dict):
        raise ReportError("INVALID_RESPONSE")
    fits: dict[str, dict] = {}
    for key in _FITS:
        if key not in raw_fits:
            continue
        item = raw_fits[key]
        if not isinstance(item, dict):
            raise ReportError("INVALID_RESPONSE")
        fits[key] = {
            "score": _score(item.get("score")),
            "label": _text(item.get("label"), limit=60),
            "summary": _text(item.get("summary")),
            "provisional": item.get("provisional") is True,
            "observation": item.get("observation") is True,
        }

    raw_headline = payload.get("headline")
    raw_ending = payload.get("day_ending")
    if not isinstance(raw_headline, dict) or not isinstance(raw_ending, dict):
        raise ReportError("INVALID_RESPONSE")
    raw_coaching = payload.get("coaching", [])
    if not isinstance(raw_coaching, list):
        raise ReportError("INVALID_RESPONSE")
    coaching = []
    for item in raw_coaching[:5]:
        if not isinstance(item, dict):
            raise ReportError("INVALID_RESPONSE")
        coaching.append({
            "issue": _text(item.get("issue")),
            "suggestion": _text(item.get("suggestion")),
        })

    mode = payload.get("mode")
    if isinstance(mode, bool) or not isinstance(mode, int) or mode not in (5, 10):
        raise ReportError("INVALID_RESPONSE")
    return {
        "status": "available",
        "source": "mirrorting",
        "sessionId": kiosk_session_id,
        "mirrorSessionId": mirror_session_id,
        "reportId": str(source_id),
        "totalScore": _score(payload.get("total_score")),
        "grade": _text(payload.get("grade"), limit=40),
        "modeMinutes": mode,
        "fitScores": fits,
        "strengths": _text_list(payload.get("strengths")),
        "improvements": _text_list(payload.get("improvements")),
        "headline": {
            "sentence": _text(raw_headline.get("sentence")),
            "context": _text(raw_headline.get("context")),
        },
        "dayEnding": {
            "label": _text(raw_ending.get("label"), limit=80),
            "text": _text(raw_ending.get("text")),
        },
        "coaching": coaching,
    }


def _json_response(response: httpx.Response, *, report: bool = False) -> dict:
    if response.status_code == 403:
        raise ReportError("INTEGRATION_UNAUTHORIZED")
    if response.status_code == 404:
        raise ReportError("REPORT_PENDING" if report else "REPORT_NOT_FOUND", retryable=report)
    if response.status_code != 200:
        raise ReportError("BACKEND_UNAVAILABLE", retryable=response.status_code >= 500)
    try:
        payload = response.json()
    except ValueError as exc:
        raise ReportError("INVALID_RESPONSE") from exc
    if not isinstance(payload, dict):
        raise ReportError("INVALID_RESPONSE")
    return payload


def fetch_mirrorting_report(
    kiosk_session_id: str,
    mirror_session_id: int,
    access_token: str,
    *,
    base_url: str,
    client: httpx.Client | None = None,
) -> dict:
    """Read a linked report from the configured upstream using server-only token.

    The caller must first load the persisted link after validating the card's
    kiosk session. No browser value may override ``base_url`` or ``access_token``.
    """
    root = _trusted_base_url(base_url)
    if isinstance(mirror_session_id, bool) or not isinstance(mirror_session_id, int) or mirror_session_id < 1:
        raise ReportError("INVALID_RESPONSE")
    if not isinstance(access_token, str) or not access_token:
        raise ReportError("INTEGRATION_PENDING")
    path = f"/api/sessions/{mirror_session_id}"
    headers = {"X-Session-Token": access_token, "Accept": "application/json"}
    owned = client is None
    http = client or httpx.Client(timeout=5, follow_redirects=False, trust_env=False)
    try:
        try:
            progress = _json_response(http.get(root + path + "/progress", headers=headers, follow_redirects=False))
            status = progress.get("status")
            stage = progress.get("stage")
            if stage == "error":
                raise ReportError("REPORT_ERROR", retryable=True)
            if status == "aborted":
                raise ReportError("REPORT_NOT_FOUND")
            if status != "completed":
                if status not in {"ready", "in_progress", "analyzing"}:
                    raise ReportError("INVALID_RESPONSE")
                raise ReportError("REPORT_PENDING", retryable=True)
            report = _json_response(http.get(root + path + "/report", headers=headers, follow_redirects=False), report=True)
            return normalize_report(kiosk_session_id, mirror_session_id, report)
        except httpx.TimeoutException as exc:
            raise ReportError("REPORT_TIMEOUT", retryable=True) from exc
        except httpx.RequestError as exc:
            raise ReportError("BACKEND_UNAVAILABLE", retryable=True) from exc
    finally:
        if owned:
            http.close()


def _wrapped(draw: ImageDraw.ImageDraw, text: str, font, max_width: int) -> list[str]:
    lines: list[str] = []
    for paragraph in text.splitlines() or [""]:
        line = ""
        for char in paragraph:
            candidate = line + char
            if line and draw.textlength(candidate, font=font) > max_width:
                lines.append(line)
                line = char
            else:
                line = candidate
        lines.append(line)
    return lines


def render_report(report: Mapping[str, object], *, name: str, team: str) -> Image.Image:
    """Render a 576-dot 1-bit receipt from verified normalized source fields."""
    if report.get("status") != "available" or report.get("source") != "mirrorting":
        raise ReportError("REPORT_NOT_FOUND")
    if not report.get("sessionId") or not report.get("reportId"):
        raise ReportError("INVALID_RESPONSE")
    try:
        title_font, section_font, body_font, small_font = _font(34), _font(26), _font(22), _font(18)
    except BadgeError as exc:
        raise ReportError("REPORT_RENDER_FAILED") from exc

    width, margin = REPORT_WIDTH, 34
    canvas = Image.new("L", (width, 4300), 255)
    draw = ImageDraw.Draw(canvas)
    y = 0
    draw.rectangle((0, 0, width, 108), fill=0)
    draw.text((margin, 20), "MIRRORTING WORKS", font=section_font, fill=255)
    draw.text((margin, 60), "오늘의 퇴근 리포트", font=body_font, fill=255)
    y = 135

    def line(label: str, value: str) -> None:
        nonlocal y
        if not value:
            return
        draw.text((margin, y), label, font=small_font, fill=0)
        y += 28
        for part in _wrapped(draw, value, body_font, width - 2 * margin):
            draw.text((margin, y), part, font=body_font, fill=0)
            y += 32
        y += 10

    def section(label: str, values: list[str]) -> None:
        nonlocal y
        if not values:
            return
        y += 12
        draw.line((margin, y, width - margin, y), fill=0, width=2)
        y += 22
        draw.text((margin, y), label, font=section_font, fill=0)
        y += 44
        for value in values:
            for part in _wrapped(draw, value, body_font, width - 2 * margin):
                draw.text((margin, y), part, font=body_font, fill=0)
                y += 32
            y += 12

    line("이름 / 팀", f"{_text(name, limit=30)} / {_text(team, limit=40)}")
    line("사원번호", str(report["sessionId"]))
    line("MirrorTing 세션", str(report["reportId"]))
    score = report.get("totalScore")
    score_label = "미측정" if score is None else f"{float(score):g}점"
    if report.get("grade"):
        score_label += f" · {_text(report['grade'], limit=40)}"
    line("종합 결과", score_label)

    fits = report.get("fitScores") or {}
    if not isinstance(fits, Mapping):
        raise ReportError("INVALID_RESPONSE")
    fit_lines = []
    for key in _SCORED_FITS:
        fit = fits.get(key)
        if not isinstance(fit, Mapping):
            continue
        label = _text(fit.get("label"), limit=60) or key
        value = "미측정" if fit.get("score") is None else f"{float(fit['score']):g}점"
        if fit.get("provisional"):
            value += " (참고 지표)"
        fit_lines.append(f"{label}: {value}")
    section("4-Fit", fit_lines)
    section("발견한 강점", list(report.get("strengths") or []))
    section("다음 연습", list(report.get("improvements") or []))
    headline = report.get("headline") or {}
    if isinstance(headline, Mapping):
        headline_lines = [
            clean for item in (headline.get("sentence"), headline.get("context"))
            if (clean := _text(item, limit=220))
        ]
        section("오늘의 한 문장", headline_lines)
    coaching = report.get("coaching") or []
    if isinstance(coaching, list):
        coaching_lines = []
        for item in coaching[:3]:
            if not isinstance(item, Mapping):
                continue
            issue = _text(item.get("issue"), limit=100)
            suggestion = _text(item.get("suggestion"), limit=220)
            if suggestion:
                coaching_lines.append(f"{issue}: {suggestion}" if issue else suggestion)
        section("다음 대화 제안", coaching_lines)
    ending = report.get("dayEnding") or {}
    if isinstance(ending, Mapping):
        section(_text(ending.get("label"), limit=80) or "하루의 결말", [_text(ending.get("text"))] if ending.get("text") else [])
    if y > canvas.height - 100:
        raise ReportError("REPORT_RENDER_FAILED")
    draw.line((margin, y + 10, width - margin, y + 10), fill=0, width=2)
    draw.text((margin, y + 26), "출처: MirrorTing 세션 분석 결과", font=small_font, fill=0)
    return canvas.crop((0, 0, width, y + 74)).point(lambda pixel: 255 if pixel > 127 else 0).convert("1")
