# Screen Definition

## Naming Rule

Document/Figma/QA shared ID:

```text
SCR-XX SCREEN_NAME
```

Figma state frame:

```text
SCR-XX__SCREEN_NAME__state
```

Example:
`SCR-12__NFC_REGISTER__writing`

---

## SCR-01 HOME

**Purpose**: 입사/퇴근 진입점. 새 세션의 깨끗한 시작 상태.

**Entry**: app start, completion reset, fatal safe reset, inactivity reset.

**UI**:
- MIRRORTING WORKS brand
- short welcome copy
- large `입사하기` card/button
- large `퇴근하기` card/button

**Actions**:
- 입사 → SCR-02
- 퇴근 → SCR-15

**Data**: none. Previous visitor data must not appear.

**API**: optional health preflight only. HOME must not block forever on health request.

**Accessibility**: both actions large, text labels required, not icon-only.

**Done**: both flows reachable; old session cleared.

---

## SCR-02 TEAM_SELECT

**Purpose**: 6개 팀 중 입사 희망 팀 선택.

**Entry**: SCR-01 check-in.

**UI**:
- title: `어느 팀에 입사하시겠어요?`
- 2×3 TeamCard grid
- back

**Teams**:
1. 개발팀
2. AI팀
3. 디자인팀
4. 기획팀
5. 마케팅팀
6. 인사팀

**Action**: card tap → store temporary selected team → SCR-03.

**API**: none required if team content is local config.

**Timeout**: global inactivity.

**Error**: missing team config is development/config error; do not silently omit team.

**Done**: all 6 visible without unintended scrolling, touchable, selected team passes correctly.

---

## SCR-03 TEAM_DETAIL

**Purpose**: 선택한 팀의 의미/업무를 빠르게 이해하고 확정.

**UI**:
- team icon
- team name
- 1–2 sentence description
- `주요 업무` 3 items
- keyword 3 chips
- `다른 팀 보기`
- `이 팀으로 입사하기`

**Actions**:
- 다른 팀 보기 → SCR-02
- 확정 → session.team set → SCR-04

**API**: none.

**Done**: content matches `CONTENT_AND_ASSET_SPEC.md` exactly.

---

## SCR-04 NAME_INPUT

**Purpose**: 사원증/세션에 사용할 이름 입력.

**Entry**: team confirmed.

**UI**:
- selected team summary
- text input
- physical keyboard hint
- next CTA
- back

**Input**: physical 2.4GHz keyboard.

**Rules**:
- 1–10 characters target (matches current backend name max 10)
- trim leading/trailing whitespace
- empty value cannot proceed
- visible focus
- Korean IME composition must work
- virtual keyboard not required

**Actions**:
- next → save name → SCR-05
- back → SCR-03

**Done**: Korean name input verified on target Pi; Enter behavior does not bypass validation.

---

## SCR-05 AI_MODE_SELECT

**Purpose**: 촬영 전에 A/B 경험 선택.

**UI**:
- title: `어떤 AI 프로필을 만들어볼까요?`
- two equal AIModeCards

**A**: `AI 캐릭터 매칭` — 나와 가장 가까운 캐릭터 찾기

**B**: `AI 프로필 생성` — 나만의 사원증 프로필 만들기

**Actions**:
- A → SCR-06
- B → SCR-07
- back → SCR-04

**Done**: no silent preselection; mode stored only after user selection.

---

## SCR-06 AI_MODE_DETAIL_A

**Purpose**: A가 어떻게 동작하는지 이해하고 촬영 시작.

**Intro**:
`AI가 얼굴의 특징을 분석해 8명의 MIRRORTING WORKS 캐릭터 중 가장 가까운 캐릭터를 찾아드립니다.`

**HOW IT WORKS**:
1. 사람 탐지 — 카메라 앞 사용자를 찾습니다. *(Target; model TBD)*
2. 얼굴 분석 — 얼굴 위치와 촬영 상태를 확인합니다.
3. 특징 추출 — 딥러닝으로 얼굴 특징을 128차원 데이터로 변환합니다.
4. 캐릭터 비교 — 8개 캐릭터의 특징과 비교합니다.
5. 최종 매칭 — 가장 가까운 캐릭터를 선택합니다.

**Actions**:
- 다른 방식 보기 → SCR-05
- `캐릭터 매칭 시작하기` → SCR-08

**Done**: 기술 표현은 과장 없이 현재/목표 구현과 일치.

---

## SCR-07 AI_MODE_DETAIL_B

**Purpose**: B 로컬 CV 합성 방식 이해.

**Intro**:
`촬영한 얼굴은 그대로 유지하면서 컴퓨터 비전 기술로 사원증용 프로필 사진을 만듭니다.`

**HOW IT WORKS**:
1. 사람·얼굴 탐지
2. 자세 분석 — 얼굴/어깨 위치
3. 인물 분리 — 사람/배경 구분
4. 정장 합성 — 투명 정장 PNG를 위치에 맞게 합성
5. 프로필 완성 — 배경/구도 정리 및 품질 확인

**Constraints**:
- no cloud image generation API
- no gender inference for outfit selection
- shared neutral formal outfit template preferred

**Actions**:
- 다른 방식 보기 → SCR-05
- `AI 프로필 만들기` → SCR-08

---

## SCR-08 CAMERA

**Purpose**: 정확히 한 사용자의 유효한 사진 확보.

**Entry required**: team, name, aiMode.

**CURRENT technical path**:
- browser `getUserMedia` preview/capture
- low-cost preview frame → `/api/detect`
- captured full frame → backend AI path

**UI**:
- camera preview
- dynamic face/person guide
- one short instruction
- capture CTA
- safe back when not processing

**States**:
- initializing: `카메라를 준비하고 있어요.`
- ready: `얼굴이 잘 보이도록 화면을 바라봐주세요.`
- no_person: `카메라 앞으로 조금 더 가까이 와주세요.`
- multiple_people: `한 분만 화면 안에 들어와 주세요.`
- bad_position: `얼굴이 잘 보이도록 위치를 조금 조정해주세요.`
- capturing: `촬영 중이에요. 잠시만 그대로 있어주세요.`
- error: `카메라를 사용할 수 없어요.`

**Action rules**:
- capture enabled only when valid ready condition is met
- double submit blocked
- back disabled during capture

**API CURRENT**: `/api/detect` for face count; target may extend quality metadata.

**Done**: no fixed-box-only UX; state responds to actual detection/quality information available from backend.

---

## SCR-09 AI_PROCESSING

**Purpose**: A/B 처리 중 시스템이 살아있음을 명확히 표시.

**UI**:
- mode-aware title
- step animation
- indeterminate/progress only if truthful

**Mode A steps**:
face detect → align → SFace 128D → compare 8 → validate result

**Mode B steps**:
detect → pose/landmark → segmentation → suit composite → final quality

**Rules**:
- fake numeric percentage forbidden
- duplicate job forbidden
- random fallback forbidden

**Success**:
- A → SCR-10
- B → SCR-11

**Failure**:
- retryable → retry path preserving session/capture when valid
- fatal backend → SCR-20 or operator path

---

## SCR-10 AI_RESULT_A

**Purpose**: 캐릭터 매칭 결과를 명확하고 정직하게 표시.

**UI**:
- matched character hero
- name/team context
- wording: `8명의 캐릭터 중 가장 가까운 캐릭터`
- optional ranking/relative score if useful
- continue CTA

**Do not say**: `82% 닮았습니다` unless metric semantics are explicitly proven.

**CURRENT data**: `/api/match` returns top/order/display/raw/margin; UI should use visitor-safe values only. `raw` is diagnostic.

**Action**: continue → SCR-12.

---

## SCR-11 AI_RESULT_B

**Purpose**: 생성된 사원증용 프로필 확인.

**UI**:
- composited profile preview
- name/team
- short explanation that face is preserved/local processing
- continue

**Actions**:
- optional retake only if product owner approves/retry contract exists
- continue → SCR-12

**API**: PROPOSED Mode B generation contract.

---

## SCR-12 NFC_REGISTER

**Purpose**: current session을 NFC 사원증과 연결.

**UI states**:
- waiting: `사원증 카드를 태그해주세요.`
- detected: `카드를 확인했어요.`
- writing: `사원 정보를 등록하고 있어요.`
- verifying: `등록 정보를 확인하고 있어요.`
- success: `사원증 등록이 완료됐어요.`
- timeout/error: next action + retry

**Rules**:
- NFC logic is backend-owned
- no duplicate write
- success only after backend confirmation/verification
- retryable failure preserves AI result/session

**Success** → SCR-13.

---

## SCR-13 BADGE_PRINTING

**Purpose**: 80mm badge print status.

**States**:
- preparing
- printing
- success
- offline/error
- paper_out only if backend can actually detect it

**Rules**:
- exactly-once user intent; duplicate tap protection
- session/result preserved on retryable failure

**Success** → SCR-14.

---

## SCR-14 CHECKIN_COMPLETE

**Purpose**: 입사 완료 및 스마트미러 이동 안내.

**UI**:
- success state
- `사원증 발급이 완료됐어요.`
- `이제 사원증을 가지고 MirrorTing 스마트미러로 이동해주세요.`
- home action / auto reset

**Reset**: clear visitor UI/session state after configured completion timeout.

---

## SCR-15 CHECKOUT_NFC

**Purpose**: 퇴근 사용자를 NFC로 식별.

**States**:
- waiting
- detected
- resolving
- success
- unknown_card
- timeout
- reader_error

**Copy**:
`사원증을 태그해주세요.`

**Success** → SCR-16.

---

## SCR-16 CHECKOUT_RESULT

**Purpose**: 사용자/세션 및 MirrorTing 결과 조회 상태 확인.

**UI**:
- name/team
- check-in session context
- MirrorTing result availability

**Branches**:
- result exists → next
- no result → retry fetch / approved fallback report path

**Do not invent** MirrorTing scores or feedback.

---

## SCR-17 REPORT_PREVIEW

**Purpose**: 출력 전 리포트 확인.

**Content target**:
- MIRRORTING WORKS
- name / team / employee/session ID
- check-in/out time if reliable
- MirrorTing scenario/summary
- strength
- next action
- Mode A character or Mode B profile-created marker

**Action**: `퇴근 리포트 출력` → SCR-18.

---

## SCR-18 REPORT_PRINTING

Same printer state principles as SCR-13, with separate report job identity.

Success → SCR-19.

---

## SCR-19 CHECKOUT_COMPLETE

**Purpose**: 퇴근 완료.

Copy example:
`오늘도 수고하셨습니다.`

Auto reset to HOME and clear session.

---

## SCR-20 FATAL_ERROR

Use only when local recovery is unsafe.

**UI**:
- human-readable issue
- safe next action
- Home/reset if safe
- optional short diagnostic reference for operator

Never display raw traceback/HTTP JSON dump.

---

## SCR-90 IDLE_WARNING

Overlay/modal before inactivity reset.

**UI**:
- `계속 진행하시겠어요?`
- countdown
- `계속하기`

Any valid user interaction resumes session.
Do not interrupt irreversible in-flight operations without explicit policy.
