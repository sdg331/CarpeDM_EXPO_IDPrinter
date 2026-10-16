"""MirrorTing boundary tests: ownership, pending state, and truthful receipt."""

import httpx
import pytest

from backend.reports import (
    ReportError,
    fetch_mirrorting_report,
    normalize_report,
    render_report,
)


UPSTREAM = "http://127.0.0.1:8001"
MIRROR_ID = 42
KIOSK_ID = "MW2610030001"


def upstream_report(**overrides):
    body = {
        "session_id": MIRROR_ID,
        "total_score": 78.4,
        "grade": "성장",
        "mode": 5,
        "fit_scores": {
            "response": {"score": 78.4, "label": "응답", "summary": "요점을 먼저 말했어요."},
            "voice": {"score": None, "label": "목소리", "summary": "측정되지 않았어요."},
            "expression": {"score": 71.0, "label": "표정", "summary": "참고 지표예요.", "provisional": True},
            "eye": {"score": 80.0, "label": "시선", "summary": "관찰 신호", "observation": True},
        },
        "strengths": ["응답 — 결론을 먼저 전달했어요."],
        "improvements": ["다음에는 질문을 하나 더 건네 보세요."],
        "headline": {"sentence": "결론부터 말해 보세요.", "context": "응답에서 개선 여지가 있어요."},
        "day_ending": {"label": "오늘의 결말", "text": "대화를 마쳤어요."},
        "coaching": [{"issue": "말이 길었어요", "suggestion": "핵심을 한 문장으로 시작하세요.", "quote": "민감한 원문"}],
    }
    body.update(overrides)
    return body


def test_complete_report_uses_server_token_and_source_session_only():
    requested = []

    def handler(request):
        requested.append((str(request.url), request.headers.get("X-Session-Token")))
        if request.url.path.endswith("/progress"):
            return httpx.Response(200, json={"status": "completed", "stage": "done", "pct": 100})
        return httpx.Response(200, json=upstream_report())

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        result = fetch_mirrorting_report(
            KIOSK_ID, MIRROR_ID, "secret-capability", base_url=UPSTREAM, client=client
        )

    assert requested == [
        (f"{UPSTREAM}/api/sessions/{MIRROR_ID}/progress", "secret-capability"),
        (f"{UPSTREAM}/api/sessions/{MIRROR_ID}/report", "secret-capability"),
    ]
    assert result["reportId"] == str(MIRROR_ID)
    assert result["sessionId"] == KIOSK_ID
    assert result["strengths"] == ["응답 — 결론을 먼저 전달했어요."]
    assert result["fitScores"]["voice"]["score"] is None
    assert result["fitScores"]["expression"]["provisional"] is True
    assert "quote" not in result["coaching"][0]
    assert "scenario" not in result and "summary" not in result
    assert "secret-capability" not in str(result)


def test_analysis_pending_never_fetches_or_fabricates_a_report():
    paths = []

    def handler(request):
        paths.append(request.url.path)
        return httpx.Response(200, json={"status": "analyzing", "stage": "scoring", "pct": 35})

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(ReportError, match="REPORT_PENDING") as caught:
            fetch_mirrorting_report(KIOSK_ID, MIRROR_ID, "token", base_url=UPSTREAM, client=client)
    assert caught.value.retryable is True
    assert paths == [f"/api/sessions/{MIRROR_ID}/progress"]


def test_mismatched_upstream_session_is_rejected():
    with pytest.raises(ReportError, match="INVALID_RESPONSE"):
        normalize_report(KIOSK_ID, MIRROR_ID, upstream_report(session_id=MIRROR_ID + 1))


def test_invalid_upstream_auth_is_not_reported_as_missing_data():
    with httpx.Client(transport=httpx.MockTransport(lambda _: httpx.Response(403))) as client:
        with pytest.raises(ReportError, match="INTEGRATION_UNAUTHORIZED"):
            fetch_mirrorting_report(KIOSK_ID, MIRROR_ID, "wrong", base_url=UPSTREAM, client=client)


def test_unconfigured_or_userinfo_upstream_is_rejected_before_network():
    for base_url in ("", "http://user:pass@127.0.0.1:8001", "file:///tmp/report", "http://127.0.0.1:bad"):
        with pytest.raises(ReportError, match="INTEGRATION_PENDING"):
            fetch_mirrorting_report(KIOSK_ID, MIRROR_ID, "token", base_url=base_url)


def test_unmeasured_report_stays_unmeasured_and_can_render():
    report = normalize_report(
        KIOSK_ID,
        MIRROR_ID,
        upstream_report(total_score=None, grade=None, strengths=[], improvements=[], headline={}, day_ending={}),
    )
    assert report["totalScore"] is None
    assert report["strengths"] == []
    assert report["improvements"] == []
    try:
        image = render_report(report, name="김지연", team="AI팀")
    except ReportError as exc:
        if exc.code == "REPORT_RENDER_FAILED":
            pytest.skip("CI image has no CJK font; device font must be validated separately")
        raise
    assert image.mode == "1"
    assert image.width == 576
    assert image.height > 300


def test_real_report_sections_fit_a_receipt_without_coaching_quotes():
    report = normalize_report(KIOSK_ID, MIRROR_ID, upstream_report())
    try:
        image = render_report(report, name="김지연", team="AI팀")
    except ReportError as exc:
        if exc.code == "REPORT_RENDER_FAILED":
            pytest.skip("CI image has no CJK font; device font must be validated separately")
        raise
    assert image.mode == "1"
    assert image.width == 576
    assert image.height < 4300


def test_career_advice_is_stable_per_visitor_and_varies_across_visitors():
    from backend.career_tips import CAREER_TIPS, career_tip

    first = career_tip(KIOSK_ID)
    assert first == career_tip(KIOSK_ID)
    assert {career_tip(f"visitor-{i}")["id"] for i in range(200)} == {f"{i + 1:02d}" for i in range(len(CAREER_TIPS))}
    assert first["source"] == "동양미래대학교 취업지원센터"
    assert "첨삭" in first["note"]


def test_print_wrapping_keeps_short_words_together_without_losing_text():
    from PIL import Image, ImageDraw, ImageFont
    from backend.reports import _wrapped

    draw = ImageDraw.Draw(Image.new("L", (1, 1)))
    font = ImageFont.load_default(size=22)
    value = "업무의 방향과 완성 시점을 확인하면 좋아요."
    width = int(draw.textlength("업무의 방향과 완성", font=font))
    lines = _wrapped(draw, value, font, width)
    assert "".join(lines) == value
    assert any("좋아요." in line for line in lines)
    assert all(draw.textlength(line, font=font) <= width for line in lines)


def test_thermal_photo_keeps_subtle_midtones_distinct_without_losing_black_or_white():
    from PIL import Image, ImageStat
    from backend.reports import thermal_photo

    photo = Image.new("L", (1024, 768), 0)
    photo.paste(150, (128, 0, 512, 768))
    photo.paste(180, (512, 0, 896, 768))
    photo.paste(255, (896, 0, 1024, 768))
    original = photo.tobytes()
    result = thermal_photo(photo, (512, 640))
    darker = ImageStat.Stat(result.crop((80, 32, 240, 352))).mean[0]
    lighter = ImageStat.Stat(result.crop((272, 32, 432, 352))).mean[0]
    assert lighter - darker > 36
    assert result.crop((0, 0, 48, 384)).getextrema() == (0, 0)
    assert result.crop((464, 0, 512, 384)).getextrema() == (255, 255)
    assert result.mode == "1" and result.size == (512, 384)
    assert photo.tobytes() == original


def test_thermal_photo_respects_camera_orientation_and_preserves_the_whole_frame():
    from PIL import Image
    from backend.reports import thermal_photo

    photo = Image.new("RGB", (800, 400), "white")
    photo.paste("black", (0, 0, 80, 400))
    photo.getexif()[274] = 6
    result = thermal_photo(photo, (512, 640))
    assert result.mode == "1" and result.size == (320, 640)
    assert result.crop((0, 0, 320, 48)).getextrema() == (0, 0)
    assert result.crop((0, 592, 320, 640)).getextrema() == (255, 255)
    assert photo.size == (800, 400) and photo.getexif()[274] == 6


@pytest.mark.parametrize("size", [(400, 800), (800, 400)])
def test_report_keeps_entire_photo_and_prints_one_separate_teacher_tip(monkeypatch, size):
    from PIL import Image, ImageDraw, ImageFont
    import backend.reports as reports
    from backend.career_tips import career_tip

    monkeypatch.setattr(reports, "_font", lambda size: ImageFont.load_default(size=size))
    photo = Image.new("RGB", size, "white")
    pen = ImageDraw.Draw(photo)
    for x, y in [(0, 0), (size[0] - 32, 0), (0, size[1] - 32), (size[0] - 32, size[1] - 32)]:
        pen.rectangle((x, y, x + 31, y + 31), fill="black")
    drawn = []
    original = ImageDraw.ImageDraw.text
    def capture_text(draw, position, value, **kwargs):
        drawn.append(value)
        return original(draw, position, value, **kwargs)
    monkeypatch.setattr(ImageDraw.ImageDraw, "text", capture_text)
    report = normalize_report(KIOSK_ID, MIRROR_ID, upstream_report())
    image = render_report(report, name="김미래", team="AI팀", photo=photo)
    expected = reports.thermal_photo(photo, (480, 640))
    x = (576 - expected.width) // 2
    assert image.crop((x, 154, x + expected.width, 154 + expected.height)).tobytes() == expected.tobytes()
    assert image.mode == "1" and image.width == 576
    text = "".join(drawn)
    tip = career_tip(KIOSK_ID)
    assert text.count(tip["title"]) == 1
    assert "TIP" in drawn
    assert tip["source"] not in text and tip["note"] not in text
    assert "목소리: 미측정" in text
    assert drawn[-1] == "오늘의 기록을 오래 간직해주세요."


@pytest.mark.parametrize("content", ["긴 리포트 " * 100, "verbose report " * 100, "줄\n" * 250])
def test_maximum_accepted_report_renders_all_lines_and_footer(monkeypatch, content):
    from PIL import ImageDraw, ImageFont
    import backend.reports as reports

    # A deterministic scalable font keeps this regression active without OS fonts.
    monkeypatch.setattr(reports, "_font", lambda size: ImageFont.load_default(size=size))
    payload = upstream_report(
        strengths=[f"강점{i}: {content}" for i in range(8)],
        improvements=[f"연습{i}: {content}" for i in range(8)],
        headline={"sentence": content, "context": content},
        coaching=[{"issue": content, "suggestion": content} for _ in range(5)],
        day_ending={"label": "마지막 결말", "text": "마지막 기록 " + content},
    )
    report = normalize_report(KIOSK_ID, MIRROR_ID, payload)
    drawn = []
    original_text = ImageDraw.ImageDraw.text

    def record_text(draw, position, value, **kwargs):
        drawn.append((position, value, kwargs["font"]))
        return original_text(draw, position, value, **kwargs)

    monkeypatch.setattr(ImageDraw.ImageDraw, "text", record_text)
    image = render_report(report, name="김지연", team="AI팀")
    assert image.mode == "1" and image.width == 576
    assert image.height > 4300
    printed_text = "".join(value for _, value, _ in drawn)
    # All accepted strengths/improvements and the last section survive wrapping.
    for value in report["strengths"] + report["improvements"] + [report["dayEnding"]["text"]]:
        assert value.replace("\n", "") in printed_text
    assert drawn[-1][1] == "오늘의 기록을 오래 간직해주세요."
    assert drawn[-1][0][1] > 4300
    for (x, y), value, font in drawn:
        bounds = font.getbbox(value)
        assert x + bounds[2] <= image.width
        assert y + bounds[3] <= image.height
        assert font.size >= 24
    # Check real ink in the footer, not just a tall empty allocation.
    assert image.crop((34, image.height - 48, 542, image.height)).getextrema() == (0, 255)


@pytest.mark.parametrize("score", [None, 0, 100])
def test_editorial_receipt_preserves_feedback_without_boxes_or_tip_provenance(monkeypatch, score):
    from PIL import ImageDraw, ImageFont
    import backend.reports as reports

    monkeypatch.setattr(reports, "_font", lambda size: ImageFont.load_default(size=size))
    drawn, bar_outlines = [], []
    original_text = ImageDraw.ImageDraw.text
    original_rectangle = ImageDraw.ImageDraw.rectangle

    def record_text(draw, position, value, **kwargs):
        drawn.append(value)
        return original_text(draw, position, value, **kwargs)

    def record_rectangle(draw, bounds, **kwargs):
        if kwargs.get("outline") == 0 and kwargs.get("width") == 1:
            bar_outlines.append(bounds)
        return original_rectangle(draw, bounds, **kwargs)

    monkeypatch.setattr(ImageDraw.ImageDraw, "text", record_text)
    monkeypatch.setattr(ImageDraw.ImageDraw, "rectangle", record_rectangle)
    report = normalize_report(KIOSK_ID, MIRROR_ID, upstream_report(
        total_score=score,
        fit_scores={
            "response": {"score": score, "label": "응답", "summary": "원본 응답 해석"},
            "voice": {"score": None, "label": "목소리"},
            "expression": {"score": score, "label": "표정", "provisional": True},
            "eye": {"score": 83, "label": "시선", "summary": "원본 시선 관찰", "observation": True},
        },
        coaching=[{"issue": f"관찰{i}", "suggestion": f"연습{i}", "quote": "출력 금지 원문"} for i in range(5)],
    ))
    image = render_report(report, name="방문자", team="AI팀")
    text = "".join(drawn)
    for expected in ("원본 응답 해석", "원본 시선 관찰", "목소리: 미측정", "자세: 미측정", "참고 지표", "5분 모드", "미측정은 0점이 아니며", "TIP"):
        assert expected in text
    for index in range(5):
        assert f"관찰{index}" in text
        assert f"연습{index}" in text
    assert "83점" not in text and "출력 금지 원문" not in text
    assert bar_outlines == []
    assert "동양미래대학교 취업지원센터" not in text
    assert "첨삭" not in text and "짧게 정리" not in text and "출처" not in text
    assert "01 /" not in text and "관찰된 점:" not in text
    if score is not None:
        assert f"{score}점" in text
