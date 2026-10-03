# Decisions

이 문서는 다시 실수로 논의/변경하지 않도록 확정사항과 현재 우선 방향을 기록한다.

하드웨어/함체 상세 이력은 [HARDWARE_ENCLOSURE_2026-09-30.md](HARDWARE_ENCLOSURE_2026-09-30.md)를 우선한다.

## D-001 Company
Status: CONFIRMED

Decision:
- 작품 전체: **4-Fit MirrorTing**
- 가상 회사명: **MIRRORTING WORKS**
- MirrorTing은 스마트미러 시스템명으로 사용

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

입사 → 팀 → 이름 → AI A/B → 촬영 → AI → 결과 → NFC → 사원증 출력 → MirrorTing 안내

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
Status: CURRENT

Touch-first.
**전면 고정 키보드와 키보드 트레이는 사용하지 않는다.**
이름 입력에 물리 키보드가 꼭 필요할 경우 서비스용/임시 입력 장치로 처리하며, 전면 설계에는 포함하지 않는다.

## D-010 Audio
Status: CONFIRMED

No speaker. Use screen animation + LED feedback.

## D-011 Front Hardware Layout
Status: CURRENT DIRECTION

- top center: Camera Module 3
- center: portrait 10.1" display
- upper/display area: COB LED + diffuser
- printer body hidden; output slot only
- NFC: right-side placement preferred, may be visible/slightly protruding
- no front keyboard tray
- black enclosure

Exact dimensions are validated by physical fit, not by conversation-only estimates.

## D-012 LED
Status: CONFIRMED hardware / layout TBD

5V COB LED + ON/OFF controller.
Use diffuser/translucent material so LED dots are not directly visible.
Do not blindly power a long strip from Pi USB.
Exact length and segmentation are decided after brightness/heat/cable tests.

## D-013 Current Framework
Status: CONFIRMED for EXPO sprint

Keep current vanilla HTML/CSS/JS + FastAPI.
No framework migration during feature sprint.

## D-014 Random Fallback
Status: CONFIRMED

Production random character fallback must be removed.

## D-015 Camera Architecture
Status: CURRENT + provisional target

Current browser getUserMedia preview/capture is allowed to remain if stable on Raspberry Pi.
AI inference remains backend-owned.

## D-016 NFC Data
Status: CONFIRMED principle / payload TBD

Store minimal card identity/session data.
Detailed profile/experience data is backend/local DB responsibility.

## D-017 Privacy
Status: CONFIRMED direction

Do not persist original captured face image unnecessarily.
Current /api/match memory-only behavior should be preserved.

## D-018 Idle
Status: PROJECT DEFAULT

Move toward 60 sec inactivity reset with warning.
Final timing may be tuned after real exhibition test.

## D-019 Figma
Status: CONFIRMED process

Docs/User Flow/Screen Definition first → Figma wireframe → UX review → DESIGN/tokens → Hi-Fi/prototype.

## D-020 AI Agent
Status: CONFIRMED

Use AGENTS.md + docs as system of record.
No Claude/Cursor-specific config required.

## D-021 Enclosure Size and Manufacturing
Status: CURRENT DIRECTION

Approximate target:
- 300(W) × 150(D) × 520(H) mm
- portrait
- matte black
- 3D printed
- Bambu Lab A1, 256 × 256 × 256 mm build volume

The enclosure is split into modules.
Previous SPCC metal enclosure proposals are superseded.

## D-022 Printer Visibility
Status: CONFIRMED

ZTP-80USL2 body should be hidden from the visitor.
Only the paper output area should be visually exposed on the front.

## D-023 Printer Power
Status: CONFIRMED

ZTP-80USL2 uses a dedicated 12V 5A adapter.
Do **not** power the printer from Raspberry Pi 5.

## D-024 Printer Data
Status: CURRENT DIRECTION

Primary: USB.
Fallback: RS232.

Do not keep USB and RS232 connected simultaneously without a specific diagnostic reason.
Validate one communication path at a time.

## D-025 Printer Service / Paper Replacement
Status: CURRENT DIRECTION

Use a removable **basket/cradle** structure so the printer can be lifted/withdrawn for paper replacement and service.

Explicitly rejected:
- hidden hinge + push latch as the main paper-service mechanism

Exact retention hardware remains TBD after real-printer fit.

## D-026 Printer USB Harness
Status: ISSUE / REQUIRED

Printer board USB pin discussion:
- GND
- D+
- D-
- VUSB

A correct PH2.0-family 4-pin harness / USB data lead must be identified.
As of 2026-09-30, the current USB connection is broken and previous cable purchases did not fit.
Further blind soldering is not the preferred repair path.

## D-027 NFC Physical Placement
Status: CURRENT DIRECTION

Use ACR1252U.
Right-side placement is preferred.
The NFC target may be intentionally visible or slightly protruding so the interaction is obvious.
Cable routing remains hidden.

The older “must be fully embedded behind a thin front window” concept is no longer mandatory.

## D-028 NFC Card Operations
Status: CONFIRMED

NFC cards are exhibition assets.
They are **reused**, not given to visitors.
Session reset/reissue must prevent a previous visitor's data from remaining associated with the card.

## D-029 USB Hub
Status: CURRENT DIRECTION

Powered USB hub is optional.
Prefer direct Pi connections for touch/NFC/printer first.
Add a powered hub only if port count, cable management or power stability requires it.

## D-030 Print Order
Status: CONFIRMED for current build

First print/validate:
1. display bezel/frame
2. display cable clearance
3. camera/LED upper structure
4. NFC structure
5. printer basket/cradle after real measurement
6. internal power/cable brackets
7. service/back structure

Do not print the full enclosure before fit tests.

## D-031 Display Orientation and Cable Clearance
Status: CONFIRMED

Display is portrait.
The enclosure must preserve HDMI/touch USB connector clearance and cable bend radius behind the display.

## D-032 Printer Can Be Temporarily Deferred
Status: CONFIRMED

The broken printer USB connection does not block:
- display frame
- Pi/display/touch
- camera
- UI
- NFC software
- LED structure
- cable-routing work

Final exhibition approval still requires real ZTP-80USL2 output/cutter/error validation.

## D-033 Hardware/Browser Responsibility
Status: CONFIRMED

NFC and printer are backend-owned.
Do not control them directly from browser code.
Do not display success before backend-confirmed NFC/print success.
Protect irreversible actions against duplicate taps.


## D-034 Frontend Redesign Scope
Status: CONFIRMED — 2026-10-01

Decision:
- 기존 SCR-01~SCR-20 및 SCR-90의 기능 흐름을 유지한다.
- 이번 리디자인은 카피, 화면 연출, icon, motion, state 표현을 중심으로 진행한다.
- NFC/print/API/idempotency 흐름을 시각 리디자인 때문에 변경하지 않는다.

## D-035 Check-in / Team Copy
Status: CONFIRMED — 2026-10-01

HOME:
- `입사하신 것을 진심으로 축하드립니다.`
- `오늘의 직장 생활을 시작해볼까요?`
- actions: `출근하기`, `퇴근하기`

TEAM_SELECT:
- `어느 팀의 합격 문자를 받으셨나요?`

## D-036 Team Detail Presentation
Status: CONFIRMED — 2026-10-01

- SCR-03 logical state는 유지한다.
- 사용자에게는 SCR-02 위에 뜨는 중앙 modal로 표현한다.
- 배경 Team Select는 dim/blur 처리한다.
- modal에는 팀명, 설명, keyword 3개, 주요 업무 3개, `다른 팀 보기`, `이 팀으로 입사하기`를 제공한다.

## D-037 Touch-first Microinteraction
Status: CONFIRMED — 2026-10-01

- hover는 pointer/demo 환경의 보조 효과다.
- 실제 kiosk UX는 pressed → selected → loading/success/error state를 기준으로 한다.
- hover-only 정보 금지.
- 기본 pressed scale은 약 0.985, 과한 bounce/spin은 사용하지 않는다.

## D-038 Screen Scene Diversity
Status: CONFIRMED — 2026-10-01

같은 design system을 사용하되 모든 화면을 같은 card template로 만들지 않는다.

Examples:
- HOME = hero
- TEAM = explore grid
- TEAM DETAIL = layered modal
- NAME = input focus
- CAMERA = immersive preview
- AI PROCESSING = process
- RESULT = reveal
- NFC = hardware interaction
- REPORT = editorial

## D-039 3D Icon System
Status: CONFIRMED direction — 2026-10-01

- hero 3D object, team 3D icon, utility vector icon의 3단계 asset 체계를 사용한다.
- HOME에는 사원증/퇴근 리포트 3D object를 중앙에 대각선으로 배치한다.
- 6개 팀 icon은 동일 camera/material/light family로 제작한다.
- runtime asset 안에 읽어야 하는 text를 bake하지 않는다.
- 최종 asset은 타 서비스 artwork를 복제하지 않고 독자적으로 제작한다.

## D-040 AI Mode B Integration
Status: CONFIRMED baseline / enhancement optional — 2026-10-01

Baseline:
- 외부 cloud 생성형 image API를 사용하지 않는다.
- 얼굴 identity를 유지하는 local CV + neutral formal-suit composite 방식.
- frontend flow는 SCR-08 → SCR-09 → SCR-11 그대로 유지한다.
- `generateProfile`은 backend-owned integration으로 구현한다.

Optional future:
- 품질이 부족하면 동일 API contract 뒤에 local-LAN GPU worker를 연결할 수 있다.
- GPU worker는 cloud dependency가 아니며, 실제 benchmark 전에는 필수 경로로 확정하지 않는다.

## D-041 Truthful AI Progress
Status: CONFIRMED — 2026-10-01

- fake numeric progress 금지.
- backend가 실제 stage를 제공하지 않으면 indeterminate UI만 사용한다.
- stage UI를 쓰려면 backend-reported state와 1:1로 연결한다.
