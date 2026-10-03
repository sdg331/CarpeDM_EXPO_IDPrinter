"""Generate a reviewable patch against the observed MirrorTing checkout.

This script only reads ``MIRRORTING_SOURCE`` and writes a patch beside itself.
It never edits the MirrorTing repository. The anchors deliberately fail if
the target source changed, so the patch cannot silently land in the wrong
place after a branch switch.
"""

from __future__ import annotations

import os
from difflib import unified_diff
from pathlib import Path


HERE = Path(__file__).resolve().parent
SOURCE = Path(os.environ["MIRRORTING_SOURCE"]).resolve()
changes: dict[str, tuple[str, str]] = {}


def edit(relative: str, replacements: list[tuple[str, str]]) -> None:
    old = (SOURCE / relative).read_text()
    new = old
    for before, after in replacements:
        count = new.count(before)
        if count != 1:
            raise RuntimeError(f"Expected one matching anchor in {relative}; found {count}")
        new = new.replace(before, after, 1)
    changes[relative] = old, new


edit("poc/backend/app/core/config.py", [
    (
        "    media_retention_days: int = 7\n",
        "    media_retention_days: int = 7\n"
        "    # Server-to-server kiosk bridge. Never include its secret in browser responses.\n"
        "    idprinter_base_url: str = \"\"\n"
        "    idprinter_bridge_token: SecretStr = SecretStr(\"\")\n",
    ),
])

edit("poc/backend/app/models/models.py", [
    (
        "    claim_token: Mapped[str] = mapped_column(String(64), default=\"\", index=True)\n",
        "    claim_token: Mapped[str] = mapped_column(String(64), default=\"\", index=True)\n"
        "    # Original kiosk card snapshot, persisted for safe retry after a failed link.\n"
        "    kiosk_session_id: Mapped[str | None] = mapped_column(String(16), nullable=True)\n"
        "    kiosk_card_uid: Mapped[str | None] = mapped_column(String(32), nullable=True)\n"
        "    kiosk_link_status: Mapped[str] = mapped_column(String(20), default=\"not_requested\")\n",
    ),
])

edit("poc/backend/app/schemas/schemas.py", [
    (
        "class NfcResolveOut(BaseModel):\n    uid: str\n    job_role: str\n    scenario_slug: str  # 발급 시 지정이 없으면 직무 기본 팩 슬러그\n    job_role_label: str = \"\"\n",
        "class NfcResolveOut(BaseModel):\n    uid: str\n    job_role: str\n    scenario_slug: str  # 발급 시 지정이 없으면 직무 기본 팩 슬러그\n    job_role_label: str = \"\"\n"
        "    # A kiosk-issued card keeps its identity while the visitor selects a role.\n"
        "    kiosk_session_id: str = \"\"\n"
        "    requires_role_selection: bool = False\n",
    ),
    (
        "    nfc_uid: str = Field(default=\"\", max_length=32)\n",
        "    nfc_uid: str = Field(default=\"\", max_length=32)\n"
        "    kiosk_session_id: str = Field(default=\"\", max_length=16)\n",
    ),
    (
        "    access_token: str = \"\"\n\n\nclass HistoryTurnOut",
        "    access_token: str = \"\"\n"
        "    kiosk_link_status: Literal[\"not_requested\", \"pending\", \"linked\", \"conflict\"] = \"not_requested\"\n"
        "\n\nclass HistoryTurnOut",
    ),
])

edit("poc/backend/app/api/nfc.py", [
    (
        "from app.api.deps import require_admin\n",
        "from app.api.deps import require_admin\n"
        "from app.core.config import settings\n"
        "from app.services.idprinter_bridge import BridgeError, IDPrinterBridge\n",
    ),
    (
        '    card = db.query(NfcCard).filter_by(uid=_normalize_uid(body.uid)).first()\n    if card is None or card.status != "active":\n        raise HTTPException(status_code=404, detail="등록되지 않았거나 폐기된 카드입니다")\n    card.last_seen_at = utcnow()\n',
        '    url = settings.idprinter_base_url.strip()\n'
        '    token = settings.idprinter_bridge_token.get_secret_value()\n'
        '    if url or token:\n'
        '        if not url or not token:\n'
        '            raise HTTPException(status_code=503, detail="사원증 연결 설정을 확인해주세요")\n'
        '        try:\n'
        '            with IDPrinterBridge(url, token) as bridge:\n'
        '                snapshot = bridge.resolve(body.uid)\n'
        '        except BridgeError as error:\n'
        '            status = 404 if error.code == "KIOSK_CARD_NOT_FOUND" else 503\n'
        '            raise HTTPException(status_code=status, detail="사원증을 확인하지 못했어요") from error\n'
        '        return NfcResolveOut(\n'
        '            uid=snapshot.uid, job_role="", scenario_slug="", job_role_label="",\n'
        '            kiosk_session_id=snapshot.kiosk_session_id, requires_role_selection=True,\n'
        '        )\n'
        '    card = db.query(NfcCard).filter_by(uid=_normalize_uid(body.uid)).first()\n'
        '    if card is None or card.status != "active":\n'
        '        raise HTTPException(status_code=404, detail="등록되지 않았거나 폐기된 카드입니다")\n'
        '    card.last_seen_at = utcnow()\n',
    ),
])

edit("poc/backend/app/main.py", [
    (
        "        if expired:\n            db.commit()\n            print(f\"보관 기간 만료 미저장 리포트 인용 {len(expired)}건 파기\")\n",
        "        # A card UID is needed only while the kiosk link can still be retried.\n"
        "        stale_cards = (\n"
        "            db.query(RoleplaySession)\n"
        "            .filter(RoleplaySession.started_at < cutoff)\n"
        "            .filter(RoleplaySession.kiosk_card_uid.isnot(None))\n"
        "            .all()\n"
        "        )\n"
        "        for session in stale_cards:\n"
        "            session.kiosk_card_uid = None\n"
        "            session.kiosk_session_id = None\n"
        "        if expired or stale_cards:\n"
        "            db.commit()\n"
        "        if expired:\n"
        "            print(f\"보관 기간 만료 미저장 리포트 인용 {len(expired)}건 파기\")\n",
    ),
])

helpers = '''

def _idprinter_bridge() -> IDPrinterBridge | None:
    url = settings.idprinter_base_url.strip()
    token = settings.idprinter_bridge_token.get_secret_value()
    if not url and not token:
        return None
    if not url or not token:
        raise HTTPException(status_code=503, detail={"code": "KIOSK_BRIDGE_UNCONFIGURED"})
    try:
        return IDPrinterBridge(url, token)
    except BridgeError as error:
        raise HTTPException(status_code=503, detail={"code": error.code}) from error


def _bridge_error_status(error: BridgeError) -> int:
    if error.code == "KIOSK_CARD_NOT_FOUND":
        return 404
    if error.code == "KIOSK_LINK_CONFLICT":
        return 409
    return 503


def _link_kiosk_session(db: Session, session: RoleplaySession) -> str:
    """Retry a committed session against its original card snapshot.

    IDPrinter performs the final atomic active-card check. A card reused for
    another visitor cannot change this stored snapshot to its new owner.
    """
    if not session.kiosk_session_id or not session.kiosk_card_uid:
        return "not_requested"
    try:
        bridge = _idprinter_bridge()
        if bridge is None:
            status = "pending"
        else:
            with bridge:
                bridge.link(
                    CardSnapshot(session.kiosk_card_uid, session.kiosk_session_id),
                    session.id, session.access_token,
                )
            status = "linked"
    except BridgeError as error:
        status = "conflict" if error.code in {"KIOSK_LINK_CONFLICT", "KIOSK_CARD_NOT_FOUND"} else "pending"
    except HTTPException:
        status = "pending"
    session.kiosk_link_status = status
    db.commit()
    return status
'''

sessions_source = (SOURCE / "poc/backend/app/api/sessions.py").read_text()
block_start = "    if body.nfc_uid:\n"
block_end = "    # 직무 검증"
if sessions_source.count(block_start) != 1 or sessions_source.count(block_end) != 1:
    raise RuntimeError("MirrorTing NFC session block changed")
old_nfc_block = block_start + sessions_source.split(block_start, 1)[1].split(block_end, 1)[0]
new_nfc_block = '''    if body.nfc_uid:
        from app.api.nfc import DEFAULT_PACK_BY_ROLE, _normalize_uid
        from app.models import NfcCard
        from app.services import nfc_bridge

        bridge = _idprinter_bridge()
        if bridge is None:
            # Original standalone MirrorTing card contract.
            card = db.query(NfcCard).filter_by(uid=_normalize_uid(body.nfc_uid)).first()
            if card is None or card.status != "active":
                raise HTTPException(status_code=404, detail="등록되지 않았거나 폐기된 카드입니다")
            card.last_seen_at = utcnow()
            job_role = card.job_role or job_role
            if not scenario_slug:
                scenario_slug = card.scenario_slug or DEFAULT_PACK_BY_ROLE.get(card.job_role, "")
            if nfc_bridge.recent_tap_matches(body.nfc_uid):
                card_org_id = card.institution_id
        else:
            # The kiosk owns identity. The visitor chooses the MirrorTing role;
            # a stale local NfcCard must not overwrite that choice.
            if not body.kiosk_session_id or not job_role:
                raise HTTPException(status_code=422, detail="사원증 확인과 체험 역할 선택이 필요합니다")
            if not nfc_bridge.recent_tap_matches(body.nfc_uid, max_age_sec=600):
                raise HTTPException(status_code=409, detail="사원증을 다시 태그해주세요")
            with bridge:
                try:
                    kiosk_snapshot = bridge.resolve(body.nfc_uid)
                except BridgeError as error:
                    raise HTTPException(
                        status_code=_bridge_error_status(error), detail={"code": error.code},
                    ) from error
            if kiosk_snapshot.kiosk_session_id != body.kiosk_session_id:
                raise HTTPException(status_code=409, detail="사원증이 새 방문객에게 등록됐어요. 다시 태그해주세요")
            if not scenario_slug:
                scenario_slug = DEFAULT_PACK_BY_ROLE.get(job_role, "")

'''

edit("poc/backend/app/api/sessions.py", [
    (
        "from app.services.session_fsm import InvalidTransition, transition\n",
        "from app.services.session_fsm import InvalidTransition, transition\n"
        "from app.services.idprinter_bridge import BridgeError, CardSnapshot, IDPrinterBridge\n",
    ),
    (
        "\n\n@router.post(\"\", response_model=SessionOut)\ndef create_session(",
        helpers + "\n\n@router.post(\"\", response_model=SessionOut)\ndef create_session(",
    ),
    (
        "    card = None\n    card_org_id = None\n",
        "    card = None\n    card_org_id = None\n    kiosk_snapshot = None\n",
    ),
    (old_nfc_block, new_nfc_block),
    (
        "        access_token=secrets.token_urlsafe(24),\n",
        "        access_token=secrets.token_urlsafe(24),\n"
        "        kiosk_session_id=kiosk_snapshot.kiosk_session_id if kiosk_snapshot else None,\n"
        "        kiosk_card_uid=kiosk_snapshot.uid if kiosk_snapshot else None,\n"
        "        kiosk_link_status=\"pending\" if kiosk_snapshot else \"not_requested\",\n",
    ),
    (
        "    turn = _create_turn(db, session, spec, order=1)\n\n    return SessionOut(",
        "    turn = _create_turn(db, session, spec, order=1)\n"
        "    # _create_turn has committed this session. Keep it retryable on bridge failure.\n"
        "    kiosk_link_status = _link_kiosk_session(db, session) if kiosk_snapshot else \"not_requested\"\n\n"
        "    return SessionOut(",
    ),
    (
        "        access_token=session.access_token,\n    )\n\n\n@router.get(\"/mine\")",
        "        access_token=session.access_token,\n"
        "        kiosk_link_status=kiosk_link_status,\n"
        "    )\n\n\n@router.post(\"/{session_id}/kiosk-link\")\n"
        "def retry_kiosk_link(\n"
        "    session: RoleplaySession = Depends(require_session),\n"
        "    db: Session = Depends(get_db),\n"
        "):\n"
        "    \"\"\"Retry only the original snapshot with X-Session-Token.\"\"\"\n"
        "    if not session.kiosk_session_id or not session.kiosk_card_uid:\n"
        "        raise HTTPException(status_code=404, detail={\"code\": \"KIOSK_LINK_NOT_REQUESTED\"})\n"
        "    return {\"status\": _link_kiosk_session(db, session)}\n\n\n@router.get(\"/mine\")",
    ),
    (
        "        elapsed_sec=elapsed,\n    )\n\n\n@router.post(\"/{session_id}/turns/{turn_id}/observation\")",
        "        elapsed_sec=elapsed,\n"
        "        kiosk_link_status=session.kiosk_link_status or \"not_requested\",\n"
        "    )\n\n\n@router.post(\"/{session_id}/turns/{turn_id}/observation\")",
    ),
])

edit("mvp/src/lib/pocApi.js", [
    (
        "export function createSession({ serviceMode = \"workplace\", difficulty, mode, scenarioSlug, selectedEpisodeId, consent, jobRole, nfcUid }) {",
        "export function createSession({ serviceMode = \"workplace\", difficulty, mode, scenarioSlug, selectedEpisodeId, consent, jobRole, nfcUid, kioskSessionId }) {",
    ),
    (
        "      ...(nfcUid ? { nfc_uid: nfcUid } : {}),\n",
        "      ...(nfcUid ? { nfc_uid: nfcUid } : {}),\n"
        "      ...(kioskSessionId ? { kiosk_session_id: kioskSessionId } : {}),\n",
    ),
])

edit("mvp/src/lib/useServiceEntryRoute.js", [
    (
        "      setNfcCard({ uid: card.uid, jobRole: card.job_role, scenarioSlug: card.scenario_slug, jobRoleLabel: card.job_role_label });\n"
        "      setNfcFallback(false);\n"
        "      setApiError(\"\");\n"
        "      navigate(\"preview\");\n"
        "    } catch {\n"
        "      setNfcFallback(true);\n",
        "      if (card.requires_role_selection && card.kiosk_session_id && card.uid) {\n"
        "        // This UID is already bound to a current IDPrinter visitor.\n"
        "        // Keep the verified kiosk snapshot while this visitor picks a role.\n"
        "        setNfcCard({ uid: card.uid, kioskSessionId: card.kiosk_session_id });\n"
        "        setNfcFallback(true);\n"
        "        setApiError(\"\");\n"
        "      } else {\n"
        "        setNfcCard({ uid: card.uid, jobRole: card.job_role, scenarioSlug: card.scenario_slug, jobRoleLabel: card.job_role_label });\n"
        "        setNfcFallback(false);\n"
        "        setApiError(\"\");\n"
        "        navigate(\"preview\");\n"
        "      }\n"
        "    } catch {\n"
        "      setNfcCard(null);\n"
        "      setNfcFallback(true);\n",
    ),
    (
        "    setNfcCard({ uid: \"\", jobRole: role.id, scenarioSlug: role.scenarioSlug, jobRoleLabel: role.label });\n",
        "    const verified = nfcCard?.kioskSessionId\n"
        "      ? { uid: nfcCard.uid, kioskSessionId: nfcCard.kioskSessionId }\n"
        "      : { uid: \"\", kioskSessionId: \"\" };\n"
        "    setNfcCard({ ...verified, jobRole: role.id, scenarioSlug: role.scenarioSlug, jobRoleLabel: role.label });\n",
    ),
])

edit("mvp/src/App.jsx", [
    (
        "        nfcUid: nfcCard?.uid || \"\",\n",
        "        nfcUid: nfcCard?.uid || \"\",\n"
        "        kioskSessionId: nfcCard?.kioskSessionId || \"\",\n",
    ),
])

edit("mvp/src/pages/ServiceEntryShell.jsx", [
    (
        '    {active === "home" && nfcFallback && <NfcStartFallback onPick={startFromJobRole} onClose={() => setNfcFallback(false)} />}\n',
        '    {active === "home" && nfcFallback && <NfcStartFallback cardConfirmed={Boolean(entry.state.nfcCard?.kioskSessionId)} onPick={startFromJobRole} onClose={() => setNfcFallback(false)} />}\n',
    ),
])

edit("mvp/src/components/nfc/NfcStartFallback.jsx", [
    (
        "export function NfcStartFallback({ onPick, onClose }) {",
        "export function NfcStartFallback({ cardConfirmed = false, onPick, onClose }) {",
    ),
    (
        '<div className="nfc-fallback-overlay" role="dialog" aria-label="카드 미인식 — 직무 선택으로 시작">',
        '<div className="nfc-fallback-overlay" role="dialog" aria-label={cardConfirmed ? "사원증 확인 완료 — 체험 역할 선택" : "카드 미인식 — 직무 선택으로 시작"}>',
    ),
    (
        '        <h2>카드가 인식되지 않아요</h2>\n'
        '        <p>직무를 선택해 시작하세요 — 발급 카드 없이도 같은 연습을 바로 진행할 수 있어요.</p>\n',
        '        <h2>{cardConfirmed ? "사원증을 확인했어요" : "카드가 인식되지 않아요"}</h2>\n'
        '        <p>{cardConfirmed ? "이번에 체험할 역할을 선택하세요. 사원증의 팀 소속과는 별개의 선택이에요." : "직무를 선택해 시작하세요 — 발급 카드 없이도 같은 연습을 바로 진행할 수 있어요."}</p>\n',
    ),
])

client = (HERE / "bridge_client.py").read_text().replace(
    "Companion client to copy into MirrorTing's ``poc/backend/app/services``.",
    "Server-side companion client for the IDPrinter kiosk.",
)
changes["poc/backend/app/services/idprinter_bridge.py"] = "", client

tests = (HERE / "test_bridge_client.py").read_text().replace(
    "from integrations.mirrorting.bridge_client import",
    "from app.services.idprinter_bridge import",
)
changes["poc/backend/tests/test_idprinter_bridge.py"] = "", tests

flow_tests = (HERE / "test_kiosk_flow.py").read_text()
changes["poc/backend/tests/test_idprinter_kiosk_flow.py"] = "", flow_tests

diff = []
for relative, (old, new) in changes.items():
    diff.extend(unified_diff(
        old.splitlines(keepends=True), new.splitlines(keepends=True),
        fromfile=f"a/{relative}" if old else "/dev/null", tofile=f"b/{relative}",
    ))
out = HERE / "session_bridge.patch"
out.write_text("".join(diff))
print(f"{out}: {len(changes)} files, {out.stat().st_size} bytes")
