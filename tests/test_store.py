from pathlib import Path

from backend.store import KioskStore


def make_store(tmp_path: Path) -> KioskStore:
    store = KioskStore(tmp_path / "kiosk.sqlite3")
    store.init()
    return store


def test_session_ids_are_backend_owned_and_increment(tmp_path):
    store = make_store(tmp_path)
    first = store.create_session(
        name="김지연", team_id="ai", ai_mode="A", char_id="char_01"
    )
    second = store.create_session(
        name="홍길동", team_id="design", ai_mode="A", char_id="char_02"
    )

    assert first["session_id"].startswith("MW")
    assert len(first["session_id"]) == 12
    assert int(second["session_id"][-4:]) == int(first["session_id"][-4:]) + 1


def test_reissuing_card_disconnects_previous_session(tmp_path):
    store = make_store(tmp_path)
    a = store.create_session(
        name="A", team_id="ai", ai_mode="A", char_id="char_01"
    )
    b = store.create_session(
        name="B", team_id="design", ai_mode="A", char_id="char_02"
    )

    store.bind_card(
        session_id=a["session_id"], card_uid="04AABBCC", operation_id="op-register-a"
    )
    assert store.resolve_card("04AABBCC")["session_id"] == a["session_id"]

    store.bind_card(
        session_id=b["session_id"], card_uid="04AABBCC", operation_id="op-register-b"
    )
    resolved = store.resolve_card("04AABBCC")
    assert resolved["session_id"] == b["session_id"]


def test_operation_result_is_durable_for_idempotency(tmp_path):
    store = make_store(tmp_path)
    session = store.create_session(
        name="김지연", team_id="ai", ai_mode="A", char_id="char_01"
    )
    store.begin_operation(
        "op-12345678", kind="badge_print", session_id=session["session_id"]
    )
    expected = {"status": "success", "printJobId": "op-12345678"}
    store.finish_operation(
        "op-12345678",
        kind="badge_print",
        status="success",
        result=expected,
    )

    operation = store.get_operation("op-12345678", "badge_print")
    assert operation["status"] == "success"
    assert operation["result"] == expected


def test_retryable_operation_reuses_same_session(tmp_path):
    store = make_store(tmp_path)
    session = store.create_session(
        name="김지연", team_id="ai", ai_mode="A", char_id="char_01"
    )
    store.begin_operation(
        "op-nfc-12345678", kind="nfc_register", session_id=session["session_id"]
    )
    store.finish_operation(
        "op-nfc-12345678",
        kind="nfc_register",
        status="retryable_error",
        error_code="NFC_TIMEOUT",
        retryable=True,
    )

    restarted = store.restart_operation("op-nfc-12345678", kind="nfc_register")
    assert restarted["status"] == "running"
    assert restarted["session_id"] == session["session_id"]
