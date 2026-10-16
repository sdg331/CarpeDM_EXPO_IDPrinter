"""Dedicated-card photo permission, real QR pixels, and durable print safety."""

from concurrent.futures import ThreadPoolExecutor
from io import BytesIO
import threading

import cv2
import numpy as np
import pytest
from fastapi.testclient import TestClient
from PIL import Image

import backend.app as kiosk
from backend.printing import PREVIEWS, PrintError
from backend.profile import ProfileStore
from backend.store import KioskStore
from backend.souvenir import introduction_url, qr_image, render_souvenir

URL = "https://example.org/mirrorting"
UID = "04AABBCC"


@pytest.fixture
def setup(monkeypatch, tmp_path):
    store = KioskStore(tmp_path / "test.sqlite3")
    store.init()
    monkeypatch.setattr(kiosk, "STORE", store)
    monkeypatch.setitem(kiosk.STATE, "souvenirs", ProfileStore(ttl_seconds=600, max_items=8))
    monkeypatch.setattr(kiosk, "read_card_uid", lambda _: UID)
    monkeypatch.setenv("KIOSK_SOUVENIR_CARD_UID", UID)
    monkeypatch.setenv("KIOSK_SOUVENIR_QR_URL", URL)
    monkeypatch.setenv("KIOSK_PRINT", "screen")
    return store, TestClient(kiosk.app, base_url="http://127.0.0.1", client=("127.0.0.1", 51000))


def photo_bytes():
    data = BytesIO()
    Image.new("RGB", (720, 960), "#acb7c1").save(data, format="JPEG")
    return data.getvalue()


def grant(client, operation="photo-card-read"):
    response = client.post("/api/nfc/resolve", json={"operationId": operation, "purpose": "souvenir"})
    assert response.status_code == 200
    return response.json()


def test_reserved_card_does_not_need_a_visitor_or_mirrorting(setup):
    store, client = setup
    permission = grant(client)
    assert permission["kind"] == "souvenir"
    assert "sessionId" not in permission and UID not in str(permission)
    assert grant(client) == permission
    # The ordinary checkout reader recognizes the same special card too.
    assert client.post("/api/nfc/resolve", json={"operationId": "normal-checkout-read"}).json()["kind"] == "souvenir"
    assert store.resolve_card(UID) is None
    qr = client.get(permission["qrPreviewUrl"])
    assert qr.headers["cache-control"].startswith("no-store")
    pixels = np.array(Image.open(BytesIO(qr.content)).convert("L"))
    assert cv2.QRCodeDetector().detectAndDecode(pixels)[0] == URL


def test_direct_photo_needs_no_card_or_qr_and_prints_once(setup, monkeypatch):
    store, client = setup
    monkeypatch.setenv("KIOSK_SOUVENIR_CARD_UID", "")
    monkeypatch.setenv("KIOSK_SOUVENIR_QR_URL", "")
    monkeypatch.setattr(kiosk, "read_card_uid", lambda _: pytest.fail("Direct photos must not read NFC"))
    body = {"operationId": "direct-photo-visitor"}
    result = client.post("/api/souvenirs/start", json=body)
    assert result.status_code == 200
    permission = result.json()
    assert permission["kind"] == "souvenir" and permission["qrPreviewUrl"] is None
    assert "sessionId" not in permission
    assert client.post("/api/souvenirs/start", json=body).json() == permission
    path = f"/api/souvenirs/{permission['photoPass']}/print"
    first = client.post(path, files={"frame": ("photo.jpg", photo_bytes())})
    assert first.status_code == 200 and first.json()["status"] == "preview"
    assert client.post(path, files={"frame": ("photo.jpg", photo_bytes())}).json() == first.json()
    image_response = client.get(first.json()["previewUrl"])
    image = Image.open(BytesIO(image_response.content))
    assert image.width == 576 and image.mode == "1"
    assert store.resolve_card(UID) is None
    # Cancellation invalidates the grant and deletes the in-memory preview.
    client.delete(f"/api/souvenirs/{permission['photoPass']}")
    assert client.get(first.json()["previewUrl"]).status_code == 410


def test_direct_photo_rejects_foreign_origin_and_unresolved_print(setup):
    store, client = setup
    body = {"operationId": "direct-photo-security"}
    assert client.post("/api/souvenirs/start", json=body,
                       headers={"Origin": "https://untrusted.example"}).status_code == 403
    store.claim_operation("souvenir-uncertain-direct", kind="souvenir_print", session_id=None)
    store.finish_operation("souvenir-uncertain-direct", kind="souvenir_print", status="unknown",
                           error_code="UNKNOWN_OUTCOME")
    response = client.post("/api/souvenirs/start", json=body)
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "SOUVENIR_PRINT_PENDING"


def test_explicit_checkout_rehearsal_prints_uploaded_photo_and_labels_the_example(setup, monkeypatch):
    _, client = setup
    captured = []
    original = kiosk.render_report

    def render_example(report, **kwargs):
        assert report["source"] == "demo_sample" and report["sample"] is True
        assert kwargs["photo"].size == (720, 960)
        captured.append(True)
        return original(report, **kwargs)

    monkeypatch.setattr(kiosk, "render_report", render_example)
    monkeypatch.setattr(kiosk, "read_card_uid", lambda _: pytest.fail("Rehearsal must not read a card"))
    permission = client.post("/api/souvenirs/start", json={
        "operationId": "explicit-checkout-rehearsal", "purpose": "rehearsal",
    }).json()
    assert permission["qrPreviewUrl"] is None
    path = f"/api/souvenirs/{permission['photoPass']}/print"
    first = client.post(path, files={"frame": ("real-photo.jpg", photo_bytes())})
    assert first.status_code == 200 and first.json()["status"] == "preview"
    assert client.post(path, files={"frame": ("real-photo.jpg", photo_bytes())}).json() == first.json()
    assert captured == [True]


def test_menu_reset_cancels_old_card_read_before_it_can_resolve(setup, monkeypatch):
    store, client = setup
    started, release = threading.Event(), threading.Event()

    def read_pending(_timeout):
        started.set()
        assert release.wait(5)
        return UID

    monkeypatch.setattr(kiosk, "read_card_uid", read_pending)
    with ThreadPoolExecutor(max_workers=1) as pool:
        pending = pool.submit(client.post, "/api/nfc/resolve", json={"operationId": "previous-visitor-read"})
        try:
            assert started.wait(5)
            assert client.post("/api/nfc/reset").json() == {"ok": True}
        finally:
            release.set()
        response = pending.result(timeout=5)
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "NFC_READ_CANCELLED"
    assert store.resolve_card(UID) is None
    # A fresh read still works after the reset.
    monkeypatch.setattr(kiosk, "read_card_uid", lambda _: UID)
    assert grant(client, "new-visitor-read")["kind"] == "souvenir"


def test_wrong_card_and_missing_qr_fail_without_photo_permission(setup, monkeypatch):
    _, client = setup
    monkeypatch.setattr(kiosk, "read_card_uid", lambda _: "04998877")
    result = client.post("/api/nfc/resolve", json={"operationId": "wrong-photo-card", "purpose": "souvenir"})
    assert result.status_code == 403 and result.json()["error"]["code"] == "SOUVENIR_CARD_REQUIRED"
    monkeypatch.setattr(kiosk, "read_card_uid", lambda _: UID)
    monkeypatch.setenv("KIOSK_SOUVENIR_QR_URL", "")
    result = client.post("/api/nfc/resolve", json={"operationId": "missing-photo-url"})
    assert result.status_code == 503 and result.json()["error"]["code"] == "SOUVENIR_NOT_CONFIGURED"


def test_reserved_card_cannot_be_bound_to_an_employee(setup, monkeypatch):
    store, client = setup
    monkeypatch.setitem(kiosk.STATE, "proto", type("Proto", (), {"ids": ["char_01"]})())
    response = client.post("/api/nfc/register", json={
        "operationId": "reserved-card-registration", "name": "점검자", "teamId": "ai",
        "aiMode": "A", "result": {"kind": "A", "characterId": "char_01"},
    })
    assert response.status_code == 409 and response.json()["error"]["code"] == "SOUVENIR_CARD"
    assert store.resolve_card(UID) is None


def test_photo_endpoints_keep_local_and_origin_restrictions(setup):
    _, client = setup
    permission = grant(client)
    remote = TestClient(kiosk.app, client=("192.168.1.20", 50000))
    assert remote.get(permission["qrPreviewUrl"]).status_code == 403
    assert remote.delete(f"/api/souvenirs/{permission['photoPass']}").status_code == 403
    assert client.post(f"/api/souvenirs/{permission['photoPass']}/print", files={"frame": ("photo.jpg", photo_bytes())}, headers={"Origin": "https://untrusted.example"}).status_code == 403


def test_expired_or_cancelled_permission_cannot_print(setup, monkeypatch):
    store, client = setup
    clock = [0]
    monkeypatch.setitem(kiosk.STATE, "souvenirs", ProfileStore(ttl_seconds=10, clock=lambda: clock[0]))
    permission = grant(client)
    clock[0] = 11
    path = f"/api/souvenirs/{permission['photoPass']}"
    assert client.get(path + "/qr").status_code == 410
    assert client.post(path + "/print", files={"frame": ("photo.jpg", photo_bytes())}).status_code == 410
    assert store.get_operation(permission["printJobId"]) is None
    permission = grant(client, "fresh-photo-card")
    path = f"/api/souvenirs/{permission['photoPass']}"
    client.delete(path)
    assert client.post(path + "/print", files={"frame": ("photo.jpg", photo_bytes())}).status_code == 410


def test_real_photo_receipt_decodes_qr_and_replays_without_reprinting(setup):
    store, client = setup
    permission = grant(client)
    path = f"/api/souvenirs/{permission['photoPass']}"
    response = client.post(path + "/print", files={"frame": ("photo.jpg", photo_bytes())})
    assert response.status_code == 200
    printed = response.json()
    assert printed["status"] == "preview" and printed["physicalOutput"] is False
    preview = client.get(printed["previewUrl"])
    image = Image.open(BytesIO(preview.content))
    assert image.mode == "1" and image.width == 576
    assert cv2.QRCodeDetector().detectAndDecode(np.array(image.convert("L")))[0] == URL
    assert client.post(path + "/print", files={"frame": ("photo.jpg", photo_bytes())}).json() == printed
    assert store.get_operation(permission["printJobId"])["session_id"] is None
    assert "frame" not in store.get_operation(permission["printJobId"]) and store.resolve_card(UID) is None
    client.delete(path)
    assert client.get(printed["previewUrl"]).status_code == 410


def test_parallel_requests_and_restart_cannot_submit_twice(setup, monkeypatch):
    store, client = setup
    permission = grant(client)
    calls = []
    monkeypatch.setattr(kiosk, "print_badge", lambda image: calls.append(image.size) or {
        "backend": "escpos", "status": "submitted", "physicalOutput": True,
    })
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: kiosk._print_souvenir(permission["photoPass"], photo_bytes()), range(2)))
    assert len(calls) == 1
    assert any(isinstance(result, dict) and result["status"] == "submitted" for result in results)
    store.claim_operation("souvenir-restart-case", kind="souvenir_print", session_id=None)
    store.recover_interrupted_operations()
    assert store.get_operation("souvenir-restart-case")["status"] == "unknown"
    store.resolve_unknown_operation("souvenir-restart-case", outcome="printed")
    assert store.get_operation("souvenir-restart-case")["result"]["completionConfirmed"] is True


def test_safe_failure_retries_but_ambiguous_output_stays_locked(setup, monkeypatch):
    store, client = setup
    permission = grant(client)
    other_permission = grant(client, "another-photo-pass")
    calls = []
    def unavailable(image):
        calls.append(image)
        raise PrintError("offline before device", retryable=True)
    monkeypatch.setattr(kiosk, "print_badge", unavailable)
    kiosk._print_souvenir(permission["photoPass"], photo_bytes())
    assert store.get_operation(permission["printJobId"])["status"] == "retryable_error"
    def uncertain(image):
        calls.append(image)
        raise PrintError("device disconnected")
    monkeypatch.setattr(kiosk, "print_badge", uncertain)
    kiosk._print_souvenir(permission["photoPass"], photo_bytes())
    kiosk._print_souvenir(permission["photoPass"], photo_bytes())
    assert len(calls) == 2 and store.get_operation(permission["printJobId"])["status"] == "unknown"
    another_print = kiosk._print_souvenir(other_permission["photoPass"], photo_bytes())
    assert another_print.status_code == 409 and b"SOUVENIR_PRINT_PENDING" in another_print.body
    assert len(calls) == 2 and store.get_operation(other_permission["printJobId"]) is None
    blocked = client.post("/api/nfc/resolve", json={"operationId": "new-visitor-photo"})
    assert blocked.status_code == 409 and blocked.json()["error"]["code"] == "SOUVENIR_PRINT_PENDING"
    store.resolve_unknown_operation(permission["printJobId"], outcome="not_printed")
    assert store.get_operation(permission["printJobId"])["status"] == "retryable_error"


def test_invalid_upload_cannot_claim_a_print(setup):
    store, client = setup
    permission = grant(client)
    path = f"/api/souvenirs/{permission['photoPass']}/print"
    assert client.post(path, files={"frame": ("bad.jpg", b"not an image")}).status_code == 400
    assert client.post(path, files={"frame": ("big.jpg", b"x" * (kiosk.MAX_UPLOAD + 1))}).status_code == 413
    assert store.get_operation(permission["printJobId"]) is None


@pytest.mark.parametrize("url", ["", "javascript:alert(1)", "https://user:secret@example.org", "https://example.org:bad", "https://example.org/\n", "https://example.org/" + "x" * 200])
def test_qr_destination_boundary_rejects_invalid_addresses(url):
    with pytest.raises(ValueError):
        introduction_url(url)


def test_qr_has_integer_modules_and_photo_is_contained_instead_of_cropped():
    qr = qr_image(URL)
    assert qr.mode == "1" and qr.width <= 304
    assert np.all(np.array(qr.convert("L"))[:16] == 255)
    photo = Image.new("RGB", (960, 720), "white")
    photo.paste("black", (0, 0, 960, 20))
    image = render_souvenir(photo, URL)
    # Full landscape image scales to 512 x 384; top and bottom are both retained.
    assert image.width == 576 and image.mode == "1"
    assert np.array(image.convert("L"))[155, 50] == 0
    assert np.array(image.convert("L"))[530, 50] == 255
    qr_y = 152 + 384 + 32 + 224
