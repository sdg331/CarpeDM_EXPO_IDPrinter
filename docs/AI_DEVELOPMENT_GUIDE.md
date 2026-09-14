# AI Development Guide

## Goal

AI 에이전트를 **결정자**가 아니라 **명세 구현·검증 동료**로 사용한다.

## AI에게 바로 맡겨도 좋은 작업

- existing screen 분석
- CSS/레이아웃 구현
- 반복 컴포넌트 정리
- mock scenario 작성
- test 초안
- Git 설명
- PR 요약
- 문서 동기화 후보 찾기
- Figma vs screenshot 차이 분석

## 반드시 사람 검토가 필요한 작업

- navigation/state architecture
- API integration
- timeout/retry semantics
- camera behavior
- NFC/print interaction
- privacy/retention

## 승인 없이 변경 금지

- user flow
- team names/content
- AI A/B meaning
- AI algorithm contract
- DB/session identity model
- NFC payload
- hardware protocol
- printer behavior
- source-of-truth docs

## Standard Agent Loop

```text
Inspect
→ Read relevant specs
→ Plan smallest change
→ Implement
→ Run tests
→ Verify acceptance criteria
→ Report
```

## Good Request Structure

Always include:
- Screen ID/feature
- source docs
- exact scope
- forbidden changes
- verification

## Anti-Patterns

Do not ask:
`예쁘게 알아서 만들어줘.`

Prefer:
`SCR-02를 SCREEN_DEFINITION + DESIGN + ACCEPTANCE_CRITERIA에 맞춰 구현해. 다른 화면/API는 변경하지 마.`

## Hallucination Guard

If value is not confirmed:
- use TBD
- ask/flag it
- do not invent permanent token/API field/team content

## Hardware Truth

AI agent may simulate deterministic mock states, but production code must not convert hardware failure into fake success.

## Refactoring

Before refactor:
- state current behavior
- identify public interface
- find tests
- preserve flow/API

Separate structural cleanup from feature PR where possible.

## AI-Generated Code Review

Before accepting:
- does it match current stack?
- did it add dependencies unnecessarily?
- did it bypass FastAPI/hardware boundary?
- did it invent API shape?
- are error/retry states present?
- are tests meaningful?
