# Frontend QA Checklist

## Visual
- [ ] 800×1280
- [ ] no horizontal overflow
- [ ] main CTA not clipped
- [ ] consistent spacing/tokens
- [ ] status text readable over camera/result visuals
- [ ] no accidental tiny icon-only critical action

## Touch
- [ ] primary targets comfortably ≥48×48
- [ ] no hover dependency
- [ ] no precision drag
- [ ] rapid double tap handled

## Keyboard
- [ ] name input only
- [ ] Korean IME
- [ ] visible focus
- [ ] keyboard reconnect after reboot

## Check-in Flow
- [ ] HOME
- [ ] 6 teams
- [ ] team detail
- [ ] name
- [ ] A/B select
- [ ] A detail
- [ ] B detail
- [ ] camera
- [ ] AI processing
- [ ] result
- [ ] NFC
- [ ] badge print
- [ ] complete

## Check-out Flow
- [ ] HOME → checkout
- [ ] NFC resolve
- [ ] MirrorTing result
- [ ] report preview
- [ ] report print
- [ ] complete

## Failure
- [ ] camera unavailable
- [ ] no person
- [ ] multiple people
- [ ] AI error/timeout
- [ ] backend offline
- [ ] NFC timeout/write failure
- [ ] printer error
- [ ] unknown checkout card
- [ ] MirrorTing result missing

## Data Isolation
- [ ] previous name cleared
- [ ] previous team cleared
- [ ] previous AI image/result cleared
- [ ] previous NFC/print state cleared
- [ ] stale async response ignored

## Forbidden
- [ ] no random production AI result
- [ ] no fake NFC success
- [ ] no fake print success
- [ ] no raw stack trace
- [ ] no cloud Mode B upload unless explicitly approved

## 사진 전용 경로
- [ ] HOME 세 번째 진입 및 카드 확인
- [ ] 일반 카드 오류·전용 카드 촬영
- [ ] 이름·팀 없이 사진과 소개 QR 확인
- [ ] 취소·재촬영·출력 실패/상태 조회
- [ ] 완료/HOME에서 사진·촬영 권한 초기화
- [ ] 리포트 직각 테두리·번호 섹션·스크롤·출력 CTA

## 사진 포함 체험 리포트·센터 팁

- [ ] 확인한 사진이 리포트에 포함되고 사진 없이 진행 가능
- [ ] 센터명·팁 한 가지·첨삭 요약 표기가 분석과 구분됨
- [ ] 안전 재시도에서는 Blob/팁/작업 ID 유지, 완료·초기화에서는 사진 해제
- [ ] 첫 화면의 얼굴·리포트 내부 스크롤·800×1280 하단 출력 CTA 확인

[소프트웨어 검증](qa/REPORT_PHOTO_TIPS_2026-10-12.md), 실제 Pi 터치/인쇄는 별도 인수.
