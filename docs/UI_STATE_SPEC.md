# UI State Specification

## Principle

복잡한 하드웨어 흐름을 `isLoading`, `hasError` 같은 여러 boolean 조합으로 만들지 않는다. 도메인별 explicit state를 사용한다.

## Session

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
healthy
degraded
unavailable
```

Health state may help operator diagnostics, but visitor flow should not expose technical service names unnecessarily.

## Action Lock

Lock duplicate action while these are in flight:
- camera capture
- AI submission
- NFC write/verify
- badge print
- checkout resolve
- report print

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
