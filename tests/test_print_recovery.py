"""Recover exact pending receipts without repeating successful/device-uncertain jobs."""
from concurrent.futures import ThreadPoolExecutor
from io import BytesIO

import pytest
from fastapi.testclient import TestClient
from PIL import Image

import backend.app as kiosk
from backend.printing import PrintError
from backend.store import KioskStore


@pytest.fixture
def setup(monkeypatch, tmp_path):
    store = KioskStore(tmp_path / "recovery.sqlite3")
    store.init()
    monkeypatch.setattr(kiosk, "STORE", store)
    monkeypatch.setenv("KIOSK_PRINT", "screen")
    client = TestClient(kiosk.app, base_url="http://127.0.0.1", client=("127.0.0.1", 51000))
    return store, client


def pending(store, operation_id, *, kind="souvenir_print", image=True, status="unknown"):
    session = None
    if kind != "souvenir_print":
        session = store.create_session(name="점검자", team_id="ai", ai_mode="A", char_id="char_01")
        store.bind_card(session_id=session["session_id"], card_uid=operation_id.upper(), operation_id="nfc-" + operation_id)
    store.claim_operation(operation_id, kind=kind, session_id=session["session_id"] if session else None)
    if image:
        data = BytesIO()
        Image.new("1", (576, 96), 1).save(data, format="PNG")
        store.save_print_payload(operation_id, data.getvalue(), {"reportId": "42"} if kind == "report_print" else {})
    store.finish_operation(operation_id, kind=kind, status=status, error_code="UNKNOWN_OUTCOME", retryable=status == "retryable_error")
    return session


def recover(client, ids, batch="recovery-batch-0001", outcome="not_printed"):
    revisions = {row["operationId"]: row["revision"] for row in client.get("/api/print/recovery").json()["pending"]}
    return client.post("/api/print/recovery", json={
        "operationId": batch, "operationIds": ids, "outcome": outcome, "confirmed": True,
        "revisions": {op: revisions.get(op, "already-complete") for op in ids},
    })


def test_all_kinds_recover_once_and_release_report_card(setup, monkeypatch):
    store, client = setup
    ids = ["pending-badge-0001", "pending-report-0001", "pending-photo-0001"]
    sessions = [pending(store, op, kind=kind) for op, kind in zip(ids, ["badge_print", "report_print", "souvenir_print"])]
    calls = []
    monkeypatch.setattr(kiosk, "print_badge", lambda image: calls.append(image.tobytes()) or {"backend": "escpos"})
    listing = client.get("/api/print/recovery").json()
    assert len(listing["pending"]) == 3 and all(row["hasImage"] for row in listing["pending"])
    assert "점검자" not in str(listing) and "image_png" not in str(listing)
    response = recover(client, ids)
    assert response.status_code == 200
    assert [row["status"] for row in response.json()["results"]] == ["submitted"] * 3
    assert len(calls) == 3
    assert recover(client, ids).json() == response.json()
    assert recover(client, ids, "recovery-batch-0002").json()["results"][0]["status"] == "skipped"
    assert len(calls) == 3 and all(store.print_payload(op) is None for op in ids)
    assert store.active_card(sessions[0]["session_id"])
    assert not store.active_card(sessions[1]["session_id"])
    assert store.get_operation(ids[1])["result"]["reportId"] == "42"
    assert all(op["outcome"] == "not_printed" for op in _resolutions(store))


def _resolutions(store):
    with store._connect() as con:
        return [dict(row) for row in con.execute("SELECT * FROM operator_resolutions")]


def test_parallel_batches_cannot_repeat_a_successful_receipt(setup, monkeypatch):
    store, _ = setup
    pending(store, "parallel-photo-001")
    calls = []
    monkeypatch.setattr(kiosk, "print_badge", lambda image: calls.append(image.size) or {"backend": "escpos"})
    listing = kiosk.pending_print_recovery()["pending"]
    req = kiosk.PrintRecoveryRequest(operationId="parallel-recovery-001", operationIds=["parallel-photo-001"], outcome="not_printed", confirmed=True, revisions={row["operationId"]: row["revision"] for row in listing})
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: kiosk.recover_pending_prints(req), range(2)))
    assert len(calls) == 1 and results[0] == results[1]


def test_failure_stops_batch_and_same_batch_does_not_repeat_unknown_output(setup, monkeypatch):
    store, client = setup
    for op in ["first-photo-0001", "next-photo-0001"]:
        pending(store, op)
    calls = []
    def disconnect(image):
        calls.append(image.size)
        raise PrintError("connection lost")
    monkeypatch.setattr(kiosk, "print_badge", disconnect)
    result = recover(client, ["first-photo-0001", "next-photo-0001"])
    assert result.json()["results"] == [{"operationId": "first-photo-0001", "status": "unknown"}]
    recover(client, ["first-photo-0001", "next-photo-0001"])
    assert len(calls) == 1
    assert store.get_operation("next-photo-0001")["status"] == "unknown"
    assert store.print_payload("first-photo-0001") is not None


def test_restart_retains_receipt_and_already_printed_confirmation_does_not_print(setup, monkeypatch):
    store, client = setup
    pending(store, "restart-photo-001", status="retryable_error")
    store.claim_operation("restart-photo-001", kind="souvenir_print", session_id=None)
    reopened = KioskStore(store.path)
    reopened.init()
    reopened.recover_interrupted_operations()
    monkeypatch.setattr(kiosk, "STORE", reopened)
    monkeypatch.setattr(kiosk, "print_badge", lambda _: pytest.fail("must not print a confirmed receipt"))
    assert reopened.print_payload("restart-photo-001") is not None
    response = recover(client, ["restart-photo-001"], outcome="printed")
    assert response.json()["results"][0]["status"] == "confirmed"
    assert reopened.get_operation("restart-photo-001")["result"]["completionConfirmed"] is True
    assert reopened.print_payload("restart-photo-001") is None
    assert not reopened.unresolved_souvenir_print()


def test_legacy_missing_photo_unlocks_without_fabricating_a_print(setup, monkeypatch):
    store, client = setup
    pending(store, "old-photo-no-image", image=False)
    monkeypatch.setattr(kiosk, "print_badge", lambda _: pytest.fail("missing photo must not print"))
    result = recover(client, ["old-photo-no-image"])
    assert result.json()["results"][0]["status"] == "missing_image"
    assert store.get_operation("old-photo-no-image")["status"] == "retryable_error"
    assert not store.unresolved_souvenir_print()


def test_running_replaced_and_successful_jobs_stay_protected(setup, monkeypatch):
    store, client = setup
    session = pending(store, "replaced-badge-001", kind="badge_print")
    replacement = store.create_session(name="새방문", team_id="ai", ai_mode="A", char_id="char_01")
    store.bind_card(session_id=replacement["session_id"], card_uid="REPLACED-BADGE-001", operation_id="new-card-binding")
    store.claim_operation("running-photo-001", kind="souvenir_print", session_id=None)
    pending(store, "success-photo-001", status="success")
    monkeypatch.setattr(kiosk, "print_badge", lambda _: pytest.fail("ineligible jobs must not print"))
    result = recover(client, ["replaced-badge-001", "running-photo-001", "success-photo-001"])
    assert all(row["status"] == "skipped" for row in result.json()["results"])
    assert store.get_operation("running-photo-001")["status"] == "running"


def test_recovery_requires_local_origin_and_explicit_confirmation(setup):
    _, client = setup
    request = {"operationId": "test-batch-0001", "operationIds": ["pending-photo-001"], "outcome": "not_printed", "revisions": {"pending-photo-001": "test"}}
    assert client.post("/api/print/recovery", json=request).status_code == 422
    request["confirmed"] = False
    assert client.post("/api/print/recovery", json=request).status_code == 422
    request["confirmed"] = True
    assert client.post("/api/print/recovery", json=request, headers={"Origin": "https://untrusted.example"}).status_code == 403
    remote = TestClient(kiosk.app, client=("192.168.1.20", 51000))
    assert remote.get("/api/print/recovery").status_code == 403
    assert remote.post("/api/print/recovery", json=request).status_code == 403


def test_failed_device_submission_keeps_exact_image_but_success_deletes_it(setup, monkeypatch):
    store, _ = setup
    store.claim_operation("save-photo-before-usb", kind="souvenir_print", session_id=None)
    image = Image.new("1", (576, 80), 1)
    image.paste(0, (40, 20, 70, 60))
    def offline(_):
        assert store.print_payload("save-photo-before-usb") is not None
        raise PrintError("offline", retryable=True)
    monkeypatch.setattr(kiosk, "print_badge", offline)
    kiosk._submit_print("save-photo-before-usb", "souvenir_print", image)
    png, _ = store.print_payload("save-photo-before-usb")
    assert Image.open(BytesIO(png)).tobytes() == image.tobytes()
    store.claim_operation("save-photo-before-usb", kind="souvenir_print", session_id=None)
    monkeypatch.setattr(kiosk, "print_badge", lambda _: {"backend": "screen", "previewUrl": "/api/print/previews/test"})
    kiosk._submit_print("save-photo-before-usb", "souvenir_print", image)
    assert store.print_payload("save-photo-before-usb") is None


def test_pending_images_expire_with_local_retention(setup):
    store, _ = setup
    pending(store, "expired-photo-0001")
    with store._connect() as con:
        con.execute("UPDATE operations SET created_at='2000-01-01T00:00:00+00:00' WHERE operation_id='expired-photo-0001'")
    store.purge_expired(24)
    assert store.print_payload("expired-photo-0001") is None
    assert store.get_operation("expired-photo-0001")["status"] == "unknown"


def test_stale_second_batch_cannot_repeat_an_uncertain_first_batch(setup, monkeypatch):
    store, client = setup
    pending(store, "stale-photo-0001")
    row = client.get("/api/print/recovery").json()["pending"][0]
    calls = []
    def disconnect(image):
        calls.append(image.size)
        raise PrintError("lost after device access")
    monkeypatch.setattr(kiosk, "print_badge", disconnect)
    request = {"operationId": "stale-batch-0001", "operationIds": [row["operationId"]], "outcome": "not_printed", "confirmed": True,
               "revisions": {row["operationId"]: row["revision"]}}
    assert client.post("/api/print/recovery", json=request).json()["results"][0]["status"] == "unknown"
    request["operationId"] = "stale-batch-0002"
    assert client.post("/api/print/recovery", json=request).json()["results"][0]["status"] == "skipped"
    assert len(calls) == 1


def test_cannot_touch_device_if_recovery_image_cannot_be_saved(setup, monkeypatch):
    import sqlite3
    store, _ = setup
    store.claim_operation("queue-write-failure", kind="souvenir_print", session_id=None)
    def disk_full(*_):
        raise sqlite3.OperationalError("disk full")
    monkeypatch.setattr(store, "save_print_payload", disk_full)
    monkeypatch.setattr(kiosk, "print_badge", lambda _: pytest.fail("device must remain untouched"))
    response = kiosk._submit_print("queue-write-failure", "souvenir_print", Image.new("1", (576, 80), 1))
    assert response.status_code == 503
    assert store.get_operation("queue-write-failure")["status"] == "retryable_error"
