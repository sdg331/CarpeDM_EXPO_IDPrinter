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


def test_registration_claim_and_session_creation_are_one_transaction(tmp_path):
    from concurrent.futures import ThreadPoolExecutor

    store = make_store(tmp_path)
    def create():
        return store.create_session(name='방문객', team_id='ai', ai_mode='A', char_id='char_01', operation_id='same-registration')
    with ThreadPoolExecutor(max_workers=6) as pool:
        results = list(pool.map(lambda _: create(), range(6)))
    assert len({result['session_id'] for result in results}) == 1
    assert sum(result['claimed'] for result in results) == 1


def test_bridge_requires_current_card_and_rejects_cross_visitor_report(tmp_path):
    import pytest
    from backend.store import OperationConflict

    store = make_store(tmp_path)
    first = store.create_session(name='이전', team_id='ai', ai_mode='A', char_id='char_01')['session_id']
    second = store.create_session(name='다음', team_id='ai', ai_mode='A', char_id='char_01')['session_id']
    store.bind_card(session_id=first, card_uid='AABBCCDD', operation_id='card-first')
    expected = store.link_mirrorting(session_id=first, card_uid='AABBCCDD', mirror_session_id=10, access_token='private-token')
    assert store.link_mirrorting(session_id=first, card_uid='AABBCCDD', mirror_session_id=10, access_token='private-token') == expected
    assert 'access_token' not in expected
    store.bind_card(session_id=second, card_uid='AABBCCDD', operation_id='card-second')
    with pytest.raises(OperationConflict):
        store.link_mirrorting(session_id=first, card_uid='AABBCCDD', mirror_session_id=10, access_token='private-token')
    with pytest.raises(OperationConflict):
        store.link_mirrorting(session_id=second, card_uid='AABBCCDD', mirror_session_id=10, access_token='private-token')
    store.link_mirrorting(session_id=second, card_uid='AABBCCDD', mirror_session_id=11, access_token='next-token')
    assert store.get_mirrorting_link(second)['mirror_session_id'] == 11


def test_retention_removes_personal_data_but_keeps_unknown_print_guard(tmp_path):
    import sqlite3
    import pytest
    from backend.store import OperationConflict, SessionNotFound

    store = make_store(tmp_path)
    session = store.create_session(name='삭제예정', team_id='ai', ai_mode='A', char_id='char_01')['session_id']
    store.bind_card(session_id=session, card_uid='AABBCCDD', operation_id='private-card')
    store.link_mirrorting(session_id=session, card_uid='AABBCCDD', mirror_session_id=10, access_token='erase-token')
    store.claim_operation('old-print', kind='badge_print', session_id=session, unique_session=True)
    store.finish_operation('old-print', kind='badge_print', status='unknown', error_code='UNKNOWN_OUTCOME')
    with sqlite3.connect(store.path) as con:
        con.execute("UPDATE sessions SET created_at='2000-01-01T00:00:00+00:00'")
    purged = store.purge_expired()
    assert purged == {'sessions': 1, 'bindings': 1, 'links': 1}
    assert store.resolve_card('AABBCCDD') is None
    with pytest.raises(SessionNotFound):
        store.get_session(session)
    guarded = store.claim_operation('different-print', kind='badge_print', session_id=session, unique_session=True)
    assert guarded['claimed'] is False and guarded['status'] == 'unknown'
    with pytest.raises(OperationConflict):
        store.resolve_unknown_operation('old-print', outcome='not_printed')
    with sqlite3.connect(store.path) as con:
        assert con.execute('SELECT name,profile_id FROM sessions').fetchone() == ('', None)
        assert con.execute('SELECT COUNT(*) FROM mirrorting_links').fetchone()[0] == 0


def test_operator_confirmation_is_explicit_and_not_repeatable(tmp_path):
    import pytest
    from backend.store import OperationConflict

    store = make_store(tmp_path)
    session = store.create_session(name='방문객', team_id='ai', ai_mode='A', char_id='char_01')['session_id']
    store.bind_card(session_id=session, card_uid='AABBCCDD', operation_id='current-card')
    store.claim_operation('unknown-print', kind='badge_print', session_id=session, unique_session=True)
    store.recover_interrupted_operations()
    safe_retry = store.resolve_unknown_operation('unknown-print', outcome='not_printed')
    assert safe_retry['status'] == 'retryable_error'
    assert store.claim_operation('unknown-print', kind='badge_print', session_id=session, unique_session=True)['claimed']
    store.finish_operation('unknown-print', kind='badge_print', status='unknown')
    confirmed = store.resolve_unknown_operation('unknown-print', outcome='printed')
    assert confirmed['status'] == 'success'
    assert confirmed['result']['status'] == 'confirmed'
    assert confirmed['result']['completionConfirmed'] is True
    with pytest.raises(OperationConflict):
        store.resolve_unknown_operation('unknown-print', outcome='not_printed')
