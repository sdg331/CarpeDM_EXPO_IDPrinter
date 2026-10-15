# Error Handling

## Principle

Error is a designed state, not an afterthought.

For each error answer:
1. What happened?
2. Can the user fix it?
3. Is retry safe?
4. Does session survive?
5. Can the same side-effect happen twice?
6. What does operator need to know?

## Categories

### User-correctable
- no person
- multiple people
- bad position
- unknown NFC card

Use guidance, not red system-failure treatment.

### Retryable system/hardware
- camera not ready
- AI timeout
- NFC timeout/write/verify failure
- printer offline/error
- network timeout

Preserve session.

### Fatal/integrity
- backend unavailable after retries
- session corrupt/unknown
- unrecoverable device condition

Stop unsafe continuation and provide safe reset/operator path.

## Camera Copy

- NO_PERSON: `카메라 앞으로 조금 더 가까이 와주세요.`
- MULTIPLE_PEOPLE: `한 분만 화면 안에 들어와 주세요.`
- CAMERA_UNAVAILABLE: `카메라를 사용할 수 없어요. 잠시 후 다시 시도해주세요.`

## AI

- timeout: `결과 생성이 예상보다 오래 걸리고 있어요. 다시 시도해주세요.`
- failure: `분석하지 못했어요. 다시 촬영해볼게요.`

Never choose a random character on failure.

## NFC

- timeout: `카드를 확인하지 못했어요. 다시 한 번 태그해주세요.`
- write failed: `카드에 정보를 등록하지 못했어요. 카드를 다시 태그해주세요.`
- reader offline: `카드 리더를 사용할 수 없어요. 잠시 후 다시 시도해주세요.`

Preserve team/name/AI result.

## Printer

- offline/error: `프린터를 사용할 수 없어요. 잠시 후 다시 시도해주세요.`
- paper out: use only if backend detects reliably.

Preserve badge/report data.

## Backend

Fallback visitor copy:
`문제가 발생했어요. 다시 시도해주세요.`

Optionally show short reference code for operator.

Never show:
- Python traceback
- TypeError
- raw HTTP response
- USB/PCSC stack traces

## Retry

No unlimited silent retry.
Read-only health/report fetch may use limited automatic retry.
NFC write/print should prefer explicit retry with idempotency/job identity.

## Fatal Home Reset

Before clearing session, ensure side-effect state is known enough to avoid duplicate write/print on restart.

## 사진 전용 오류 · 2026-10-12

`SOUVENIR_NOT_CONFIGURED`는 소개 URL/전용 UID 미설정, `SOUVENIR_CARD_REQUIRED`는 일반 카드, `SOUVENIR_CARD`는 전용 카드의 입사 등록 차단이다. `SOUVENIR_PASS_EXPIRED`는 HOME에서 다시 카드 확인, `SOUVENIR_RENDER_FAILED`는 장치 접근 전 안전한 명시적 재시도다. 사진 출력의 `UNKNOWN_OUTCOME`은 기존 상태 조회/운영자 실물 확인만 허용한다. `SOUVENIR_PRINT_PENDING`이면 기존 결과 불명 또는 실행 중 인화를 먼저 확인해야 새 승인/인화를 진행할 수 있다.

## 화면 일괄 복구 · 2026-10-16

출력 오류 및 기념사진 전역 차단은 `미출력 건 한 번에 출력`에서 복구한다. unknown은 운영자가 실물/대기열을 확인한 선택적 재출력 또는 printed 확인만 허용한다. running은 선택 불가, success는 대상에서 제외한다. 이미지가 없으면 missing_image로 알리고 차단만 해제한다. 복구 중 같은 배치 ID 재전송은 이전 결과를 재사용하며 프린터 실패 시 나머지는 유지한다. `PRINT_QUEUE_UNAVAILABLE`은 복구 이미지를 보관하지 못한 장치 접근 전 오류다.
