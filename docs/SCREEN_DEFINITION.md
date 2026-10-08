> 2026-10-05 UI 변경: SCR-05/07/11의 A/B 선택·B 생성 진입은 제거했다. 이름 이후 SCR-06 캐릭터 매칭으로 연결한다. 퇴근은 SCR-16→SCR-26 PHOTO_CAMERA→SCR-27 PHOTO_REVIEW→SCR-17 REPORT이며 사진 없이 진행 가능하다. 아래 이전 B 명세는 이력이다. 기념사진은 화면 전용이며 종이 사진 인쇄는 미연결이다.

> 2026-10-05 전체 점검 수정: SCR-16에서 기념사진 또는 `사진 없이 리포트 보기`를 선택한다. 촬영 화면의 권한 대기/연결 종료는 공통 카메라 오류로 복구한다. 상태 창과 홈 초기화는 서버 상태를 새로 조회한다. 조회 응답은 현재 입력·사진을 지우지 않으며 홈 초기화 자체는 이전 방문자 정보를 제거한다. AI·NFC·출력 오류는 실패 원인과 다음 행동을 중심으로 표시한다. 샘플 완료는 실제 등록한 카드 이동을 지시하지 않는다. [검증 결과](qa/AUDIT_FIXES_2026-10-05.md).

# Screen Definition

2026-10-08 공통 시각 갱신: 기존 화면 ID·상태·API 흐름을 유지하며 HOME의 블루/네이비/회색을 모든 화면에 적용했다. 카드 그림자와 중복 표면을 줄이고 입력·사진·상태·리포트의 목적에 맞게 구성한다. SCR-06은 큰 캐릭터 사진을 표시하고 과정 토글은 제거했다. SCR-12는 340px 리더 아이콘과 작은 방문자 정보 카드로 구성한다. SCR-15는 400px 리더 아이콘을 중앙 정렬한다. 장식 애니메이션을 제거하고 분석·카드·출력 작업은 안내 문구 위 단일 로딩 표시로 알린다. 샘플 화면도 동일한 키오스크 크기 규칙을 사용한다. 웹 풋터도 동일한 제작 표기를 사용한다. 검증 범위는 [TOUCH_UI_2026-10-08.md](qa/TOUCH_UI_2026-10-08.md)를 따른다.

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
- 상단 MIRRORTING WORKS 브랜드 한 개. 중앙 로고는 표시하지 않는다.
- `입사를 진심으로 / 축하합니다.`를 두 줄 제목으로 표시한다. 부제는 `당신과 함께할 오늘을 기대합니다.`로 표시하고 영어 환영 문구는 표시하지 않는다.
- 버튼 설명은 `나의 사원증 만들기`·`오늘의 기록 보기`로 짧게 표시한다.
- 환영 문구 아래에 `출근하기`·`퇴근하기` 선택 카드를 좌우로 배치한다. 왼쪽 출근 카드는 파란색, 오른쪽 퇴근 카드는 밝은 회색으로 표시한다.
- 800×1280 기준 환영 제목 52px, 부제 24px, 카드 제목 40px, 카드 설명 24px, 선택 카드 높이 최소 416px, 이미지 220px를 사용한다. 이미지는 상단 패딩 뒤 8px 여백을 두어 배치하고, 글은 하단에 배치한다. 웹 화면 폭이 640px 이하이면 카드를 세로로 배치하고 높이를 최소 128px로 줄이며 이미지 위 여백을 없앤다. 화면 목록 미리보기도 장치와 동일한 키오스크 스타일을 사용한다.
- 제작 표기 `동양미래대학교 컴퓨터공학부 전공동아리 CarpeDM`는 하단에 표시한다.
- 상단 장치 상태 버튼은 표시하지 않는다. 서버 연결 실패 안내는 화면에 유지한다.
- 샘플/웹 미리보기는 상단에서 모드를 명시한다.

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
- title: `어느 팀과 함께할까요?`
- subtitle: `선택한 팀이 사원증에 표시돼요.`
- 2×3 TeamCard grid, 152px icon and minimum 240px card height
- back

**Teams**:
1. 개발팀
2. AI팀
3. 디자인팀
4. 기획팀
5. 마케팅팀
6. 인사팀

**Action**: card tap → store selected team → SCR-04 NAME_INPUT.

**API**: none required if team content is local config.

**Timeout**: global inactivity.

**Error**: missing team config is development/config error; do not silently omit team.

**Done**: all 6 visible without unintended scrolling, touchable, selected team passes correctly.

---

## SCR-03 TEAM_DETAIL

2026-10-08: 실제 흐름과 화면 미리보기 목록에서 제외했다. 팀 선택 후 SCR-04로 바로 이동한다. 아래 명세는 이전 이력이다.

**Purpose**: 선택한 팀의 의미/업무를 빠르게 이해하고 확정.

**UI**:
- team icon
- team name
- 1–2 sentence description
- `주요 업무` 3 items
- keyword 3 readable tags
- `다른 팀 보기`
- `이 팀으로 입사하기`

2026-10-05 가독성 기준: 흰색 중앙 팝업에서 투명 아이콘과 48px 팀명, 26px 원문 설명을 표시한다. 세 업무는 26px 글씨를 가진 개별 중립 카드로 구분하며, 키워드는 26px 글씨의 연한 파란 태그로 표시한다. 업무·키워드 제목은 24px이다. 하단은 전체 폭의 104px 입사 버튼과 64px 보조 행동을 세로 배치한다. 작은 웹 화면에서는 업무를 세로 목록으로 묶고 업무·키워드 20px, 입사 버튼 72px를 사용한다. 모든 팀은 동일한 팝업 스타일을 사용하며 48px 이상의 닫기 버튼, 포커스 잠금·복귀, 배경 입력 차단을 유지한다.

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
- 유효한 1~10자 이름은 한글 조합 중에도 다음 버튼을 즉시 활성화한다. 버튼 터치는 현재 입력값으로 진행하며, 조합 확정용 Enter와 조합 중 form submit은 화면을 넘기지 않는다.
- physical keyboard required; no on-screen keyboard

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
현재 방문자 UI는 얼굴 확인·특징 추출·캐릭터 비교의 세 단계를 항상 표시한다. 설명을 접는 토글은 사용하지 않는다.

2026-10-06 안내 디자인: 실제 8개 캐릭터 자산을 미리보기로 표시하고, 세 단계 설명은 번호·아이콘·구분선이 있는 공통 패널로 구성한다. 미리보기는 분석 결과나 선택 상태를 뜻하지 않는다. 원래 설명·촬영 조건·시작 및 이름 수정 동작을 유지한다. 키오스크는 800×1280에 전체 내용과 버튼을 표시하며 작은 웹 미리보기는 캐릭터를 4열로 배치한다.

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

2026-10-06 표현: 상단 카메라 라벨과 감지 상태, 하단 반투명 안내 바로 구성한다. 준비 중·얼굴 확인 중·한 분씩 촬영·촬영 준비 완료·촬영 중·연결 확인 필요는 실제 카메라 상태를 따른다. 얼굴 위치를 추적하는 박스나 수치 진행률은 표시하지 않는다. 웹 미리보기와 퇴근 기념사진도 같은 상태 표현을 사용하며 샘플은 명시한다.

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
- captured photo with subtle decorative glowing points (shared by kiosk/web, modes A/B)
- sample mode explicitly uses a labeled fixture photo
- light points are visual decoration, not detected landmarks or progress
- reduced-motion disables the animation
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
- retryable → retake path preserving name/team/session; release the failed capture preview
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

2026-10-06 요약 카드: 등록 화면에서만 프로필을 144×192, 이름을 38px로 확대한다. 약 240px 카드에서 팀과 등록 상태를 사진 옆에 배치하며, 오류 안내·재시도 버튼까지 800×1280에 들어오는지 확인한다. 다른 화면의 요약 카드와 NFC 동작은 유지한다.

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
