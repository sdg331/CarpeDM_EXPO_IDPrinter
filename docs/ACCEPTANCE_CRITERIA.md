# Acceptance Criteria

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
- [ ] random fallback removed
- [ ] duplicate processing prevented
- [ ] A success → SCR-10
- [ ] B success → SCR-11
- [ ] timeout/error path defined

## SCR-10 RESULT A
- [ ] result belongs to current session
- [ ] wording does not misrepresent score as probability
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
