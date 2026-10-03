# MirrorTing 서버 연결 준비

이 폴더는 IDPrinter 키오스크와 **실제 MirrorTing 결과 API**를 연결하기 위한 동반 패치입니다. 현재 IDPrinter 작업용 worktree에만 존재하며 MirrorTing 원본에는 적용하지 않았습니다. 패치 기준은 2026-10-03에 확인한 `2026CarpeDM_EXPO-main/poc/backend`와 같은 저장소의 `mvp/src` 스냅샷입니다(확인 당시 기준 커밋 `98c17ad`, 로컬 수정 포함). 별도의 `2026CarpeDM_EXPO-smart-mirror` sparse checkout에는 백엔드가 없어 이 패치를 적용할 수 없습니다. 실제 배포 대상 저장소가 정해지면 그 코드에 대한 앵커 검사와 재검증이 필요합니다.

## 확인한 기존 계약

- 기존 MirrorTing `POST /api/sessions`는 `SessionCreateIn.nfc_uid`를 받아 **MirrorTing 로컬에 등록된** NFC 카드의 직무·시나리오를 조회합니다. IDPrinter에서 발급했지만 MirrorTing 로컬 DB에 없는 카드는 원래 404가 됩니다. 이 패치의 연동 모드는 IDPrinter의 현재 카드 스냅샷을 조회하여 로컬 카드 등록 요구를 대체하고, 사용자가 선택한 체험 역할을 그대로 사용합니다. 응답의 `id`는 정수 MirrorTing 세션 ID이며 `access_token`은 이후 MirrorTing 세션 조회 권한입니다 (`poc/backend/app/api/sessions.py`, `poc/backend/app/schemas/schemas.py`).
- 실제 리포트는 `GET /api/sessions/{id}/report`입니다. `X-Session-Token`이 필요하고, 분석 전에는 404입니다. `GET /api/sessions/{id}/progress`의 `status`가 `completed`가 될 때까지 대기해야 합니다 (`poc/backend/app/api/reports.py`, `poc/backend/app/api/deps.py`, `poc/backend/app/api/sessions.py`).
- `ReportOut`에는 `session_id`, `total_score`, `fit_scores`, `strengths`, `improvements`, `headline`, `day_ending`, `coaching`, `grade`, `mode` 등이 있습니다. 리포트 ID 필드는 없으므로 IDPrinter의 `reportId`는 **원천 `session_id`의 문자열 표현**입니다. `total_score`와 Fit 점수는 측정되지 않으면 `null`일 수 있습니다. `eye`는 관찰 지표이며 `expression`은 임시·참고 지표로 표시합니다.
- IDPrinter의 여섯 팀은 사원증 소속입니다. MirrorTing의 세 직무는 체험 역할이므로 이 연결에서 팀을 직무로 자동 변환하지 않습니다.

## 연결 순서

1. IDPrinter에서 NFC 카드를 사원증 방문 세션에 등록합니다.
2. 관람객이 MirrorTing 리더에 그 카드를 태그하면 `POST /api/nfc/resolve`가 IDPrinter의 인증된 `GET /api/integrations/mirrorting/cards/{uid}`에서 현재 `sessionId`와 UID를 확인합니다. 기존 역할 선택 화면은 이 스냅샷을 보존한 채 열립니다.
3. 관람객이 MirrorTing 체험 역할을 직접 선택합니다. 프런트엔드는 선택한 역할, UID, 원래 키오스크 `sessionId`를 `POST /api/sessions`에 보냅니다. MirrorTing 서버는 최근 물리적 NFC 태그와 IDPrinter의 **현재** 카드 스냅샷이 모두 일치하는지 다시 확인하고, 다른 관람객에게 카드가 재발급되었다면 세션 생성 전 409로 거부합니다.
4. MirrorTing이 역할극 세션을 만든 뒤 그 **같은** 스냅샷, 정수 `mirrorSessionId`, 세션 `accessToken`을 인증된 `POST /api/integrations/mirrorting/link`에 보냅니다. IDPrinter는 DB 트랜잭션 안에서 카드가 여전히 그 키오스크 세션에 활성으로 묶여 있는지 확인합니다. 같은 링크의 반복 요청은 성공하고, 서로 다른 링크는 409로 거부합니다.
5. IDPrinter 서버가 보관한 MirrorTing 토큰으로 리포트를 가져와 원천 필드만 정규화합니다. IDPrinter 브라우저는 브리지 토큰과 MirrorTing 토큰을 받지 않습니다. 실제 리포트가 없는 경우 데모 문구를 결과로 채우지 않습니다.

`session_bridge.patch`는 MirrorTing에 세션 스냅샷 컬럼과 `kiosk_link_status`를 추가합니다. 첫 턴 저장으로 역할극 세션이 커밋된 후 링크가 실패해도 새 세션을 만들지 않고 `pending` 또는 `conflict`를 응답합니다. `POST /api/sessions/{id}/kiosk-link`는 기존 `X-Session-Token`으로 **원래 스냅샷만** 다시 연결합니다. `GET /api/sessions/{id}`에서도 링크 상태를 조회할 수 있습니다. `pending`은 네트워크·설정 오류의 재시도 대상이고 `conflict`는 카드 재사용 또는 다른 링크의 운영 확인 대상입니다. 패치에 포함된 프런트엔드 변경은 역할 선택과 UID 전달을 연결하지만 `pending`·`conflict` 상태 안내 화면까지 만들지는 않습니다. 운영자는 링크 상태를 확인하고 재시도 또는 카드 재태그를 안내해야 합니다.

## 환경 변수

| 실행 서버 | 변수 | 값 |
| --- | --- | --- |
| IDPrinter | `KIOSK_BRIDGE_TOKEN` | 길이 32자 이상의 서버 간 공유 비밀 |
| IDPrinter | `KIOSK_MIRRORTING_URL` | MirrorTing 백엔드의 신뢰 가능한 기본 URL, 예: `http://127.0.0.1:8001` |
| MirrorTing | `MIRROR_TING_IDPRINTER_BASE_URL` | IDPrinter 백엔드의 신뢰 가능한 기본 URL, 예: `http://127.0.0.1:8002` |
| MirrorTing | `MIRROR_TING_IDPRINTER_BRIDGE_TOKEN` | IDPrinter의 `KIOSK_BRIDGE_TOKEN`과 같은 값 |

서버가 다른 장비라면 두 서버 간 주소는 해당 장비에서 접근 가능한 LAN 주소여야 합니다. IDPrinter의 Pi 브라우저는 계속 **자기 장비의 localhost**로 접속합니다. IDPrinter의 비브리지 방문자 `/api` 경로는 서버에서 실제 접속 IP가 loopback인 요청만 받으며, 외부 장비에는 브리지 경로만 인증 토큰으로 엽니다. 리버스 프록시를 추가한다면 비브리지 경로의 loopback 제한을 그대로 유지해야 합니다. 신뢰할 수 없는 네트워크로 보낼 때는 HTTPS를 사용합니다. URL과 비밀은 서버의 환경 파일에만 두고 Git, QR, 브라우저 저장소에 넣지 않습니다. 이 패치의 MirrorTing 서버 설정은 둘 다 비어 있으면 독립 실행을 유지하며, 한쪽만 설정되면 NFC 세션 생성을 503으로 거부합니다.

## 적용 및 검증

대상 MirrorTing 백엔드가 정해지면 먼저 실제 변경분과 DB를 보존하고, 아래처럼 패치가 맞는지 **읽기 전용으로** 확인합니다. 패치는 실제 `sessions.py`의 현재 앵커와 맞지 않으면 생성 단계에서 멈춥니다.

```sh
MIRRORTING_SOURCE=/absolute/path/to/MirrorTing python3 integrations/mirrorting/generate_session_bridge_patch.py
git -C /absolute/path/to/MirrorTing apply --check /absolute/path/to/IDPrinter/integrations/mirrorting/session_bridge.patch
```

적용 후 MirrorTing의 기존 `python -m app.seed.run` 또는 서버 시작 경로가 `_migrate_columns()`를 호출하여 모델의 새 컬럼을 기존 SQLite DB에 추가합니다 (`poc/backend/app/seed/run.py`). DB를 백업한 뒤 실행해야 합니다. 기존 코드로 만든 임시 DB에 패치를 적용하고 같은 DB에서 다시 시드를 실행하여 `kiosk_session_id`, `kiosk_card_uid`, `kiosk_link_status` 세 컬럼이 추가되고 기존 시나리오 4건이 보존되는 것을 확인했습니다. 계약 검증은 IDPrinter worktree의 `tests/test_reports.py`, `integrations/mirrorting/test_bridge_client.py`와 MirrorTing에 추가되는 `tests/test_idprinter_bridge.py`, `tests/test_idprinter_kiosk_flow.py`입니다. 확인한 스냅샷을 별도 임시 복사본에 적용했을 때 MirrorTing 백엔드 계약 테스트 7개와 `mvp` Vite 프로덕션 빌드가 통과했습니다. 실제 대상 배포와 실물 NFC·프린터 검증은 수행하지 않았습니다.

현장 통합에서는 최소한 다음을 확인합니다.

1. 카드 등록 → MirrorTing 리더 태그 → 별도 체험 역할 선택 → 세션 생성 → IDPrinter 리포트 API에서 같은 두 세션 ID가 나오는지. MirrorTing 로컬 카드 등록이 없어도 가능한지.
2. 분석 중에는 `REPORT_PENDING`, 완료 후에는 실제 `fitScores`와 `totalScore`가 나오는지. 미측정 값은 그대로 비워 두는지.
3. 카드 재발급을 UID 조회와 링크 요청 사이에 끼워 넣으면 409가 나고 새 관람객에 연결되지 않는지.
4. 링크 요청을 같은 내용으로 다시 보내면 성공하고, 다른 MirrorTing 세션 ID나 토큰이면 409가 나오는지.
5. MirrorTing 네트워크를 끊으면 생성 세션이 `pending`으로 남고, 복구 후 같은 세션의 재시도 경로로 `linked`가 되는지.
6. 잘못된 브리지 토큰과 잘못된 `X-Session-Token`으로 개인 리포트가 열리지 않는지.
7. 실제 프린터에서는 제출 성공과 물리적 출력 완료가 구분되는지. 화면 미리보기에는 종이가 나왔다고 표시하지 않는지.

원본 사진은 이 브리지로 보내거나 저장하지 않습니다. MirrorTing에 보존되는 UID 스냅샷은 서버 시작 시 기존 `media_retention_days`가 지난 세션에서 지우도록 패치했습니다. IDPrinter는 자체 보존 기간에 따라 방문 세션과 링크를 정리합니다.
