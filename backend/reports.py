"""MirrorTing report transport, source validation, and thermal receipt rendering.

The upstream owns the report. This module accepts only the real MirrorTing
``/api/sessions/{id}/report`` schema; it never fills a missing live result with
the frontend's demonstration copy. Kiosk visitor identity comes from our local
session and is passed separately to ``render_report``.
"""

from __future__ import annotations

import math
import os
from collections.abc import Mapping
from urllib.parse import urlsplit

import httpx
from PIL import Image, ImageDraw, ImageFilter, ImageOps

from backend.badge import BadgeError, _font
from backend.career_tips import career_tip

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
                split = line.rfind(" ") + 1
                remainder = line[split:] + char
                if split and draw.textlength(remainder, font=font) <= max_width:
                    lines.append(line[:split])
                    line = remainder
                else:
                    lines.append(line)
                    line = char
            else:
                line = candidate
        lines.append(line)
    return lines


def thermal_photo(photo: Image.Image, size: tuple[int, int]) -> Image.Image:
    """Prepare photo-only, native-dot black/white pixels before receipt assembly.

    Gamma is an exponent: values above 1 darken midtones. Keep true white/black
    endpoints, without clipping pale face detail or stretching each histogram.
    Operator tuning never changes the camera, text, QR, or printer heat settings.
    """
    try:
        gamma = float(os.getenv("KIOSK_PHOTO_GAMMA", "1.25"))
    except ValueError:
        gamma = 1.25
    if not math.isfinite(gamma) or not 1.0 <= gamma <= 1.8:
        gamma = 1.25

    photo = ImageOps.exif_transpose(photo).convert("L")
    # Reduce camera grain before downsampling; sharpen only at the final dot size
    # so edge detail survives without turning sensor noise into black flecks.
    photo = photo.filter(ImageFilter.MedianFilter(3))
    photo = ImageOps.contain(photo, size, method=Image.Resampling.LANCZOS)
    photo = photo.point([round(255 * (i / 255) ** gamma) for i in range(256)])
    photo = photo.filter(ImageFilter.UnsharpMask(radius=0.75, percent=125, threshold=3))
    # Dither once, at final size. Receipt assembly and USB bands retain these
    # exact binary pixels; never resample/dither the complete receipt afterward.
    return photo.convert("1", dither=Image.Dither.FLOYDSTEINBERG)


ENCOURAGEMENT = (
    "오늘 하루도 고생 많으셨습니다.",
    "눈에 띄는 결과가 없던 날에도,",
    "여러분이 애쓴 시간은 소중합니다.",
    "이 사진이 오늘의 여러분에게",
    "작은 응원으로 남길 바랍니다.",
    "저희의 처음에 함께해 주셔서 감사합니다.",
)
KEEPSAKE_HEIGHT = len(ENCOURAGEMENT) * 38 + 40 + 168


def draw_keepsake(draw: ImageDraw.ImageDraw, top: int) -> None:
    """Solid native-dot lettering; only the photograph uses dithering."""
    for index, line in enumerate(ENCOURAGEMENT):
        draw.text((REPORT_WIDTH // 2, top + index * 38), line, font=_font(24), fill=0, anchor="mt", stroke_width=1)
    stamp_y = top + len(ENCOURAGEMENT) * 38 + 40
    draw.rectangle((64, stamp_y, 511, stamp_y + 168), outline=0, width=8)
    draw.text((REPORT_WIDTH // 2, stamp_y + 26), "CarpeDM", font=_font(78), fill=0, anchor="mt", stroke_width=2)
    draw.text((REPORT_WIDTH // 2, stamp_y + 120), "오늘의 당신을 응원합니다", font=_font(25), fill=0, anchor="mt", stroke_width=1)


def render_report(report: Mapping[str, object], *, name: str, team: str,
                  photo: Image.Image | None = None, photo_is_sample: bool = False) -> Image.Image:
    """Render a 576-dot 1-bit receipt from verified normalized source fields."""
    sample = report.get("source") == "demo_sample" and report.get("sample") is True
    if report.get("status") != "available" or (report.get("source") != "mirrorting" and not sample):
        raise ReportError("REPORT_NOT_FOUND")
    if not report.get("sessionId") or not report.get("reportId"):
        raise ReportError("INVALID_RESPONSE")
    try:
        title_font, section_font, body_font, small_font = _font(38), _font(30), _font(28), _font(24)
    except BadgeError as exc:
        raise ReportError("REPORT_RENDER_FAILED") from exc

    width, margin = REPORT_WIDTH, 34
    draw = ImageDraw.Draw(Image.new("L", (1, 1), 255))
    text_runs, rules = [], []

    def text(position, value, font):
        text_runs.append((position, value, font))

    def centered(value, top, font):
        text(((width - draw.textlength(value, font=font)) / 2, top), value, font)

    centered("4-Fit MirrorTing", 22, small_font)
    centered("오늘의 나를, 한 장에.", 54, title_font)
    centered("시연용 예시 · 실제 체험 기록 아님" if sample else "MY DAY / MY RECORD", 110, small_font)
    y = 154
    photo_position = None
    if photo is not None:
        photo = thermal_photo(photo, (480, 640))
        photo_position = ((width - photo.width) // 2, y)
        y += photo.height + 16
        centered(("샘플 캐릭터 사진 · 인화 품질 확인" if photo_is_sample else "직접 촬영한 사진 · 체험 기록은 예시") if sample else "오늘의 기념사진", y, small_font)
        y += 48
        y += KEEPSAKE_HEIGHT + 32

    def paragraph(value, font=body_font, *, center=False):
        nonlocal y
        if not value:
            return
        for part in _wrapped(draw, value, font, width - 2 * margin):
            if center:
                centered(part, y, font)
            else:
                text((margin, y), part, font)
            y += font.size + 10
        y += 8

    def section(label, values):
        nonlocal y
        if not values:
            return
        y += 12
        rules.append(y)
        text((margin, y + 18), label, small_font)
        y += 62
        for value in values:
            paragraph(value)

    paragraph(f"{_text(name, limit=30)} · {_text(team, limit=40)}", center=True)
    paragraph("RECORD / " + str(report["sessionId"]), small_font, center=True)
    if report.get("modeMinutes") in (5, 10):
        paragraph(f"대화 체험 / {report['modeMinutes']}분 모드", small_font, center=True)

    headline = report.get("headline") or {}
    if isinstance(headline, Mapping):
        if headline.get("sentence"):
            y += 16
            paragraph(_text(headline["sentence"]), section_font, center=True)
        paragraph(_text(headline.get("context")), small_font, center=True)
    score = report.get("totalScore")
    score_label = "미측정" if score is None else f"{float(score):g}점"
    if report.get("grade"):
        score_label += " · " + _text(report['grade'], limit=40)
    y += 12
    paragraph(score_label, title_font, center=True)

    fits = report.get("fitScores") or {}
    if not isinstance(fits, Mapping):
        raise ReportError("INVALID_RESPONSE")
    y += 12
    rules.append(y)
    text((margin, y + 18), "4-Fit / 대화의 인상", small_font)
    y += 62
    column_width = (width - 2 * margin - 28) // 2
    row_top = row_bottom = y
    for index, (key, fallback) in enumerate(zip(_SCORED_FITS, ("응답", "목소리", "표정", "자세"))):
        fit = fits.get(key, {})
        if not isinstance(fit, Mapping):
            raise ReportError("INVALID_RESPONSE")
        if index % 2 == 0:
            row_top = row_bottom
        x = margin + (index % 2) * (column_width + 28)
        item_y = row_top
        label = _text(fit.get("label"), limit=60) or fallback
        value = "미측정" if fit.get("score") is None else f"{float(fit['score']):g}점"
        if fit.get("provisional"):
            value += " (참고 지표)"
        for value, font in ((f"{label}: {value}", body_font), (_text(fit.get("summary")), small_font)):
            if not value:
                continue
            for part in _wrapped(draw, value, font, column_width):
                text((x, item_y), part, font)
                item_y += font.size + 10
        row_bottom = max(row_bottom, item_y + 22)
    y = row_bottom
    eye = fits.get("eye")
    if isinstance(eye, Mapping) and (observation := _text(eye.get("summary"))):
        paragraph("시선 관찰 / 점수 제외", small_font)
        paragraph(observation, small_font)

    ending = report.get("dayEnding") or {}
    reflection = list(report.get("strengths") or [])
    if isinstance(ending, Mapping) and ending.get("text"):
        reflection.append(_text(ending["text"]))
    section("오늘 남은 장면", reflection)
    next_steps = list(report.get("improvements") or [])
    coaching = report.get("coaching") or []
    if isinstance(coaching, list):
        for item in coaching[:5]:
            if not isinstance(item, Mapping):
                continue
            issue, suggestion = _text(item.get("issue")), _text(item.get("suggestion"))
            if suggestion:
                next_steps.append(f"{issue}\n{suggestion}" if issue else suggestion)
    section("다음 대화에서는", next_steps)
    tip = career_tip(str(report["sessionId"]))
    section("TIP", [tip["title"], tip["body"]])
    y += 12
    paragraph("미측정은 0점이 아니며, 참고 지표와 시선 관찰은 보조 피드백입니다. 이번 체험의 기록으로 읽어주세요.", small_font)
    rules.append(y + 10)
    centered("오늘의 기록을 오래 간직해주세요.", y + 26, small_font)
    canvas = Image.new("L", (width, y + 74), 255)
    draw = ImageDraw.Draw(canvas)
    if photo_position is not None:
        canvas.paste(photo, photo_position)
        draw_keepsake(draw, photo_position[1] + photo.height + 64)
    for rule_y in rules:
        for x in range(margin, width - margin, 14):
            draw.line((x, rule_y, min(x + 8, width - margin), rule_y), fill=0, width=2)
    for position, value, font in text_runs:
        draw.text(position, value, font=font, fill=0)
    return canvas.point(lambda pixel: 255 if pixel > 127 else 0).convert("1")
