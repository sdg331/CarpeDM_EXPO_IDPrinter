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

    assert first["status"] == "preview"
    assert second["status"] == "preview"
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


def test_concurrent_nfc_retries_claim_one_reader_call(monkeypatch, tmp_path):
    from concurrent.futures import ThreadPoolExecutor
    import threading
    from backend.nfc import NfcError

    store = configure(monkeypatch, tmp_path)
    monkeypatch.setattr(backend_app, 'read_card_uid', lambda _: (_ for _ in ()).throw(NfcError('NFC_TIMEOUT', True)))
    first = backend_app.register_nfc(register_request())
    assert first.status_code == 408
    entered, release = threading.Event(), threading.Event()
    calls = []

    def read(_):
        calls.append(True)
        entered.set()
        assert release.wait(5)
        return '04AABBCC'

    monkeypatch.setattr(backend_app, 'read_card_uid', read)
    with ThreadPoolExecutor(max_workers=2) as pool:
        pending = pool.submit(backend_app.register_nfc, register_request())
        assert entered.wait(5)
        repeated = pool.submit(backend_app.register_nfc, register_request()).result(5)
        assert repeated.status_code == 409
        release.set()
        completed = pending.result(5)
    assert len(calls) == 1
    assert store.resolve_card('04AABBCC')['session_id'] == completed['sessionId']


def test_different_print_operation_ids_share_session_guard(monkeypatch, tmp_path):
    from concurrent.futures import ThreadPoolExecutor
    import threading

    configure(monkeypatch, tmp_path)
    registered = backend_app.register_nfc(register_request())
    monkeypatch.setattr(backend_app, 'render_badge', lambda *a, **kw: Image.new('1', (10, 10)))
    entered, release = threading.Event(), threading.Event()
    calls = []

    def print_once(_):
        calls.append(True)
        entered.set()
        assert release.wait(5)
        return {'backend': 'escpos'}

    monkeypatch.setattr(backend_app, 'print_badge', print_once)
    request = lambda operation: backend_app.BadgePrintRequest(operationId=operation, sessionId=registered['sessionId'])
    with ThreadPoolExecutor(max_workers=2) as pool:
        pending = pool.submit(backend_app.print_session_badge, request('first-print-op'))
        assert entered.wait(5)
        repeated = pool.submit(backend_app.print_session_badge, request('second-print-op')).result(5)
        assert repeated.status_code == 409
        release.set()
        completed = pending.result(5)
    cached = backend_app.print_session_badge(request('third-print-op'))
    assert completed['status'] == 'submitted'
    assert completed['completionConfirmed'] is False
    assert cached['printJobId'] == 'first-print-op'
    assert len(calls) == 1


def test_registration_id_cannot_be_reused_for_another_visitor(monkeypatch, tmp_path):
    configure(monkeypatch, tmp_path)
    backend_app.register_nfc(register_request())
    changed = register_request()
    changed.name = '다른사람'
    response = backend_app.register_nfc(changed)
    assert response.status_code == 409
    assert b'OPERATION_CONFLICT' in response.body


def test_profile_expiry_after_registration_recovers_same_session(monkeypatch, tmp_path):
    from io import BytesIO
    from backend.profile import ProfileStore

    configure(monkeypatch, tmp_path)
    now = [1.0]
    profiles = ProfileStore(ttl_seconds=30, clock=lambda: now[0])
    monkeypatch.setitem(backend_app.STATE, 'profiles', profiles)
    image = BytesIO()
    Image.new('RGB', (720, 960), 'gray').save(image, format='PNG')
    old_profile = profiles.put(image.getvalue())
    request = backend_app.NfcRegisterRequest(operationId='b-nfc-operation', name='사진사원', teamId='design', aiMode='B',
        result=backend_app.MatchResultPayload(kind='B', profileId=old_profile))
    registered = backend_app.register_nfc(request)
    print_req = backend_app.BadgePrintRequest(operationId='b-print-operation', sessionId=registered['sessionId'])
    now[0] += 31
    expired = backend_app.print_session_badge(print_req)
    assert expired.status_code == 410
    assert b'PROFILE_EXPIRED' in expired.body
    new_profile = profiles.put(image.getvalue())
    recovered = backend_app.replace_session_profile(registered['sessionId'], backend_app.SessionProfileRequest(profileId=new_profile))
    assert recovered['sessionId'] == registered['sessionId']
    monkeypatch.setattr(backend_app, 'print_badge', lambda _: {'backend': 'screen'})
    printed = backend_app.print_session_badge(print_req)
    assert printed['status'] == 'preview'
    assert profiles.get(new_profile) is None
    assert backend_app.print_session_badge(print_req)['printJobId'] == print_req.operationId


def test_expired_profile_never_registers_card(monkeypatch, tmp_path):
    from backend.profile import ProfileStore

    store = configure(monkeypatch, tmp_path)
    monkeypatch.setitem(backend_app.STATE, 'profiles', ProfileStore())
    request = backend_app.NfcRegisterRequest(operationId='expired-profile-nfc', name='방문객', teamId='ai', aiMode='B',
        result=backend_app.MatchResultPayload(kind='B', profileId='p_missing'))
    response = backend_app.register_nfc(request)
    assert response.status_code == 410
    assert store.get_operation(request.operationId) is None


def test_profile_cannot_be_attached_to_second_session(monkeypatch, tmp_path):
    from backend.profile import ProfileStore

    configure(monkeypatch, tmp_path)
    profiles = ProfileStore()
    monkeypatch.setitem(backend_app.STATE, 'profiles', profiles)
    profile = profiles.put(b'fixture')
    request = lambda op: backend_app.NfcRegisterRequest(operationId=op, name='사진사원', teamId='ai', aiMode='B',
        result=backend_app.MatchResultPayload(kind='B', profileId=profile))
    first = backend_app.register_nfc(request('first-profile-nfc'))
    second = backend_app.register_nfc(request('second-profile-nfc'))
    assert first['ok']
    assert second.status_code == 409
    assert b'PROFILE_ALREADY_USED' in second.body


def test_known_pre_device_failure_can_retry_same_print(monkeypatch, tmp_path):
    configure(monkeypatch, tmp_path)
    registered = backend_app.register_nfc(register_request())
    monkeypatch.setattr(backend_app, 'render_badge', lambda *a, **kw: Image.new('1', (10, 10)))
    monkeypatch.setattr(backend_app, 'print_badge', lambda _: (_ for _ in ()).throw(PrintError('not configured', retryable=True)))
    req = backend_app.BadgePrintRequest(operationId='safe-print-retry', sessionId=registered['sessionId'])
    failed = backend_app.print_session_badge(req)
    assert failed.status_code == 503
    assert b'PRINT_UNAVAILABLE' in failed.body
    monkeypatch.setattr(backend_app, 'print_badge', lambda _: {'backend': 'screen'})
    assert backend_app.print_session_badge(req)['status'] == 'preview'


def test_http_rejects_cross_origin_side_effects_and_disables_legacy():
    from fastapi.testclient import TestClient

    client = TestClient(backend_app.app, client=('127.0.0.1', 50000))
    response = client.post('/api/nfc/register', headers={'Origin': 'https://unrelated.example'}, json={})
    assert response.status_code == 403
    legacy = client.post('/api/issue', json={'name': '테스트', 'dept': 'AI팀', 'char_id': 'char_01', 'emp_no': 'MW2601010001'})
    assert legacy.status_code == 410
    assert legacy.headers['cache-control'] == 'no-store, max-age=0'


def test_bridge_http_auth_link_and_report_print_use_server_identity(monkeypatch, tmp_path):
    from fastapi.testclient import TestClient

    store = configure(monkeypatch, tmp_path)
    monkeypatch.setenv('KIOSK_BRIDGE_TOKEN', 'bridge-secret-' * 4)
    monkeypatch.setenv('KIOSK_MIRRORTING_URL', 'http://127.0.0.1:8001')
    registered = backend_app.register_nfc(register_request())
    session_id = registered['sessionId']
    client = TestClient(backend_app.app, client=('127.0.0.1', 50000))
    headers = {'X-Bridge-Token': 'bridge-secret-' * 4}
    assert client.get('/api/integrations/mirrorting/cards/04AABBCC').status_code == 403
    resolved = client.get('/api/integrations/mirrorting/cards/04aabbcc', headers=headers)
    assert resolved.json() == {'ok': True, 'sessionId': session_id, 'cardUid': '04AABBCC'}
    body = {'sessionId': session_id, 'cardUid': '04AABBCC', 'mirrorSessionId': 42, 'accessToken': 'server-only-capability'}
    linked = client.post('/api/integrations/mirrorting/link', json=body, headers=headers)
    assert linked.json() == {'ok': True, 'status': 'linked', 'sessionId': session_id, 'mirrorSessionId': 42}
    assert 'server-only-capability' not in linked.text
    fetched = []

    def source(kiosk_session_id, mirror_id, token, *, base_url):
        fetched.append((kiosk_session_id, mirror_id, token, base_url))
        return {'status': 'available', 'sessionId': kiosk_session_id, 'reportId': str(mirror_id), 'source': 'mirrorting'}

    monkeypatch.setattr(backend_app, 'fetch_mirrorting_report', source)
    rendered = []
    def render(report, *, name, team):
        rendered.append((report, name, team))
        return Image.new('1', (576, 500))
    monkeypatch.setattr(backend_app, 'render_report', render)
    calls = []
    monkeypatch.setattr(backend_app, 'print_badge', lambda _: calls.append(True) or {'backend': 'screen'})
    report = client.get(f'/api/reports/{session_id}')
    assert report.json()['source'] == 'mirrorting'
    wrong = client.post('/api/reports/print', json={'operationId': 'report-print-id', 'sessionId': session_id, 'reportId': '43'})
    assert wrong.status_code == 404
    assert calls == []
    correct = {'operationId': 'report-print-id', 'sessionId': session_id, 'reportId': '42'}
    printed = client.post('/api/reports/print', json=correct)
    assert printed.json()['status'] == 'preview'
    repeated = client.post('/api/reports/print', json={**correct, 'operationId': 'another-report-print-id'})
    assert repeated.json()['printJobId'] == 'report-print-id'
    assert len(calls) == 1
    assert rendered[0][1:] == ('김지연', 'AI팀')
    assert all(row == (session_id, 42, 'server-only-capability', 'http://127.0.0.1:8001') for row in fetched)
    assert 'server-only-capability' not in report.text
    assert store.get_operation('report-print-id')['status'] == 'success'


def test_card_reassignment_prevents_previous_visitor_print_and_report(monkeypatch, tmp_path):
    configure(monkeypatch, tmp_path)
    old = backend_app.register_nfc(register_request())['sessionId']
    backend_app.register_nfc(register_request('new-visitor-nfc-operation'))
    badge = backend_app.print_session_badge(backend_app.BadgePrintRequest(operationId='old-visitor-badge', sessionId=old))
    assert badge.status_code == 409
    assert b'SESSION_REPLACED' in badge.body
    report = backend_app.get_report(old)
    assert b'SESSION_REPLACED' in report.body


def test_bridge_does_not_activate_with_short_configuration_token(monkeypatch, tmp_path):
    from fastapi.testclient import TestClient

    configure(monkeypatch, tmp_path)
    monkeypatch.setenv('KIOSK_BRIDGE_TOKEN', 'short')
    response = TestClient(backend_app.app, client=('127.0.0.1', 50000)).get('/api/integrations/mirrorting/cards/04AABBCC', headers={'X-Bridge-Token': 'short'})
    assert response.status_code == 503
    assert response.json()['error']['code'] == 'INTEGRATION_PENDING'


def test_report_render_failures_are_safe_retryable_errors_before_print(monkeypatch, tmp_path):
    import json
    from backend.reports import ReportError

    store = configure(monkeypatch, tmp_path)
    monkeypatch.setenv('KIOSK_MIRRORTING_URL', 'http://127.0.0.1:8001')
    session_id = backend_app.register_nfc(register_request())['sessionId']
    store.link_mirrorting(session_id=session_id, card_uid='04AABBCC', mirror_session_id=42, access_token='private-token')
    monkeypatch.setattr(backend_app, 'fetch_mirrorting_report', lambda *a, **kw: {
        'status': 'available', 'sessionId': session_id, 'reportId': '42', 'source': 'mirrorting',
    })
    print_calls = []
    monkeypatch.setattr(backend_app, 'print_badge', lambda _: print_calls.append(True) or {'backend': 'screen'})
    request = backend_app.ReportPrintRequest(operationId='report-render-retry', sessionId=session_id, reportId='42')
    for failure in (ReportError('REPORT_RENDER_FAILED'), OSError('private filesystem detail'), ValueError('private renderer detail')):
        def fail_render(*args, **kwargs):
            raise failure
        monkeypatch.setattr(backend_app, 'render_report', fail_render)
        response = backend_app.print_session_report(request)
        assert response.status_code == 500
        assert json.loads(response.body) == {'ok': False, 'error': {'code': 'REPORT_RENDER_FAILED', 'retryable': True}}
        assert store.get_operation(request.operationId) is None
        assert print_calls == []
    monkeypatch.setattr(backend_app, 'render_report', lambda *a, **kw: Image.new('1', (576, 500)))
    assert backend_app.print_session_report(request)['status'] == 'preview'
    assert len(print_calls) == 1
    assert store.active_card(session_id)


def test_report_rechecks_current_card_after_upstream_network_wait(monkeypatch, tmp_path):
    import json

    for action in ('read', 'print'):
        store = configure(monkeypatch, tmp_path / action)
        monkeypatch.setenv('KIOSK_MIRRORTING_URL', 'http://127.0.0.1:8001')
        old = backend_app.register_nfc(register_request())['sessionId']
        store.link_mirrorting(session_id=old, card_uid='04AABBCC', mirror_session_id=42, access_token='private-token')
        new = store.create_session(name='다음방문객', team_id='design', ai_mode='A', char_id='char_01')['session_id']
        def fetch_then_rebind(*args, **kwargs):
            store.bind_card(session_id=new, card_uid='04AABBCC', operation_id='reassigned-during-fetch')
            return {'status': 'available', 'sessionId': old, 'reportId': '42', 'source': 'mirrorting'}
        monkeypatch.setattr(backend_app, 'fetch_mirrorting_report', fetch_then_rebind)
        calls = []
        monkeypatch.setattr(backend_app, 'print_badge', lambda _: calls.append(True) or {'backend': 'screen'})
        request = backend_app.ReportPrintRequest(operationId='report-race-print', sessionId=old, reportId='42')
        response = backend_app.get_report(old) if action == 'read' else backend_app.print_session_report(request)
        assert response.status_code == 409
        assert json.loads(response.body)['error']['code'] == 'SESSION_REPLACED'
        assert calls == []
        assert store.get_operation(request.operationId) is None


def test_badge_and_report_recheck_binding_after_render_before_output(monkeypatch, tmp_path):
    import json

    for kind in ('badge', 'report'):
        store = configure(monkeypatch, tmp_path / kind)
        monkeypatch.setenv('KIOSK_MIRRORTING_URL', 'http://127.0.0.1:8001')
        old = backend_app.register_nfc(register_request())['sessionId']
        new = store.create_session(name='다음방문객', team_id='design', ai_mode='A', char_id='char_01')['session_id']
        store.link_mirrorting(session_id=old, card_uid='04AABBCC', mirror_session_id=42, access_token='private-token')
        monkeypatch.setattr(backend_app, 'fetch_mirrorting_report', lambda *a, **kw: {
            'status': 'available', 'sessionId': old, 'reportId': '42', 'source': 'mirrorting',
        })
        def render_then_rebind(*args, **kwargs):
            store.bind_card(session_id=new, card_uid='04AABBCC', operation_id='reassigned-during-render')
            return Image.new('1', (576, 500))
        monkeypatch.setattr(backend_app, 'render_badge' if kind == 'badge' else 'render_report', render_then_rebind)
        calls = []
        monkeypatch.setattr(backend_app, 'print_badge', lambda _: calls.append(True) or {'backend': 'screen'})
        request = (backend_app.BadgePrintRequest(operationId='badge-race-print', sessionId=old) if kind == 'badge'
                   else backend_app.ReportPrintRequest(operationId='report-race-print', sessionId=old, reportId='42'))
        response = backend_app.print_session_badge(request) if kind == 'badge' else backend_app.print_session_report(request)
        assert response.status_code == 409
        assert json.loads(response.body)['error']['code'] == 'SESSION_REPLACED'
        assert calls == []
        assert store.get_operation(request.operationId)['status'] == 'error'


def test_card_rebinding_waits_for_device_submission(monkeypatch, tmp_path):
    from concurrent.futures import ThreadPoolExecutor
    import threading

    store = configure(monkeypatch, tmp_path)
    old = backend_app.register_nfc(register_request())['sessionId']
    new = store.create_session(name='다음방문객', team_id='design', ai_mode='A', char_id='char_01')['session_id']
    monkeypatch.setattr(backend_app, 'render_badge', lambda *a, **kw: Image.new('1', (10, 10)))
    entered, release, binding_started, binding_committed = (threading.Event() for _ in range(4))
    def slow_print(_):
        entered.set()
        assert release.wait(5)
        assert store.active_card(old)
        return {'backend': 'escpos'}
    def rebind():
        binding_started.set()
        store.bind_card(session_id=new, card_uid='04AABBCC', operation_id='rebind-after-submit')
        binding_committed.set()
    monkeypatch.setattr(backend_app, 'print_badge', slow_print)
    request = backend_app.BadgePrintRequest(operationId='serialized-device-print', sessionId=old)
    with ThreadPoolExecutor(max_workers=2) as pool:
        printing = pool.submit(backend_app.print_session_badge, request)
        assert entered.wait(5)
        rebinding = pool.submit(rebind)
        assert binding_started.wait(5)
        assert not binding_committed.wait(0.05)
        release.set()
        assert printing.result(5)['status'] == 'submitted'
        rebinding.result(5)
    assert binding_committed.is_set()
    assert store.resolve_card('04AABBCC')['session_id'] == new


def test_lan_clients_can_only_use_authenticated_mirrorting_bridge(monkeypatch, tmp_path):
    from fastapi.testclient import TestClient

    configure(monkeypatch, tmp_path)
    monkeypatch.setenv('KIOSK_BRIDGE_TOKEN', 'bridge-secret-' * 4)
    session_id = backend_app.register_nfc(register_request())['sessionId']
    remote = TestClient(backend_app.app, client=('192.168.40.22', 50000))
    for path in (f'/api/reports/{session_id}', '/api/operations/nfc-operation-0001', '/api/health', '/api/profile/guess/image'):
        response = remote.get(path, headers={'X-Forwarded-For': '127.0.0.1'})
        assert response.status_code == 403
        assert response.json()['error']['code'] == 'LOCAL_ACCESS_REQUIRED'
    for path in ('/api/nfc/register', '/api/nfc/resolve', '/api/badge/print', '/api/reports/print'):
        assert remote.post(path, json={}).json()['error']['code'] == 'LOCAL_ACCESS_REQUIRED'
    assert remote.get('/api/integrations/mirrorting/cards/04AABBCC').status_code == 403
    allowed = remote.get('/api/integrations/mirrorting/cards/04AABBCC', headers={'X-Bridge-Token': 'bridge-secret-' * 4})
    assert allowed.status_code == 200
    assert allowed.json()['sessionId'] == session_id


def test_verbose_source_report_prints_once_with_real_renderer(monkeypatch, tmp_path):
    from PIL import ImageFont
    import backend.reports as reports

    store = configure(monkeypatch, tmp_path)
    monkeypatch.setenv('KIOSK_MIRRORTING_URL', 'http://127.0.0.1:8001')
    session_id = backend_app.register_nfc(register_request())['sessionId']
    store.link_mirrorting(session_id=session_id, card_uid='04AABBCC', mirror_session_id=42, access_token='private-token')
    source = reports.normalize_report(session_id, 42, {
        'session_id': 42, 'mode': 5, 'fit_scores': {},
        'strengths': ['verbose strength ' * 40] * 8,
        'improvements': ['verbose improvement ' * 40] * 8,
        'headline': {}, 'day_ending': {'label': '마지막 결말', 'text': '대화를 마쳤어요.'},
    })
    monkeypatch.setattr(backend_app, 'fetch_mirrorting_report', lambda *a, **kw: source)
    monkeypatch.setattr(reports, '_font', lambda size: ImageFont.load_default(size=size))
    images = []
    monkeypatch.setattr(backend_app, 'print_badge', lambda image: images.append(image) or {'backend': 'screen'})
    request = backend_app.ReportPrintRequest(operationId='verbose-report-print', sessionId=session_id, reportId='42')
    first = backend_app.print_session_report(request)
    repeated = backend_app.print_session_report(request)
    assert first['status'] == repeated['status'] == 'preview'
    assert first['printJobId'] == repeated['printJobId'] == request.operationId
    assert len(images) == 1
    assert images[0].mode == '1' and images[0].width == 576 and images[0].height > 4300
    assert store.get_operation(request.operationId)['status'] == 'success'
