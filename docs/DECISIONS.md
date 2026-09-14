# Decisions

이 문서는 다시 실수로 논의/변경하지 않도록 확정사항을 기록한다.

## D-001 Company
Status: CONFIRMED

Decision: 가상 회사명은 **MIRRORTING WORKS**.
MirrorTing은 스마트미러 시스템/작품명으로 사용.

## D-002 Teams
Status: CONFIRMED

Decision:
- 개발팀
- AI팀
- 디자인팀
- 기획팀
- 마케팅팀
- 인사팀

## D-003 Check-in Flow
Status: CONFIRMED

`입사 → 팀 → 이름 → AI A/B → 촬영 → AI → 결과 → NFC → 사원증 출력 → MirrorTing 안내`

## D-004 Check-out
Status: CONFIRMED

HOME에 퇴근하기를 제공하고, NFC로 session을 식별해 MirrorTing 결과를 조회하고 퇴근 리포트를 출력한다.

## D-005 AI Mode A
Status: CONFIRMED direction

Deep learning character matching using current YuNet/SFace baseline.
Target pipeline includes person detection/face tracking/quality checks when Pi performance allows.

## D-006 AI Mode B
Status: CONFIRMED

No external generative image API.
Local computer vision + transparent formal-suit PNG + OpenCV composite.

## D-007 AI Selection Timing
Status: CONFIRMED

A/B is selected **before** photo capture.

## D-008 AI Selection UX
Status: CONFIRMED

Two large cards → selected mode detail/HOW IT WORKS → start.
Same interaction pattern as TeamCard → TeamDetail.

## D-009 Input
Status: CONFIRMED

Touch-first. Physical compact 2.4GHz keyboard only for name input. Mouse not required.
Final keyboard model: TBD.

## D-010 Audio
Status: CONFIRMED

No speaker. Use screen animation + LED feedback.

## D-011 Front Hardware Layout
Status: CONFIRMED concept / dimensions deferred

- top camera
- center portrait display
- four-sided LED around display
- printer lower-left
- NFC lower-right
- keyboard tray bottom
- black enclosure

## D-012 LED
Status: CONFIRMED hardware

USB 5V COB, width 8mm, 6W/m, 320LED/m. Separate safe power plan; do not power blindly from Pi USB for long strip.

## D-013 Current Framework
Status: CONFIRMED for EXPO sprint

Keep current vanilla HTML/CSS/JS + FastAPI. No framework migration during feature sprint.

## D-014 Random Fallback
Status: CONFIRMED

Production random character fallback must be removed.

## D-015 Camera Architecture
Status: CURRENT + provisional target

Current browser getUserMedia preview/capture is allowed to remain if stable on Raspberry Pi. AI inference remains backend.

## D-016 NFC Data
Status: CONFIRMED principle / payload TBD

Store minimal card identity/session data. Detailed profile/experience data is backend/local DB responsibility.

## D-017 Privacy
Status: CONFIRMED direction

Do not persist original captured face image unnecessarily. Current `/api/match` memory-only behavior should be preserved.

## D-018 Idle
Status: PROJECT DEFAULT

Move toward 60sec inactivity reset with warning. Final timing may be tuned after real exhibition test.

## D-019 Figma
Status: CONFIRMED process

Docs/User Flow/Screen Definition first → Figma wireframe → UX review → DESIGN/tokens → Hi-Fi/prototype.

## D-020 AI Agent
Status: CONFIRMED

Use `AGENTS.md` + docs as system of record. No Claude/Cursor-specific config required.
