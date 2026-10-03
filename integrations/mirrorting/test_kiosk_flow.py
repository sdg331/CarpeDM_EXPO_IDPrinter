"""Companion endpoint tests, copied into MirrorTing by the prepared patch."""

from fastapi.testclient import TestClient
from pydantic import SecretStr

from app.api import nfc, sessions
from app.core.config import settings
from app.core.database import SessionLocal
from app.main import app
from app.models import RoleplaySession
from app.seed.run import seed
from app.services import nfc_bridge
from app.services.idprinter_bridge import BridgeError, CardSnapshot


CARD_UID = "04AABBCC"
KIOSK_ID = "MW2610030001"
CONSENT = {"agreed": True, "storage_policy": "none"}


class FakeBridge:
    session_id = KIOSK_ID
    fail_link = False
    links = []

    def __init__(self, _url, _token):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        pass

    def resolve(self, uid):
        assert uid == CARD_UID
        return CardSnapshot(uid=CARD_UID, kiosk_session_id=self.session_id)

    def link(self, snapshot, mirror_session_id, access_token):
        if self.fail_link:
            raise BridgeError("KIOSK_BRIDGE_UNAVAILABLE", retryable=True)
        self.links.append((snapshot, mirror_session_id, access_token))
        return {"ok": True, "status": "linked", "sessionId": snapshot.kiosk_session_id,
                "mirrorSessionId": mirror_session_id}


def _configured(monkeypatch):
    seed()
    FakeBridge.session_id = KIOSK_ID
    FakeBridge.fail_link = False
    FakeBridge.links = []
    monkeypatch.setattr(settings, "idprinter_base_url", "http://127.0.0.1:8002")
    monkeypatch.setattr(settings, "idprinter_bridge_token", SecretStr("server-only-secret-123456789012345"))
    monkeypatch.setattr(nfc, "IDPrinterBridge", FakeBridge)
    monkeypatch.setattr(sessions, "IDPrinterBridge", FakeBridge)
    monkeypatch.setattr(nfc_bridge, "recent_tap_matches", lambda *_args, **_kwargs: True)
    return TestClient(app)


def _body(kiosk_id=KIOSK_ID):
    return {"mode": 5, "service_mode": "workplace", "job_role": "cafe_crew",
            "scenario_slug": "ondo-cafe-crew", "nfc_uid": CARD_UID,
            "kiosk_session_id": kiosk_id, "consent": CONSENT}


def test_kiosk_card_without_local_mirror_card_keeps_uid_and_chosen_role(monkeypatch):
    client = _configured(monkeypatch)
    verified = client.post("/api/nfc/resolve", json={"uid": CARD_UID})
    assert verified.status_code == 200
    assert verified.json()["requires_role_selection"] is True
    assert verified.json()["kiosk_session_id"] == KIOSK_ID
    assert verified.json()["job_role"] == ""

    created = client.post("/api/sessions", json=_body())
    assert created.status_code == 200, created.text
    payload = created.json()
    assert payload["kiosk_link_status"] == "linked"
    assert FakeBridge.links == [(CardSnapshot(CARD_UID, KIOSK_ID), payload["id"], payload["access_token"])]
    with SessionLocal() as db:
        session = db.get(RoleplaySession, payload["id"])
        assert session.job_role == "cafe_crew"
        assert session.kiosk_session_id == KIOSK_ID
        assert session.kiosk_card_uid == CARD_UID


def test_reissued_card_snapshot_is_rejected_before_session_creation(monkeypatch):
    client = _configured(monkeypatch)
    FakeBridge.session_id = "MW2610030002"
    with SessionLocal() as db:
        before = db.query(RoleplaySession).count()
    response = client.post("/api/sessions", json=_body())
    assert response.status_code == 409
    with SessionLocal() as db:
        assert db.query(RoleplaySession).count() == before
    assert FakeBridge.links == []


def test_bridge_outage_retries_original_session_without_creating_another(monkeypatch):
    client = _configured(monkeypatch)
    FakeBridge.fail_link = True
    created = client.post("/api/sessions", json=_body())
    assert created.status_code == 200, created.text
    payload = created.json()
    assert payload["kiosk_link_status"] == "pending"
    FakeBridge.fail_link = False
    retried = client.post(f"/api/sessions/{payload['id']}/kiosk-link",
                          headers={"X-Session-Token": payload["access_token"]})
    assert retried.status_code == 200
    assert retried.json()["status"] == "linked"
    assert FakeBridge.links == [(CardSnapshot(CARD_UID, KIOSK_ID), payload["id"], payload["access_token"])]
