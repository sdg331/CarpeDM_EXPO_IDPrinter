# MIRRORTING WORKS — Design Contract

> 역할: **디자인 원칙 Source of Truth**. Figma는 시각적 구현 기준, `SCREEN_DEFINITION.md`는 기능 기준이다.

## 1. Product Character

MIRRORTING WORKS는 다음처럼 느껴져야 한다.
- 미래형 회사의 온보딩/퇴근 터미널
- 전문적이지만 딱딱하지 않음
- 기술적이지만 처음 보는 사람도 이해 가능
- 전시 작품답게 기억에 남지만 과장된 SF/Cyberpunk는 아님
- 하드웨어 대기 중에도 멈춘 것처럼 보이지 않음

피해야 할 인상:
- 관리자용 대시보드
- 모바일 앱을 세로 화면에 단순 확대
- 과도한 네온/글래스모피즘/게임 HUD
- AI가 만든 흔한 gradient card UI
- 정보보다 장식이 앞서는 화면

## 2. Experience Principles

### One Decision at a Time
한 화면에서 관람객이 해야 할 다음 행동이 하나로 보이게 한다.

### Touch First
- 프로젝트 최소 interactive target: **48×48 CSS px**
- 주요 CTA는 가능하면 56px 이상 높이
- Hover-only 정보 금지
- 정밀 drag/scroll 의존 금지

### Standing Distance
관람객은 앉아서 읽지 않는다.
- 제목은 짧고 크게
- 본문은 2~4줄 단위
- 핵심 버튼은 화면 하단/중앙에서 즉시 식별

### State Is Visible
사용자는 항상 시스템이 무엇을 기다리는지 알아야 한다.
- 기다리는 중
- 처리 중
- 성공
- 실패
- 사용자가 고칠 수 있는 상태

### Recover Without Blame
`사용자 오류`, `Object Detection Failed` 대신 다음 행동을 알려준다.
- `한 분만 화면 안에 들어와 주세요.`
- `카드를 다시 한 번 태그해주세요.`

## 3. Platform

- Canvas: 800×1280
- Orientation: portrait
- Primary input: touch
- Text input: physical keyboard on NAME_INPUT only
- Mouse: no UX dependency
- Speaker: none
- Feedback: visual UI + LED

## 4. Foundations

### Color
CONFIRMED:
- 물리 함체는 black/dark 계열
- UI는 높은 명암 대비 필요

브랜드 Accent Color: **TBD until Hi-Fi review**.
Wireframe은 grayscale로 진행한다.

권장 token names:
- `color.bg.canvas`
- `color.bg.surface`
- `color.bg.elevated`
- `color.text.primary`
- `color.text.secondary`
- `color.text.inverse`
- `color.border.default`
- `color.brand.primary`
- `color.status.success`
- `color.status.warning`
- `color.status.error`
- `color.status.info`

### Typography
- Korean-first
- ultra-thin weight 금지
- 영문 ALL CAPS 남용 금지
- 실제 Pi에 설치 가능한 폰트만 사용

CURRENT code prefers Pretendard; target Pi에 Pretendard 또는 Noto CJK 설치 여부를 반드시 검증한다.

2026-09-15 구현 조정 — 10.1인치 화면 가독성:
- 800×1280 원본 기준 본문 28px, 보조 안내 24px, 제목 52px, 홈 제목 68px.
- 주요 버튼 글씨 32px / 높이 104px 이상, 홈 입사·퇴근 선택은 글씨 44px / 높이 220px 이상.
- 긴 AI 설명의 단계 제목은 28px, 설명은 24px. 복구 안내는 26px 이상.
- 작은 영문 장식과 중복 안내를 줄이고 보조 글씨의 명암 대비를 높인다.
- 입사·퇴근 및 A/B 선택은 세로로 넓게 배치한다. 6개 팀은 2열·3행을 유지한다.
- 퇴근 리포트는 28px 본문과 내부 스크롤을 사용하며, 스크롤 안내와 고정 출력 버튼을 제공한다.
- 브라우저 축소 미리보기와 실제 패널의 물리적 가독성은 다르므로, Pi의 폰트·표시 배율과 현장 시청 거리에서 최종 확인한다.

Token model:
- `type.display`
- `type.heading1`
- `type.heading2`
- `type.body-lg`
- `type.body`
- `type.label`
- `type.caption`

### Spacing
8px rhythm을 기본으로 사용.
- 4 / 8 / 12 / 16 / 24 / 32 / 40 / 48 / 64

### Radius
작은 scale만 유지:
- `radius.sm`
- `radius.md`
- `radius.lg`
- `radius.full`

## 5. Layout

모든 P0 화면은 가급적 1 viewport 내에서 완료한다.

권장 영역:
1. Brand / Step context
2. Main title
3. Main content
4. Primary action
5. Back/helper area

피하기:
- 주요 단계에서 긴 세로 스크롤
- 작은 상단 toolbar
- 물리 화면 모서리에 붙는 콘텐츠
- CTA가 키보드/하드웨어 영역과 시각적으로 충돌하는 배치

## 6. Components

필수 families:
- Button
- TeamCard
- AIModeCard
- TextInput
- StepHeader
- BackButton
- StatusPanel
- LoadingIndicator
- CameraGuide
- NFCInstruction
- ResultCard
- ErrorPanel
- Modal (limited)

각 interactive component는 최소 다음 상태를 고려:
- default
- pressed
- disabled
- loading (applicable)
- selected (applicable)
- error (applicable)

## 7. Button Rules

- 화면마다 primary CTA는 원칙적으로 1개.
- Back/secondary는 primary보다 시각적 우선순위가 낮아야 함.
- destructive reset은 danger 스타일 사용.
- 색상만으로 disabled/error를 표현하지 않음.

## 8. Team Card

기본 화면은 2×3 grid.

카드 첫 화면:
- 팀명
- 팀 icon/visual

선택 후 상세:
- 팀명
- 1~2문장 소개
- 주요 업무 3개
- 키워드 3개
- `다른 팀 보기`
- `이 팀으로 입사하기`

팀마다 완전히 다른 디자인을 쓰지 않는다. 하나의 시스템 안에서 icon/작은 accent만 다르게 한다.

## 9. AI Mode Card

A/B는 동일한 시각적 무게를 가진다.

### A — AI 캐릭터 매칭
- 요약: 얼굴 특징을 분석해 8명의 캐릭터 중 가장 가까운 캐릭터를 찾음
- 상세 HOW IT WORKS는 5단계

### B — AI 프로필 생성
- 요약: 얼굴을 유지하면서 사원증용 포멀 프로필을 생성
- 외부 생성 AI/API Key 사용 없음

## 10. Camera UI

- 고정 네모에 사람을 억지로 맞추는 UX 금지
- 실제 감지 결과를 바탕으로 guide/status를 동적으로 표현
- 다중 인원/사람 없음/촬영 준비/촬영 중 상태가 분명해야 함
- 카메라 프리뷰 위 텍스트는 대비 확보
- 촬영 버튼은 `ready`일 때만 활성화

## 11. Hardware State UX

NFC/Printer/AI는 다음 구조를 공유:
1. What is happening
2. What should user do
3. Retry or next action

가짜 진행률 금지. 백엔드가 real progress를 제공할 때만 numeric progress 사용.

## 12. Motion

Motion은 상태 설명용.
- 일반 transition: 150–300ms 권장
- 장기 처리: purposeful loop
- 과한 bounce/confetti 금지
- motion 때문에 다음 단계가 지연되면 안 됨
- reduced motion 고려 가능

## 13. Voice & Tone

한국어 우선. 짧고 행동 지향적으로 쓴다.

Good:
- `사원증 카드를 태그해주세요.`
- `한 분만 화면 안에 들어와 주세요.`
- `출력 중이에요. 잠시만 기다려주세요.`

Bad:
- `NFC WRITE ERROR`
- `Object Detection Failed`
- `Submit`

Error copy formula:
> 무엇이 일어났는지 + 다음에 무엇을 하면 되는지

## 14. Accessibility

- 48×48 project minimum touch target
- 의미를 색상 하나에만 의존하지 않음
- 중요한 icon-only action 최소화
- 텍스트 contrast 검수
- focus가 필요한 NAME_INPUT에서는 visible focus 제공
- 한국어 IME composition이 깨지지 않게 구현

## 15. Figma Governance

- Figma variables와 이 파일의 token names를 동기화한다.
- Figma screen name은 `SCR-XX__SCREEN_NAME__state` 형식.
- 새로운 recurring UI pattern이 생기면 먼저 component로 일반화할지 검토.
- Figma와 DESIGN.md가 충돌하면 어느 쪽이 최신인지 확인하고 둘 다 동기화한다.
