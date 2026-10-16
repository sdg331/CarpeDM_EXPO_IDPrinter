# Testing Guide

2026-10-16 운영 MediaPipe 경로: `npm test`, `.venv/bin/python -m pytest tests -q`, `git diff --check`를 실행한다. `/api/match/landmarks`에 동일 샘플을 반복 전송해 순위·근거 재현성, any/male/female 후보 수·필터, 실제478점과9개 비교값을 확인한다. 800×1280 결과의 근거·측정 표 펼치기/접기·터치 스크롤, 좁은 웹 결과와 특징점 토글도 확인한다. `/api/match`는 SFace 비교 기준이므로 운영 추천 확인에는 사용하지 않는다. 실제 참가자의 닮음·Pi 지연·실물 카드/출력은 별도 검증한다.

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

2026-10-16 SCR-09: any/male/female에서 왼쪽 미리보기는4장, 실제 비교 후보는8/4/4인지 확인한다. 오른쪽 촬영 사진의 미러링·contain 좌표478개와 토글, reduced-motion의 첫 장 고정, 오류 시 사진·순환 제거를 확인한다. A/B 응답 전에는 결과가 없고, 응답 이후에는 최소 유지 시간·좌표 표시용 대기 없이 결과를 반환하는지 검증한다. 오류/취소·늦은 좌표 폐기를 유지한다. 좌표가 결과와 함께 도착하면 표시 확인을 위해 기다리지 않는다. 실제 Pi 성능은 별도 측정한다.

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

## 사진 전용 경로

`npm test`, `.venv/bin/python -m pytest tests -q`, `.venv/bin/python scripts/preflight.py --souvenir`로 검증한다. `integrations/mirrorting/test_kiosk_flow.py`는 동반 패치를 적용한 MirrorTing 저장소에서 실행하는 테스트이며 이 저장소에서 bare pytest 수집 대상이 아니다. [실물 확인 순서](SOUVENIR.md)를 따른다.

## 사진 포함 리포트·센터 팁

`npm test`, `.venv/bin/python -m pytest tests -q`와 사진 포함/생략·중복 JSON 요청·안전 재시도·결과 불명 잠금·7개 팁 줄바꿈을 확인한다. 실제 프린터에서는 사진 명암과 긴 용지 배출·절단을 점검한다. [최신 QA](qa/REPORT_PHOTO_TIPS_2026-10-12.md).
