# Acceptance Criteria

2026-10-16 MediaPipe 추천: 실제 입사 API가478점에서 계산한9개 비율을 사용하고, 결과ID·추천 조건·근거가 같은 얼굴에 속해야 한다. 상세 실패는 명시적 오류이며 SFace/무작위 결과로 바꾸지 않는다. 결과의 비율 펼치기·접기, 직접 선택 시 근거 숨김, 메모리 초기화, NFC 요청에서 측정값 제외를 확인한다. 키오스크 결과가 길면 화면 내부 세로 스크롤로 푸터·버튼 겹침 없이 모든 항목에 접근한다.

## Global

Every screen passes when:
- correct at 800×1280
- no horizontal overflow
- touch usable
- no required hover/mouse
- copy matches approved content
- back behavior is safe
- loading/error/retry exists where needed
- previous visitor state cannot leak

## SCR-01 HOME
- [ ] 입사/퇴근 clearly visible
- [ ] check-in → SCR-02
- [ ] check-out → SCR-15
- [ ] no previous session data visible

## SCR-02 TEAM_SELECT
- [ ] exactly 6 confirmed teams
- [ ] 2×3 layout
- [ ] fits without unintended scroll
- [ ] card touch → matching detail

## SCR-03 TEAM_DETAIL
- [ ] correct team description
- [ ] 3 responsibilities
- [ ] 3 keywords
- [ ] change team returns safely
- [ ] confirm → NAME_INPUT

## SCR-04 NAME_INPUT
- [ ] physical keyboard input works
- [ ] Korean IME works on Raspberry Pi
- [ ] empty cannot continue
- [ ] focus visible
- [ ] 1–10 char policy enforced consistently

## SCR-05 AI_MODE_SELECT
- [ ] A/B equal structural weight
- [ ] no silent preselection
- [ ] A/B route to correct details

## SCR-06/07 AI_MODE_DETAIL
- [ ] correct 5-step explanation
- [ ] no unsupported technical claim
- [ ] start → CAMERA

## SCR-08 CAMERA
- [ ] preview works on target camera
- [ ] no-person state
- [ ] multiple-person state
- [ ] ready state
- [ ] capture double-submit blocked
- [ ] successful capture transitions once
- [ ] failure is recoverable when possible

## SCR-09 AI_PROCESSING
- [ ] no fake percentage
- [ ] left four eligible previews cycle, right photo shows all actual478 points; previews are not ranking and reduced motion freezes the first
- [ ] valid AI response transitions immediately without minimum display or landmark hold; no duplicate inference or animation timer
- [ ] random fallback removed
- [ ] duplicate processing prevented
- [ ] A success → SCR-10
- [ ] B success → SCR-11
- [ ] timeout/error path defined

## SCR-10 RESULT A
- [ ] result belongs to current session
- [ ] wording does not misrepresent score as probability
- [ ] eight-character picker preserves name/team and updates the issued character
- [ ] manual choice is labelled and cancel keeps current result
- [ ] busy/error/registered sessions cannot change characters; reset clears choice
- [ ] continue → NFC

## SCR-11 RESULT B
- [ ] output belongs to current session
- [ ] no external cloud generation dependency
- [ ] continue → NFC

## SCR-12 NFC_REGISTER
- [ ] waiting/writing/verifying/success/error states
- [ ] success only after backend confirms
- [ ] duplicate write blocked
- [ ] retryable error preserves session

## SCR-13 BADGE_PRINTING
- [ ] one logical print intent
- [ ] visible progress
- [ ] retryable failure preserves badge/session
- [ ] success → CHECKIN_COMPLETE

## SCR-14 CHECKIN_COMPLETE
- [ ] clear completion
- [ ] MirrorTing next-step guidance
- [ ] auto reset clears visitor data

## SCR-15 CHECKOUT_NFC
- [ ] waiting/resolve/unknown/error states
- [ ] duplicate resolve blocked
- [ ] current card resolves current session only

## SCR-16 CHECKOUT_RESULT
- [ ] current visitor identity only
- [ ] no fabricated MirrorTing data
- [ ] missing data has clear retry path

## SCR-17 REPORT_PREVIEW
- [ ] report matches current resolved session
- [ ] print action clear
- [ ] no duplicate submit

## SCR-18 REPORT_PRINTING
- [ ] separate report print job behavior
- [ ] recoverable failure preserves report
- [ ] success → CHECKOUT_COMPLETE

## SCR-19 CHECKOUT_COMPLETE
- [ ] clear completion
- [ ] auto reset clears visitor state

## Release Blockers

Release blocked if:
- [ ] random AI fallback remains
- [ ] old visitor data appears in new session
- [ ] Korean keyboard input fails on Pi
- [ ] NFC failure loses entire session
- [ ] printer retry can create uncontrolled duplicates
- [ ] UI requires mouse/hover
- [ ] camera disconnected has no UX
- [ ] Mode B sends user photo to unapproved external service
- [ ] current backend tests regress

## 전용 카드 사진·리포트 · 2026-10-12

추가 소프트웨어 확인: 퇴근 동반 사진 전체 프레임 인쇄·사진 없이 출력, 첨삭 팁 1개/동일 세션 유지, JSON/사진 출력 간 중복 방지, 잘못된 사진은 장치 접근 전 차단. 실물 얼굴 명암·가독성·용지 배출·절단은 현장 확인 대상이다. [사진 포함 리포트](REPORT_PHOTO_TIPS.md).

- [ ] 전용 카드/일반 카드 분기와 입사 등록 차단
- [ ] 촬영/재촬영/취소, 이전 사진·이름 누출 없음
- [ ] 사진·QR 감열 인화 및 휴대폰의 실제 소개 주소 스캔
- [ ] 결과 불명/재시작/동시 요청에서 중복 인화 차단 및 운영자 복구
- [ ] 브루탈리즘 리포트 내부 스크롤·출력 CTA·출처/미측정 유지

소프트웨어 증거는 [사진/리포트 QA](qa/SOUVENIR_REPORT_2026-10-12.md), 현장 설정은 [운영](SOUVENIR.md). 위 실물 항목은 자동 테스트 통과로 완료 처리하지 않는다.

## 2026-10-14 exhibition face selection update

SCR-08 multi-person is ready when a face is selected; SCR-09 uses actual coordinates on the selected person and hides missing data. Validate primary-face agreement across detect/match/face-map/comparison, feature toggle while busy, mirrored contain positioning, and late-response cleanup. Booth/Pi acceptance remains separate.

## 응원 인화·일괄 복구 추가 기준 · 2026-10-16

- [ ] 사진 → 요청한 응원 문구 → 여백 → 굵은 사각 CarpeDM 도장, 기존 QR 가독성
- [ ] 출력 오류 화면에서 작업 선택 후 일괄 출력, 이미 출력됨 처리
- [ ] 연속 클릭/같은 배치 재요청/실행 중/기존 성공 건의 중복 출력 차단
- [ ] 장치 실패 시 남은 건 유지, 재시작 후 같은 감열 이미지 복구
- [ ] 이미지 없는 과거 작업은 재촬영 안내, 성공으로 표시하지 않음
- [ ] 800×1280 터치 및 키보드 초점 확인, 실물 용지·절단 별도 확인
