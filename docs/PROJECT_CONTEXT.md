# Project Context

## Product

- 작품 전체: **4-Fit MirrorTing**
- 가상 회사: **MIRRORTING WORKS**
- 스마트미러 시스템명: **MirrorTing**
- 장치: 사원증 발급/퇴근 리포트 키오스크
- 전시: 동양미래 EXPO

키오스크 하드웨어·함체의 최신 기준은 [HARDWARE_ENCLOSURE_2026-09-30.md](HARDWARE_ENCLOSURE_2026-09-30.md)를 우선한다.

## Worldbuilding

MIRRORTING WORKS는 관람객이 짧게 입사 체험을 하는 가상의 미래형 회사다.
MirrorTing은 회사 안에서 사용하는 AI 스마트미러 시스템이다.

키오스크는 **입사/퇴근 게이트** 역할을 한다.

입사 등록
→ AI 사원 프로필
→ NFC 사원증
→ MirrorTing 스마트미러 출근/체험
→ NFC 퇴근
→ 개인 리포트 출력

NFC 카드는 관람객에게 증정하지 않고 전시 운영용으로 회수·재사용한다.

## Visitor Context

관람객은:
- 개발자가 아닐 수 있음
- 처음 화면을 봄
- 전시장에서 오래 읽지 않음
- 빠르게 여러 번 터치할 수 있음
- 중간에 떠날 수 있음
- 기술적 에러 메시지를 이해할 필요가 없어야 함

따라서 제품은 직원 설명 없이도 주요 흐름이 이해되어야 한다.

## Target Hardware

CONFIRMED:
- Raspberry Pi 5 8GB
- 공식 Pi 5 27W USB-C 전원
- Yahboom MPJ1008 계열 10.1" capacitive touch display
- Raspberry Pi Camera Module 3
- ACR1252U NFC reader
- ZALCOM ZTP-80USL2 80mm thermal kiosk printer
- printer dedicated 12V 5A power
- 5V COB LED strip + ON/OFF controller
- black 3D printed enclosure
- no speaker
- no front-mounted keyboard tray

IMPORTANT:
- Printer power is never supplied directly from the Raspberry Pi.
- USB is the primary printer data path; RS232 is a fallback.
- Powered USB hub is optional, not mandatory.
- The current printer USB connector/harness is damaged and requires repair/replacement.

## Current Physical Direction

Approximate enclosure:
- 300(W) × 150(D) × 520(H) mm
- portrait orientation
- matte black
- segmented for Bambu Lab A1 256 × 256 × 256 mm build volume

Front/side:
- top center: Camera Module 3
- center: portrait touch display
- COB lighting around the upper/display area with diffuser
- thermal printer body hidden; output slot only visible
- NFC: right-side placement preferred; may be visibly exposed or slightly protruding
- no front keyboard tray

Service:
- printer uses a removable basket/cradle direction for paper replacement
- hidden hinge + push latch is not used
- cable routing must preserve display HDMI/USB/CSI bend clearance
- power and data paths should remain serviceable and visually hidden

Fine dimensions remain dependent on real-part measurement and test prints.

## Experience Targets

- Check-in target: about 40–60 sec excluding MirrorTing experience
- Check-out target: about 10–15 sec
- Session should recover from retryable hardware failures without losing user progress.
- Previous visitor data must never leak into a new session.
- NFC cards must be safely reset/reissued for reuse.

## Privacy Direction

- Captured face frames should not be persistently stored by the kiosk flow unless explicitly approved.
- CURRENT /api/match processes frame in memory and does not save it to disk.
- Mode A should retain result/embedding-derived data only as required.
- Mode B generated profile image retention policy is PROPOSED: use for badge/session then delete at session/retention boundary.
- NFC should store minimal data; detailed session data belongs in local DB/service.
- Do not log raw photos.

## Product Success

The product succeeds when the visitor understands:
1. 어떤 회사/팀에 입사하는지
2. AI가 무엇을 하는지
3. 어디에 카드를 태그하는지
4. 사원증이 언제 출력되는지
5. 스마트미러와 어떻게 이어지는지
6. 퇴근할 때 무엇을 하면 되는지

## Current Build Priority

1. display bezel/frame first test print
2. Pi + display + touch
3. Camera Module 3 and 300 mm cable
4. LED diffuser and right-side NFC
5. printer USB repair / harness replacement
6. printer basket/cradle
7. power/cable management
8. full hardware integration and soak test
