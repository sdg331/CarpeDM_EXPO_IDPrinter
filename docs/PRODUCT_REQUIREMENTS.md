# Product Requirements

## Objective

관람객이 직원 도움 없이 MIRRORTING WORKS 입사/퇴근 경험을 완료하고, AI·NFC·감열 출력이 하나의 이야기로 연결되는 안정적인 전시 키오스크를 만든다.

## Priority

- **P0**: 전시에 반드시 필요
- **P1**: 완성도/운영성 개선
- **P2**: 일정 여유 시

## P0 Functional Requirements

### HOME
- `입사하기`
- `퇴근하기`

### Check-in
- 6개 팀 선택
- 선택 팀 상세 확인
- 물리 키보드 이름 입력
- AI A/B 선택
- 선택 AI 방식의 HOW IT WORKS 확인
- 사진 촬영
- AI 처리 상태 확인
- 결과 확인
- NFC 카드 등록
- 사원증 출력
- MirrorTing 이동 안내

### Mode A
- 사람/대상 존재 판단 (target)
- 얼굴 검출
- 얼굴 추적/품질 판단 (target)
- 얼굴 정렬
- SFace 128D 특징 추출
- 8종 캐릭터 비교
- 최종 매칭
- 실패 시 랜덤 결과 금지

### Mode B
외부 생성 AI/API 없이 local processing:
- 사람/얼굴 탐지
- pose/landmark
- person segmentation
- face preserve
- transparent formal-suit PNG overlay
- background/layout cleanup
- quality check

### NFC
- session ↔ NFC association
- write/read result visible
- retryable errors preserve session
- duplicate write protection

### Badge print
- current session only
- double-print protection
- retry/operator recovery on failure

### Check-out
- NFC tag
- resolve session
- retrieve MirrorTing result
- report preview
- thermal report print
- reset

## P0 Non-Functional Requirements

- 800×1280 portrait
- touch-first
- no hover/mouse dependency
- Korean-first copy
- public exhibition readability
- physical keyboard only for name
- no random production fallback
- repeatable state reset
- retryable hardware failure must not erase session
- current FastAPI/YuNet/SFace baseline remains operational
- real Raspberry Pi validation required

## P1

- LED state synchronization if hardware control is added
- operator health/debug view
- visual regression screenshot checks
- anonymous session metrics (duration/error count) if approved
- reduced-motion support

## Out of Scope Without Approval

- speaker/voice guidance
- mouse UX
- cloud image generation API for Mode B
- browser direct NFC/ESC-POS driver
- changing physical enclosure from frontend task
- React/Vite migration during exhibition sprint
- automatic face-based personality/job suitability inference

## Release Success Definition

Release requires:
- all P0 screen acceptance criteria pass
- current backend tests remain green
- real camera / NFC / printer integrated
- Korean name input validated on Pi
- at least repeated end-to-end sessions without manual reboot
- previous user data isolation verified
- production has no random/fake success path
