# User Flow

## Current visitor flow · 2026-10-12

입사: HOME → 팀 → 이름 → 캐릭터 매칭 안내 → 촬영 → 분석 → 추천 확인/선택 → NFC → 사원증 → 완료.
추천 확인에서 `다른 캐릭터 고르기`를 선택하면 8명 중 직접 고를 수 있다. 취소는 현재 결과 유지.
이름·팀을 유지하고 선택한 캐릭터를 발급에 사용한다. NFC 등록 이후에는 변경하지 않는다.
퇴근: HOME → NFC → 실제 체험 기록 → 선택적 기념사진 → 리포트 → 출력 → 완료.

2026-10-12: 확인한 기념사진을 종이 리포트에 함께 인쇄한다. 사진을 건너뛰어도 체험 기록과 센터 선생님 첨삭 팁 한 가지를 출력한다. 팁은 미리보기에서 먼저 확인하며 재시도에서도 유지한다. [사진·팁 기준](REPORT_PHOTO_TIPS.md).
아래 A/B·팀 상세 흐름은 이전 설계 기록이며 현재 방문자 흐름에는 A/B 선택과 팀 상세가 없다.

## Screen Registry

- SCR-01 HOME
- SCR-02 TEAM_SELECT
- SCR-03 TEAM_DETAIL (2026-10-08 흐름에서 제외)
- SCR-04 NAME_INPUT
- SCR-05 AI_MODE_SELECT
- SCR-06 AI_MODE_DETAIL_A
- SCR-07 AI_MODE_DETAIL_B
- SCR-08 CAMERA
- SCR-09 AI_PROCESSING
- SCR-10 AI_RESULT_A
- SCR-11 AI_RESULT_B
- SCR-12 NFC_REGISTER
- SCR-13 BADGE_PRINTING
- SCR-14 CHECKIN_COMPLETE
- SCR-15 CHECKOUT_NFC
- SCR-16 CHECKOUT_RESULT
- SCR-17 REPORT_PREVIEW
- SCR-18 REPORT_PRINTING
- SCR-19 CHECKOUT_COMPLETE
- SCR-20 FATAL_ERROR
- SCR-90 IDLE_WARNING (overlay)

## Check-in Happy Path

```text
SCR-01 HOME
  ↓ 입사하기
SCR-02 TEAM_SELECT
  ↓ 팀 선택
SCR-04 NAME_INPUT
  ↓ 이름 확인
SCR-05 AI_MODE_SELECT
  ├─ A → SCR-06 AI_MODE_DETAIL_A
  └─ B → SCR-07 AI_MODE_DETAIL_B
          ↓ 시작
SCR-08 CAMERA
  ↓ capture success
SCR-09 AI_PROCESSING
  ├─ A success → SCR-10 AI_RESULT_A
  └─ B success → SCR-11 AI_RESULT_B
          ↓ 결과 확인
SCR-12 NFC_REGISTER
  ↓ verified
SCR-13 BADGE_PRINTING
  ↓ success
SCR-14 CHECKIN_COMPLETE
  ↓ timeout / 홈
SCR-01 HOME
```

## Check-out Happy Path

```text
SCR-01 HOME
  ↓ 퇴근하기
SCR-15 CHECKOUT_NFC
  ↓ session resolved
SCR-16 CHECKOUT_RESULT
  ↓ 다음
SCR-17 REPORT_PREVIEW
  ↓ 출력
SCR-18 REPORT_PRINTING
  ↓ success
SCR-19 CHECKOUT_COMPLETE
  ↓ timeout
SCR-01 HOME
```

## Back Navigation

### Before irreversible operations
Back allowed unless state is actively processing.

- SCR-02 → HOME
- SCR-03 → TEAM_SELECT
- SCR-04 → TEAM_DETAIL
- SCR-05 → NAME_INPUT
- SCR-06/07 → AI_MODE_SELECT
- SCR-08 ready/no-person/etc → AI detail

### During processing
Back disabled during:
- capture request
- AI job submission/processing where cancellation is unsafe
- NFC writing/verifying
- print job submission/printing

### After side effect
Do not navigate back to a screen that can re-submit the same NFC/print side effect.

## Camera Branches

```text
initializing → ready
ready → no_person → ready
ready → multiple_people → ready
ready → bad_position → ready
ready → capturing → captured
any → camera_error → retry / safe exit
```

## AI Failure

```text
processing
  ├─ success → result
  ├─ timeout → retry policy
  └─ error → retry or safe home
```

Random character fallback is forbidden.

## NFC Registration Failure

```text
waiting → detected → writing → verifying → success
waiting → timeout → retry
writing/verifying → error → preserve session → retry
reader offline → error → operator/retry
```

## Printer Failure

Badge/report data remains in session.

```text
printing → success
printing → offline/error → retry/operator guidance
```

Retry must not create duplicate physical output if original job may have succeeded. Backend should provide operation/job identity.

## Checkout No MirrorTing Data

PROPOSED:
- show `아직 MirrorTing 체험 기록을 찾지 못했어요.`
- primary: `다시 확인`
- secondary: `기본 리포트 출력` only if product owner approves

Do not invent assessment data.

## Inactivity

Target default:
- 60 sec inactivity policy
- warning before reset recommended (e.g. final 15 sec)
- exact timing adjustable after kiosk usability test

Skip/handle carefully on irreversible processing states.

Reset clears:
- team
- name
- aiMode
- capture reference
- AI result
- NFC state
- print state
- checkout/report state

## Fatal Error

Use SCR-20 only when local recovery is unsafe:
- session integrity unknown
- backend persistently unavailable
- non-recoverable hardware state

Offer safe Home/operator path.

## 전용 카드 기념사진 · 2026-10-12

HOME 기념사진만 남기기 → 카드 자동 읽기 → 전용 카드 → 촬영/취소 → 사진·QR 확인/재촬영 → 인화 → 완료/카드 반납. 일반 퇴근 카드 확인에서도 전용 카드면 이 경로로 분기한다. 일반 카드는 사진 전용 메뉴에서 거부한다. 별도 이름·AI·체험 기록 조회는 없다. [운영](SOUVENIR.md).

2026-10-14 전시 촬영: 여러 사람이 화면에 보이면 얼굴이 가장 크게 보이는 사람을 선택한다. 표시된 박스의 사람이 정면을 보고 촬영한다. 분석 화면은 실제 얼굴 특징점을 기본으로 표시하며 켜기/끄기가 가능하다. 기존 결과·사원증 흐름은 유지한다.
