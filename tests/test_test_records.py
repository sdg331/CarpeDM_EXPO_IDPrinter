import json

import backend.app as app
import backend.test_records as fixtures
from backend.store import KioskStore
from tests.test_reports import upstream_report


def setup_record(monkeypatch, tmp_path):
    store = KioskStore(tmp_path / "kiosk.sqlite3")
    store.init()
    session = store.create_session(name="검토자", team_id="ai", ai_mode="A", char_id="char_01")
    sid = session["session_id"]
    store.bind_card(session_id=sid, card_uid="04AABBCC", operation_id="seed-card-0001")
    folder = tmp_path / "test_records"
    folder.mkdir()
    (folder / f"{sid}.json").write_text(json.dumps({"expiresAt": 2000, "report": upstream_report(session_id=1)}))
    monkeypatch.setattr(app, "STORE", store)
    monkeypatch.setattr(fixtures, "TEST_RECORDS", folder)
    monkeypatch.setattr(fixtures.time, "time", lambda: 1000)
    monkeypatch.setenv("KIOSK_TEST_RECORDS", "1")
    monkeypatch.delenv("KIOSK_MIRRORTING_URL", raising=False)
    return store, sid


def test_explicit_record_requires_enabled_mode_and_current_card(monkeypatch, tmp_path):
    store, sid = setup_record(monkeypatch, tmp_path)
    result = app.get_report(sid)
    assert result["source"] == "local_test"
    assert result["sample"] is True
    assert result["reportId"] == f"TEST-{sid}"
    assert result["mirrorSessionId"] is None
    assert fixtures.load_test_report("MW0000000000") is None
    monkeypatch.setenv("KIOSK_TEST_RECORDS", "0")
    assert app.get_report(sid).status_code == 503
    monkeypatch.setenv("KIOSK_TEST_RECORDS", "1")
    store.release_session(sid)
    assert b"SESSION_REPLACED" in app.get_report(sid).body


def test_expired_record_cannot_be_used(monkeypatch, tmp_path):
    _, sid = setup_record(monkeypatch, tmp_path)
    monkeypatch.setattr(fixtures.time, "time", lambda: 2000)
    assert fixtures.load_test_report(sid) is None
    assert app.get_report(sid).status_code == 503


def test_real_link_takes_precedence_and_test_record_cannot_print(monkeypatch, tmp_path):
    store, sid = setup_record(monkeypatch, tmp_path)
    req = app.ReportPrintRequest(operationId="test-print-0001", sessionId=sid, reportId=f"TEST-{sid}")
    monkeypatch.setattr(app, "print_badge", lambda _: (_ for _ in ()).throw(AssertionError("Unexpected print")))
    result = app.print_session_report(req)
    assert result.status_code == 409
    assert b"TEST_REPORT_PREVIEW_ONLY" in result.body
    assert store.get_operation(req.operationId) is None
    store.link_mirrorting(session_id=sid, card_uid="04AABBCC", mirror_session_id=42, access_token="test-capability")
    assert b"INTEGRATION_PENDING" in app.get_report(sid).body
