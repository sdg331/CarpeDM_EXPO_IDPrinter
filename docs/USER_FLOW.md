# User Flow

## Screen Registry

- SCR-01 HOME
- SCR-02 TEAM_SELECT
- SCR-03 TEAM_DETAIL
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
SCR-03 TEAM_DETAIL
  ├─ 다른 팀 보기 → SCR-02
  ↓ 이 팀으로 입사하기
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
