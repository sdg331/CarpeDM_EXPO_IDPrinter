"""배지 렌더 · 발급 엔드포인트 테스트 — 프린터 없이 screen 백엔드로 끝까지 돈다."""

from pathlib import Path

import pytest
from fastapi import HTTPException

from backend.badge import BadgeError, render_badge
from backend.printing import SCREEN_OUT, backend_name, print_badge, printer_status

ROOT = Path(__file__).resolve().parent.parent
NEEDS_ASSETS = not (ROOT / "assets" / "characters" / "print" / "char_01_print.png").exists()
pytestmark = pytest.mark.skipif(NEEDS_ASSETS, reason="인쇄 자산 없음 — make_print_assets.py 먼저")


def test_배지_크기와_모드():
    """576×808 · 1비트 — 80mm 감열지 72×101mm 의 도트 수 그대로."""
    img = render_badge("김지연", "개발팀", "char_01", "2026-4181")
    assert img.size == (576, 808)
    assert img.mode == "1"


@pytest.mark.parametrize("name", ["가", "김지연", "남궁수리부엉이", "가나다라마바사아자차"])
def test_이름_길이_전범위(name):
    """1~10자 어디서도 렌더가 죽지 않아야 한다. 폭 초과는 자동 축소가 막는다."""
    img = render_badge(name, "마케팅팀", "char_02", "2026-0001")
    assert img.size == (576, 808)


def test_없는_캐릭터는_명확히_실패():
    with pytest.raises(BadgeError):
        render_badge("김지연", "개발팀", "char_99", "2026-0001")


def test_스크린_백엔드_왕복(tmp_path, monkeypatch):
    """기본(screen) 백엔드 — 파일이 실제로 써지는가."""
    assert backend_name() == "screen"          # 환경변수 미지정 시의 기본값
    img = render_badge("테스트", "디자인팀", "char_03", "2026-7777")
    result = print_badge(img)
    assert result["backend"] == "screen"
    assert SCREEN_OUT.exists()
    st = printer_status()
    assert st["ready"] is True


def test_발급_엔드포인트_직접호출():
    """httpx 없이 엔드포인트 함수를 직접 부른다. STATE 는 수동 주입."""
    from backend import app as app_module
    from backend.app import IssueRequest, issue
    from backend.face import Prototypes

    proto_path = ROOT / "assets" / "prototypes.npz"
    if not proto_path.exists():
        pytest.skip("prototypes.npz 없음")
    app_module.STATE["proto"] = Prototypes.load(proto_path)

    r = issue(IssueRequest(name="김지연", dept="개발팀",
                           char_id="char_01", emp_no="2026-4181"))
    assert r["ok"] is True and r["backend"] == "screen"

    with pytest.raises(HTTPException):
        issue(IssueRequest(name="김지연", dept="개발팀",
                           char_id="char_99", emp_no="2026-4181"))
