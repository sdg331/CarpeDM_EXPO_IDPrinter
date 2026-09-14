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
