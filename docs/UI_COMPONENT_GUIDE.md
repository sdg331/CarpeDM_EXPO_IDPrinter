# UI Component Guide

## Component Naming

Figma:
- `CMP/Button`
- `CMP/TeamCard`
- `CMP/AIModeCard`
- `CMP/TextInput`
- `CMP/StepHeader`
- `CMP/StatusPanel`
- `CMP/CameraGuide`
- `CMP/NFCInstruction`
- `CMP/ResultCard`
- `CMP/ErrorPanel`

Code names may be equivalent even in vanilla JS/CSS. Reuse classes/templates rather than screen-specific duplicates.

## Button

Properties:
- intent: primary | secondary | danger
- state: default | pressed | disabled | loading
- size: medium | large

Rules:
- min touch area 48×48
- primary CTA should be visually dominant
- disabled must be visible beyond color alone

## TeamCard

Props/data:
- id
- title
- icon
- summary: 선택 화면용 짧은 소개. 확정된 상세 설명을 대체하지 않는다.
- selected
- disabled

States:
- default
- pressed
- selected
- disabled

Grid target: 2×3.

현재 선택 카드는 팀 이름·작은 단색 아이콘·짧은 소개·`소개 보기`로 구성한다. 카드 전체를 누르면 상세로 이동하며, 이름과 동작을 접근 가능한 버튼 이름으로 제공한다. 소개는 24px, 팀 이름은 36px이며 얇은 테두리와 14px 모서리를 사용한다. 문장이 두 줄로 나뉠 때는 줄 길이를 균형 있게 맞춘다.

## TeamDetailCard

Contents:
- icon
- team title
- description
- 3 responsibilities
- 3 readable keyword tags
- secondary + primary actions

현재 상세는 팀 선택 위의 공통 중앙 팝업이다. 상단의 투명 아이콘·영문명·48px 팀명 아래에 26px 원문 설명을 전체 폭으로 놓는다. 주요 업무 세 개는 26px 글씨의 개별 중립 카드이며, 키워드는 26px 글씨의 연한 파란 태그다. 구역 제목은 24px이다. 하단에서는 104px 높이의 전체 폭 입사 버튼을 먼저 강조하고, 64px 보조 행동은 배경 없이 표시한다. 작은 웹 화면에서는 업무를 한 세로 목록으로 묶고 업무·키워드 글씨 20px, 입사 버튼 높이 72px를 사용한다. 아이콘 뒤 별도 배경은 사용하지 않는다.

## AIModeCard

Props:
- mode A/B
- title
- summary
- illustration/icon
- selected

A and B use same structure/size.

## AIModeDetail

Contents:
- title
- short description
- HOW IT WORKS 5 steps
- back/change
- start CTA

## TextInput

Used on NAME_INPUT.

States:
- default
- focused
- filled
- error
- disabled

Requirements:
- Korean IME
- obvious focus
- 1–10 char validation
- physical keyboard hint

## StepHeader

Contents:
- optional back
- current step title
- optional progress rail

Do not show Back when unsafe during hardware side-effect.

## CameraGuide

Contents:
- preview
- dynamic guide/bounding indication
- instruction
- capture CTA

It does not own YuNet/SFace logic.

## StatusPanel

Generic waiting/working/success/error panel.

Use for NFC/printer/backend states.

## LoadingIndicator

- indeterminate by default
- real progress only if backend reports truthful progress

## NFCInstruction

States:
- waiting
- detected
- writing
- verifying
- success
- error

Animation should communicate where to tap, not decorate.

## ResultCard

A/B share structural rhythm.
Mode content can differ without duplicating entire layout.

## ErrorPanel

Must answer:
1. what happened
2. what to do next

Never show raw internal errors.

## Modal

Use sparingly.
Good:
- idle warning
- destructive reset confirmation

Bad:
- every normal navigation step

## Design Drift Rule

Before creating new component/style:
1. search Figma components
2. search current CSS/JS patterns
3. check DESIGN.md
4. create only if semantics genuinely differ
