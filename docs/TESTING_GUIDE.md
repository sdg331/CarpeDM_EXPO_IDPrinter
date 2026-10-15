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

## 사진 전용 경로

`npm test`, `.venv/bin/python -m pytest tests -q`, `.venv/bin/python scripts/preflight.py --souvenir`로 검증한다. `integrations/mirrorting/test_kiosk_flow.py`는 동반 패치를 적용한 MirrorTing 저장소에서 실행하는 테스트이며 이 저장소에서 bare pytest 수집 대상이 아니다. [실물 확인 순서](SOUVENIR.md)를 따른다.

## 사진 포함 리포트·센터 팁

`npm test`, `.venv/bin/python -m pytest tests -q`와 사진 포함/생략·중복 JSON 요청·안전 재시도·결과 불명 잠금·7개 팁 줄바꿈을 확인한다. 실제 프린터에서는 사진 명암과 긴 용지 배출·절단을 점검한다. [최신 QA](qa/REPORT_PHOTO_TIPS_2026-10-12.md).

## 일괄 복구·응원 인화 · 2026-10-16

`npm test`와 `python -m pytest tests integrations/mirrorting/test_bridge_client.py -q`를 실행한다. `test_print_recovery.py`는 세 출력 종류·같은 배치/동시 요청·첫 오류 중단·재시작·기존 이미지 누락·이미 출력됨·회수 카드·동작 중·만료·출처 차단을 검증한다. `print-recovery.test.mjs`는 오류 화면 진입, 항목 선택 전 비활성, 실제 작업 ID 유지, 초기화 후 늦은 목록 응답 폐기, 샘플 경계를 검증한다. 800×1280에서 기념사진 확인·출력 오류·확인 창을 확인한다. 실제 Pi에서는 USB 연결 복구 후 대기열을 확인하고 미출력 2건과 이미 출력된 1건을 구분해 처리하며 용지/절단/사진 명암을 별도 확인한다.
