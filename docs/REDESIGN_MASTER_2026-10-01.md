# MIRRORTING WORKS Frontend Redesign Master — 2026-10-01

> 역할: 2026 EXPO 사원증/퇴근 리포트 키오스크의 **리디자인 기준 문서**.
> 기존 기능 흐름과 백엔드 계약을 보존하면서 카피, 화면 연출, 아이콘, 모션, 상태 표현을 개선한다.

## 1. 이번 리디자인에서 바꾸지 않는 것

기존 IA와 핵심 상태 전이는 유지한다.

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
- SCR-90 IDLE_WARNING overlay

특히 NFC 등록/조회, 사원증 출력, operationId/idempotency, 오류 복구 규칙은 기존 백엔드 계약을 그대로 우선한다.

## 2. 이번 리디자인에서 바꾸는 것

- 화면 카피를 "기능 설명"보다 "입사/출근/퇴근 경험" 중심으로 수정
- 화면별 레이아웃을 목적에 따라 다르게 구성
- 3D hero/team icon asset 체계 도입
- touch pressed/selected/loading/success/error 상태를 정교하게 표현
- SCR-03은 **논리 상태는 유지**하되 사용자에게는 SCR-02 위에 뜨는 modal처럼 보이게 표현
- AI 처리 화면은 실제 처리 상태와 일치하는 정보만 표시
- 카메라/NFC/프린터는 하드웨어 상태를 시각적으로 명확히 표현

## 3. 확정 카피

### SCR-01 HOME

Primary:
- `입사하신 것을 진심으로 축하드립니다.`
- `오늘의 직장 생활을 시작해볼까요?`

Actions:
- `출근하기`
- `퇴근하기`

Visual:
- 사원증 3D icon
- 퇴근 리포트 3D icon
- 두 hero object를 중앙에 대각선으로 배치

### SCR-02 TEAM_SELECT

Title:
- `어느 팀의 합격 문자를 받으셨나요?`

Teams:
- 개발팀
- AI팀
- 디자인팀
- 기획팀
- 마케팅팀
- 인사팀

Interaction:
- pointer 환경: subtle hover
- touch 환경: pressed → selected → modal
- hover에만 정보를 숨기지 않는다

### SCR-03 TEAM_DETAIL

표현 방식:
- SCR-02가 뒤에 남아 있고 dim/blur 처리
- 중앙에 dark translucent modal
- 팀 icon / 팀명 / 1~2문장 소개 / 키워드 3개 / 주요 업무 3개
- Primary: `이 팀으로 입사하기`
- Secondary: `다른 팀 보기`

내부 상태 ID는 SCR-03을 유지한다.

## 4. 화면별 '장면' 분리

모든 화면을 `큰 제목 + 카드 + 파란 버튼`으로 반복하지 않는다.

| Screen | Scene type | 핵심 연출 |
|---|---|---|
| HOME | Hero | 3D object + 큰 환영 카피 |
| TEAM_SELECT | Explore | 2×3 grid, 선택 탐색 |
| TEAM_DETAIL | Layer | 기존 화면 위 modal |
| NAME_INPUT | Focus | 넓은 여백 + 입력창 중심 |
| AI_MODE_SELECT | Compare | A/B 두 경험 비교 |
| AI_MODE_DETAIL | Explain | 단계/스토리형 설명 |
| CAMERA | Immersive | 프리뷰가 화면의 주인공 |
| AI_PROCESSING | Process | 실제 처리 상태 표시 |
| AI_RESULT | Reveal | 결과 이미지 먼저, 정보는 뒤에 |
| NFC_REGISTER | Hardware | 카드 태그 행동 중심 |
| BADGE_PRINTING | Mechanical | 종이/출력 상태 중심 |
| CHECKIN_COMPLETE | Completion | 다음 장소 안내 중심 |
| CHECKOUT_NFC | Hardware | 카드 태그 중심 |
| CHECKOUT_RESULT | Recall | 오늘 세션 확인 |
| REPORT_PREVIEW | Editorial | 리포트 읽기 경험 |
| REPORT_PRINTING | Mechanical | 출력 상태 |
| CHECKOUT_COMPLETE | Completion | 퇴근 메시지 |

## 5. 화면 간 일관성과 차별화

같게 유지:
- Pretendard
- primary blue
- spacing rhythm
- radius family
- motion easing
- header/step context의 기본 위치
- 상태 색상 의미
- touch target 최소 규칙

다르게 허용:
- 배경 light/dark
- hero composition
- 카드 사용 여부
- CTA shape/placement
- icon scale
- 정보 밀도
- 화면 전환 연출

목표는 "같은 제품의 다른 장면"이지 "같은 템플릿의 문구 교체"가 아니다.

## 6. 구현 우선순위

### P0 — 전시 필수
1. HOME
2. TEAM_SELECT + TEAM_DETAIL modal
3. NAME_INPUT
4. AI_MODE_SELECT + detail A/B
5. CAMERA
6. AI_PROCESSING
7. RESULT A/B
8. NFC_REGISTER
9. BADGE_PRINTING
10. CHECKIN_COMPLETE
11. CHECKOUT_NFC
12. REPORT_PREVIEW/PRINTING
13. CHECKOUT_COMPLETE
14. 오류/유휴 상태

### P1 — 디테일 강화
- hero 3D assets
- selected/pressed microinteraction
- AI result reveal
- NFC detection visual response
- print paper motion
- report editorial treatment

## 7. 구현 원칙

- framework migration 금지
- 현재 vanilla HTML/CSS/JS + FastAPI 유지
- 실제 hardware/API 성공 전에 UI success를 표시하지 않음
- fake progress % 금지
- irreversible operation 중 back/double tap 차단
- reduced motion 지원
- pointer hover는 보조, touch state가 기준
- 모든 화면은 800×1280 원본 기준으로 먼저 검증

## 8. 관련 문서

- [DESIGN_SYSTEM_2026-10-01.md](DESIGN_SYSTEM_2026-10-01.md)
- [ICON_ASSET_SYSTEM_2026-10-01.md](ICON_ASSET_SYSTEM_2026-10-01.md)
- [AI_MODE_B_INTEGRATION_2026-10-01.md](AI_MODE_B_INTEGRATION_2026-10-01.md)
- [USER_FLOW.md](USER_FLOW.md)
- [SCREEN_DEFINITION.md](SCREEN_DEFINITION.md)
- [API_CONTRACT.md](API_CONTRACT.md)
- [DECISIONS.md](DECISIONS.md)

## 9. 완료 기준

리디자인 완료는 "스크린샷이 예쁘다"가 아니라 아래를 모두 만족할 때로 본다.

- 실제 10.1인치 화면에서 읽힘
- touch만으로 전체 happy path 완료 가능
- 오류/대기/성공 상태가 서로 구분됨
- 화면마다 목적에 맞는 시각적 장면이 있음
- NFC/print 중복 요청 방지 규칙 유지
- AI 결과를 과장하거나 가짜 처리 상태를 표시하지 않음
- 홈 복귀 시 이전 사용자의 시각적/상태 데이터가 남지 않음
