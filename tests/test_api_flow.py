from PIL import Image

import backend.app as backend_app
from backend.printing import PrintError
from backend.store import KioskStore


class DummyProto:
    ids = ["char_01"]


def configure(monkeypatch, tmp_path):
    store = KioskStore(tmp_path / "kiosk.sqlite3")
    store.init()
    monkeypatch.setattr(backend_app, "STORE", store)
    monkeypatch.setitem(backend_app.STATE, "proto", DummyProto())
    monkeypatch.setattr(backend_app, "read_card_uid", lambda _: "04AABBCC")
    return store


def register_request(operation_id="nfc-operation-0001"):
    return backend_app.NfcRegisterRequest(
        operationId=operation_id,
        name="김지연",
        teamId="ai",
        aiMode="A",
        result=backend_app.MatchResultPayload(kind="A", characterId="char_01"),
    )


def test_nfc_registration_retry_returns_same_session(monkeypatch, tmp_path):
    configure(monkeypatch, tmp_path)

    first = backend_app.register_nfc(register_request())
    second = backend_app.register_nfc(register_request())

    assert first["status"] == "verified"
    assert second["status"] == "verified"
    assert first["sessionId"] == second["sessionId"]


def test_badge_print_same_operation_runs_printer_once(monkeypatch, tmp_path):
    configure(monkeypatch, tmp_path)
    registered = backend_app.register_nfc(register_request())
    calls = {"count": 0}

    monkeypatch.setattr(
        backend_app,
        "render_badge",
        lambda *args, **kwargs: Image.new("1", (10, 10), 1),
    )

    def fake_print(_image):
        calls["count"] += 1
        return {"backend": "screen", "path": "data/last_badge.png"}

    monkeypatch.setattr(backend_app, "print_badge", fake_print)
    req = backend_app.BadgePrintRequest(
        operationId="badge-operation-0001",
        sessionId=registered["sessionId"],
    )

    first = backend_app.print_session_badge(req)
    second = backend_app.print_session_badge(req)

    assert first["status"] == "success"
    assert second["status"] == "success"
    assert calls["count"] == 1


def test_ambiguous_print_failure_is_not_retried(monkeypatch, tmp_path):
    configure(monkeypatch, tmp_path)
    registered = backend_app.register_nfc(register_request())
    calls = {"count": 0}

    monkeypatch.setattr(
        backend_app,
        "render_badge",
        lambda *args, **kwargs: Image.new("1", (10, 10), 1),
    )

    def fail_print(_image):
        calls["count"] += 1
        raise PrintError("usb disconnected")

    monkeypatch.setattr(backend_app, "print_badge", fail_print)
    req = backend_app.BadgePrintRequest(
        operationId="badge-operation-0002",
        sessionId=registered["sessionId"],
    )

    first = backend_app.print_session_badge(req)
    second = backend_app.print_session_badge(req)

    assert first.status_code == 503
    assert second.status_code == 409
    assert calls["count"] == 1
