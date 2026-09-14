# AI Prompt Playbook

복사해서 `[ ]`만 채워 사용한다.

## 1. Screen Implementation

```text
AGENTS.md 지침을 따라 작업해.

Task:
[SCR-XX SCREEN_NAME]을 구현해.

반드시 읽을 문서:
- DESIGN.md
- docs/SCREEN_DEFINITION.md
- docs/UI_STATE_SPEC.md
- docs/ACCEPTANCE_CRITERIA.md

Constraints:
- 800x1280 portrait
- touch-first
- 현재 vanilla HTML/CSS/JS 스택 유지
- user flow/API contract 임의 변경 금지
- unrelated refactor 금지

작업 전:
1. 현재 관련 코드를 조사해.
2. 변경할 파일을 알려줘.
3. CURRENT와 TARGET의 차이를 정리해.

작업 후:
1. 테스트/검증을 실행해.
2. Acceptance Criteria를 체크해.
3. 변경 파일과 남은 리스크를 알려줘.
```

## 2. Figma → Code

```text
[SCR-XX] Figma와 SCREEN_DEFINITION.md를 기준으로 현재 구현을 맞춰줘.
DESIGN.md의 token/component 원칙을 우선해.
픽셀 복사보다 기존 CSS 시스템과 재사용성을 유지해.
800x1280에서 검증하고 차이를 요약해.
```

## 3. UI Review

```text
이 화면을 시니어 전시 키오스크 UX 디자이너 관점에서 리뷰해.
기준:
- DESIGN.md
- SCREEN_DEFINITION.md
- 800x1280
- touch-first
- 48px touch target
- 정보 위계
- 한국어 가독성
- 전시장 거리/조명
- 상태 명확성
- generic AI UI pattern
- 접근성

Critical / Major / Minor로 분류해.
취향만으로 수정 요구하지 마.
```

## 4. Bug Fix

```text
AGENTS.md를 따라 버그를 수정해.

Bug: [현상]
Expected: [정상]
Screen: [SCR-XX]
Reproduce:
1. ...
2. ...

먼저 root cause를 찾고 설명해.
증상만 숨기는 workaround, unrelated refactor 금지.
수정 후 regression risk와 test를 제시해.
```

## 5. Current API Integration

```text
docs/API_CONTRACT.md에서 CURRENT로 표시된 API만 사용해 [기능]을 연결해.
contract에 없는 필드를 invent하지 마.
loading/success/error/retry 상태를 구현해.
random/fake fallback 금지.
```

## 6. Proposed API Mock

```text
API_CONTRACT.md의 PROPOSED [기능]에 대해 deterministic mock을 만들어.
scenario:
- success
- slow success
- timeout
- retryable error
- fatal error

실제 계약과 동일한 domain shape를 쓰고 UI 코드에 mock 전용 분기를 퍼뜨리지 마.
```

## 7. Hardware State Review

```text
docs/UI_STATE_SPEC.md와 ERROR_HANDLING.md를 기준으로 [Camera/NFC/Printer/AI]의 누락 상태를 찾아줘.
반드시 검토:
- idle/initializing
- waiting/processing
- success
- timeout
- disconnected
- retryable error
- fatal error
- double tap
- stale response

코드 수정 전에 누락 목록부터 작성해.
```

## 8. Test Generation

```text
[SCR-XX] Acceptance Criteria를 읽고 테스트 케이스를 작성해.
정상뿐 아니라:
- rapid double tap
- timeout
- backend failure
- malformed response
- hardware disconnected
- retry
- stale response
- session reset
을 포함해.
```

## 9. Production Code Review

```text
이번 변경을 production PR처럼 리뷰해.
검토:
- requirement 누락
- API contract 위반
- random/fake fallback
- duplicate request
- stale async response
- session leakage
- error recovery
- accessibility
- 800x1280
- maintainability
- tests
Critical/Major/Minor로 분류해.
```

## 10. Git Help

```text
내 작업을 잃지 않는 방향으로 Git 상태를 설명해줘.

목적: [목적]

git status:
[paste]

git diff:
[paste]

git log --oneline -5:
[paste]

명령을 한 단계씩 알려줘.
reset --hard / clean -fd / push --force 같은 파괴적 명령은 사용하지 마.
```

## 11. Commit / PR

```text
현재 diff를 보고:
1. 가장 적절한 commit message 3개
2. PR title
3. PR body(What changed / Screen / Verification / Risk)
를 작성해.
실제로 하지 않은 테스트는 했다고 쓰지 마.
```

## 12. Screenshot QA

```text
Figma와 Raspberry Pi 800x1280 구현 스크린샷을 비교해.
검사:
- layout
- spacing
- alignment
- typography
- component state
- copy
- overflow
- touch target
- visual hierarchy

1. 반드시 수정
2. 허용 가능
3. Figma 문서가 수정되어야 함
으로 구분해.
```

## 13. Documentation Sync

```text
이번 코드 변경으로 stale해진 문서를 찾아줘.
검사:
- USER_FLOW
- SCREEN_DEFINITION
- UI_STATE_SPEC
- API_CONTRACT
- ACCEPTANCE_CRITERIA
- DECISIONS
- DESIGN.md
필요한 것만 최소 수정 제안해.
```
