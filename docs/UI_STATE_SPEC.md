# UI State Specification

## Principle

복잡한 하드웨어 흐름을 `isLoading`, `hasError` 같은 여러 boolean 조합으로 만들지 않는다. 도메인별 explicit state를 사용한다.

## Session

2026-10-12 체험 리포트: `souvenirFrame`/`souvenirPhoto`를 사진 확인부터 출력 성공까지 유지해 명시적 안전 재시도에서도 같은 사진을 보낸다. 사진 없이 진행·완료·초기화·페이지 종료에 해제한다. `report.careerTip`은 서버가 선택하며 UI에서 다시 뽑거나 분석값으로 표시하지 않는다. 출력 결과 불명은 기존 `reportPrint` ID로 상태를 조회한다.

```text
idle
checkin_in_progress
checkout_in_progress
completed
expired
fatal_error
```

Session carries only current visitor data.

## Camera

```text
uninitialized
initializing
ready
no_person
multiple_people
bad_position
capturing
captured
error
```

Transition concept:

```text
uninitialized → initializing → ready
ready ↔ no_person
ready ↔ multiple_people
ready ↔ bad_position
ready → capturing → captured
any active → error
```

CURRENT backend `/api/detect` supports face count/confidence only. `bad_position` requires additional quality metadata or frontend-approved heuristic; do not pretend backend supports it until implemented.

CURRENT lifecycle · 2026-10-05:
- Device and web preview start permission/stream acquisition only on a camera screen, through the same `Camera.start()` path.
- Permission and video initialization share a 15-second limit; late streams are stopped after navigation or timeout.
- Track `ended` or stream `inactive` stops the stream, aborts detection, and shows a retryable camera error.
- Capture requires an active live video track. Encoded frames and detection responses from an old camera generation are rejected.
- Detection failures release camera resources; retry opens a new stream without losing the visitor name/team.

## AI

```text
idle
submitting
queued
processing
success
timeout
error
```

Rules:
- one logical AI job per capture/attempt
- random fallback forbidden
- no fake percentage
- stale result must not update a new session

2026-10-06: 분석 화면은 최소 6초 표시한 후 성공 결과로 이동한다. 실제 요청이 6초보다 길면 추가 대기 없이 완료 시 이동한다. 최소 시간은 화면 연출 기준이며 모델 처리시간이나 진행률이 아니다. 실패는 지연 없이 안내하고 초기화/페이지 종료 시 남은 대기를 취소한다.

2026-10-12: 촬영 Blob의 임시 URL을 분석 화면에서만 사용한다. 카메라 미리보기와 같은 좌우 방향으로 표시하며 실제 분석에는 원본 Blob을 전달한다. 결과 이동·오류·초기화·페이지 종료 시 URL을 해제하고 촬영 참조를 지운다. 스캔 라인·고정 포인트 연결망·8명 비교 하이라이트는 반복 연출이며 감지 좌표·순위·진행률을 나타내지 않는다. 화면에 연출임을 표시하고 reduced-motion에서는 움직이지 않는다. 샘플 모드는 명시된 예시 사진을 사용한다. 최소 대기 시간 및 API 계약은 유지한다.

## NFC Registration

```text
idle
waiting
detected
writing
verifying
success
timeout
error
reader_offline
```

Rules:
- navigation locked during writing/verifying
- session preserved on retryable failure
- success only from backend-confirmed result

## NFC Checkout

```text
idle
waiting
detected
resolving
success
unknown_card
timeout
error
reader_offline
```

## Printer

```text
idle
submitting
queued
printing
success
offline
paper_out
error
```

Only expose `paper_out` if printer/backend can reliably distinguish it.

## MirrorTing Result

```text
idle
loading
success
not_found
timeout
error
```

`not_found` is not a fabricated report; show clear retry/fallback choice.

## Backend Health

```text
unknown
checking
healthy
degraded
unavailable
```

Health state may help operator diagnostics, but visitor flow should not expose technical service names unnecessarily.

CURRENT: app entry, Home reset, and opening the connection dialog request fresh health data with a 4-second limit and `cache: no-store`. Concurrent reads share the current request. The actual frontend uses unknown/checking/healthy/unavailable; degraded remains a conceptual state without a current classifier. An unavailable response clears old hardware details. Health responses update the header and connection dialog without replacing the current name field, camera, or photo; dialog focus and its return target are retained. Home reset still clears all previous visitor data.

## Action Lock

Lock duplicate action while these are in flight:
- camera capture
- AI submission
- NFC write/verify
- badge print
- checkout resolve
- report print

The connection and sample-settings buttons are also disabled while an action is busy.

## Operation Identity

Each side-effect operation should conceptually have an operation/job ID so a late response or retry cannot cause duplicate effects.

## Inactivity

```text
active
warning
expired
```

Default target: 60s policy with warning before reset; tune during onsite testing.

Implemented: warning at 45s, reset at 60s. The warning requires an explicit Continue or Home action. Background activity and Tab do not dismiss it. Continue restores the current screen/input and restarts the inactivity timer. Work in progress and unknown hardware outcomes are excluded; completion returns home after 15s.

## Ownership

Frontend owns:
- navigation state
- presentation state
- temporary text input
- interaction locks

Backend owns:
- AI truth
- NFC success/failure
- printer success/failure
- persistent/local session truth
- MirrorTing result truth

Camera preview exception:
- browser MediaDevices may own preview stream in current architecture
- backend remains source of AI detection/matching result

## 사진 전용 상태 · 2026-10-12

`flow:souvenir`, `photoGrant:{photoPass,printJobId,qrPreviewUrl}`, `souvenirFrame:Blob`, `souvenirPhoto:blob URL`을 사용한다. NFC 승인 후 촬영하며 고정 출력 ID를 재사용한다. 완료 시 Blob/URL을 해제하고 HOME/취소/페이지 종료 시 승인·화면 출력 미리보기 삭제를 요청한다. 늦은 응답은 기존 epoch 검사로 무시한다. 결과 불명 작업은 `souvenirPrint` ID로 조회하며 자동 재출력·idle 초기화를 하지 않는다.

## 일괄 출력 복구 · 2026-10-16

기존 오류·촬영 Blob·세션은 목록 조회와 확인 창 동안 유지한다. 확인 창은 unknown 항목을 기본 선택하지 않으며 실물 미출력 확인/이미 출력됨을 명시적으로 선택한다. 진행 중/카드 회수 항목은 비활성화한다. 배치 제출은 busy로 중복 터치를 막고 120초 제한, 결과 불명은 print_recovery 작업 ID로 조회한다. 창에는 전송/미리보기/실물 확인/이미지 없음/오류/미처리 건수를 분리한다. 창을 닫은 후 현재 출력의 실제 작업 상태를 다시 조회하며 서버 성공 없이 완료 화면을 만들지 않는다. 초기화/페이지 종료는 요청을 취소하고 오래된 응답을 폐기한다. 모달 동안 idle 초기화를 중지하고 초점 순환에 체크박스를 포함한다.
