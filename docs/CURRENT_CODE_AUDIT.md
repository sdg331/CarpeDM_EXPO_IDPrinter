# Current Code Audit — 현재 구현과 목표의 차이

> 이 문서는 이전 Raspberry Pi 프로토타입의 인수인계 시점 기록입니다. 이 저장소에서 이후 구현한 화면과 연동 범위는 `IMPLEMENTATION_STATUS.md`와 루트 `README.md`를 우선합니다.

> 이 문서는 ZIP으로 전달된 현재 코드 기준. 목표 설계와 섞지 않는다.

## 1. 현재 구조

```text
frontend/kiosk.html       # 단일 HTML/CSS/JS 키오스크
backend/app.py            # FastAPI endpoints
backend/face.py           # YuNet + SFace
backend/badge.py          # badge renderer
backend/printing.py       # screen / escpos / cups
assets/prototypes.npz     # character prototypes
scripts/                  # calibration/build/diagnostics
```

## 2. 현재 확인된 기술

CURRENT:
- FastAPI
- OpenCV headless
- YuNet (`FaceDetectorYN`)
- SFace (`FaceRecognizerSF`)
- 128D face embedding
- 8-character matching
- 576px-class thermal badge rendering pipeline
- Browser `getUserMedia()` camera preview/capture
- `/api/detect` face-count preview endpoint
- `/api/match` matching endpoint
- `/api/issue` badge render/print endpoint
- 800×1280 fixed-stage scaling
- 90sec idle reset with 15sec warning

Backend tests: **14 passed** at audit time.

## 3. 현재 API

| Method | Endpoint | CURRENT role |
|---|---|---|
| GET | `/api/health` | model/printer/calibration diagnostics |
| GET | `/api/characters` | 8 character metadata |
| POST | `/api/detect` | face count/confidence for preview |
| POST | `/api/match` | frame → 8-character scores |
| POST | `/api/issue` | name/dept/char/emp_no → badge + print |

## 4. 현재 UX와 목표의 차이

### Flow order
CURRENT:
`이름 → 부서 → 촬영 → 분석 → 결과 → 출력`

TARGET:
`HOME 입사/퇴근 → 팀 → 이름 → AI A/B → 촬영 → 결과 → NFC → 출력`

### Teams
CURRENT: 4 teams
- 디자인팀
- 개발팀
- 기획팀
- 마케팅팀

TARGET: 6 teams
- 개발팀
- AI팀
- 디자인팀
- 기획팀
- 마케팅팀
- 인사팀

### AI Modes
CURRENT: A-style character match only.
TARGET:
- A: character matching
- B: local CV formal profile synthesis

### NFC
CURRENT: not implemented.
TARGET: ACR1252U register/read + MirrorTing session bridge.

### Checkout
CURRENT: not implemented.
TARGET: NFC resolve → MirrorTing report → thermal report print.

### Employee number
CURRENT: browser creates random number.
TARGET: backend/session should own stable session/employee identifier.

### Idle
CURRENT: 90s total / 15s warning.
TARGET default: 60s inactivity reset policy, final timing verified in exhibition test.

## 5. 반드시 제거/수정할 위험

### Random AI fallback — P0 blocker
CURRENT `startAnalyze()` has backend failure fallback using `Math.random()`.

TARGET:
- no random production result
- retryable failure → retry
- backend unavailable → human-readable error/operator path

### Current README/RUN inconsistency
RUN.md describes on-screen keyboard while current frontend code comments/target planning use physical keyboard.

TARGET:
- physical 2.4GHz keyboard for name only
- no virtual keyboard dependency

## 6. 유지해야 할 좋은 기반

- YuNet/SFace pipeline
- no disk-save behavior for match frames
- detect endpoint that skips expensive embedding
- printer abstraction (`screen`, `escpos`, `cups`)
- health endpoint
- 800×1280 scaler
- automated tests

## 7. Recommended Migration Strategy

전시 일정상 framework migration은 하지 않는다.

1. existing `kiosk.html` behavior를 screen/state 명세에 맞춰 단계적으로 정리
2. 필요할 때 JS/CSS를 파일로 분리
3. API adapter layer를 추가
4. NFC/checkout/Mode B를 확장
5. 마지막에 실제 Pi/hardware soak test

React/Vite 도입은 EXPO 안정화 이후 별도 기술 부채 개선 작업으로 취급한다.
