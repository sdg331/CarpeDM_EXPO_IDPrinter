# Testing Guide

## Philosophy

Test as a physical kiosk system, not just a webpage.

```text
Unit/Backend tests
→ Screen checks
→ Flow checks
→ Failure scenarios
→ Raspberry Pi
→ Real hardware
→ Repeated exhibition soak
```

## Existing Test Baseline

CURRENT audit: `pytest tests/ -q` → **14 passed**.

Run:

```bash
pytest tests/ -v
```

Do not accept frontend work that breaks existing backend matching/badge tests.

## Mandatory Viewport

Primary: 800×1280 portrait.

Check:
- [ ] no horizontal scroll
- [ ] no clipped CTA
- [ ] no hover-only content
- [ ] 48×48 minimum target guideline
- [ ] loading/error/retry visible

## Name Input

- [ ] 2.4GHz receiver detected
- [ ] Korean input works
- [ ] IME composition works
- [ ] visible focus
- [ ] reboot reconnect tested
- [ ] Enter does not bypass invalid state

## Camera Matrix

| Scenario | Expected |
|---|---|
| camera init slow | initializing |
| no face/person | guidance |
| multiple faces | one-person guidance |
| invalid position if supported | reposition |
| capture double tap | one request |
| capture success | one transition |
| backend error | retry/human copy |

## AI Matrix

| Scenario | Expected |
|---|---|
| normal A | correct character result |
| backend unreachable | error, never random result |
| no face | retake guidance |
| multiple faces | retake guidance |
| long processing | meaningful waiting |
| stale response after reset | ignored |
| repeated tap | one logical job |
| Mode B local failure | recover/retake, no cloud fallback |

## NFC Matrix

- [ ] no card → waiting
- [ ] timeout → retry
- [ ] reader offline → error/operator path
- [ ] write fail → preserve session + retry
- [ ] verify fail → retry/error
- [ ] repeated tag → no duplicate registration

## Printer Matrix

- [ ] offline preserves result/session
- [ ] print timeout has recovery
- [ ] backend error never displays false success
- [ ] repeated tap creates one logical job
- [ ] late response after retry is deduplicated by backend strategy when implemented

## Session Isolation

Run Visitor A → reset → Visitor B.

B must not see A:
- name
- team
- image/profile
- AI result
- NFC status
- report

## Navigation Stress

- rapid tapping
- back/next alternation
- inactivity warning
- browser refresh during safe screen
- Pi reboot

## Real Raspberry Pi Validation

Required:
- Chromium target
- 800×1280 display
- touch
- physical keyboard
- Camera Module 3
- FastAPI
- ACR1252U
- ZTP-80USL2

Desktop Chrome alone is not release approval.

## Soak Test

Before EXPO, repeatedly alternate check-in/check-out for as many sessions as schedule permits.

Record:
- session count
- failure count
- recovery count
- browser/memory instability
- unexpected reload
- duplicate prints
- duplicate NFC writes
- thermal throttling/temperature if monitored

## Release Checklist

- [ ] all P0 acceptance criteria
- [ ] tests green
- [ ] production random fallback removed
- [ ] real hardware tested
- [ ] session reset tested
- [ ] operator knows basic recovery
