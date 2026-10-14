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

## 실제 얼굴 맵 · 2026-10-14

촬영 준비는 count>0 및 ok:true로 판단한다. 여러 얼굴은 ready 상태이며 선택 대상에 실제 박스·눈/코/입5점과 안내를 표시한다. 카메라 전체 프레임을 contain으로 보여주고 같은 정규화 좌표를 미러링한다. 한 사람이 아니어도 촬영을 허용한다.

분석 시작 시 captureFace:null, 실제 match 응답5점 및 별도 상세478점을 기다린다. 상세 실패는 실제5점만 유지한다. 캔버스는 데이터가 없으면 숨기며 화면 중앙 임의 맵은 없다. 같은 capture Blob·processing·busy 및 취소 신호를 확인해 늦은 다른 방문자의 좌표를 버린다. 특징점 토글은 분석 busy 중에도 허용하고 다른 진행 작업은 잠근다. 성공·오류·재촬영·초기화·pagehide에 사진/좌표를 해제한다.

UI 고정 미리보기의 분석 화면은 공개 캐릭터 샘플을 실제 좌표 API로 분석하며 샘플임을 표시한다. 카메라·NFC·출력은 실행하지 않는다.
