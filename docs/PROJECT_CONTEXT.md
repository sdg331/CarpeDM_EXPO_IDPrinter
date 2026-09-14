# Project Context

## Product

- 작품명: **MirrorTing**
- 가상 회사: **MIRRORTING WORKS**
- 장치: 사원증 발급/퇴근 리포트 키오스크
- 전시: 한국전자전/동양미래 EXPO

## Worldbuilding

MIRRORTING WORKS는 관람객이 짧게 입사 체험을 하는 가상의 미래형 회사다.
MirrorTing은 회사 안에서 사용하는 AI 스마트미러 시스템이다.

키오스크는 **입사/퇴근 게이트** 역할을 한다.

```text
입사 등록
→ AI 사원 프로필
→ NFC 사원증
→ MirrorTing 스마트미러 출근/체험
→ NFC 퇴근
→ 개인 리포트 출력
```

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
- 10.1" capacitive touch display
- Raspberry Pi Camera Module 3
- ACR1252U NFC reader
- ZTP-80USL2 80mm thermal kiosk printer
- USB 5V COB LED strip, 8mm, 6W/m
- black 3D printed enclosure
- compact 2.4GHz wireless keyboard for name input (final model TBD)
- no speaker

## Front UI Physical Arrangement

- top center: Camera Module 3
- center: portrait touch display
- display perimeter: 4-sided COB lighting + diffuser
- lower left: thermal printer
- lower right: NFC zone
- bottom: keyboard tray

Fine dimensions are deferred until physical measurement/CAD.

## Experience Targets

- Check-in target: about 40–60 sec excluding MirrorTing experience
- Check-out target: about 10–15 sec
- Session should recover from retryable hardware failures without losing user progress.
- Previous visitor data must never leak into a new session.

## Privacy Direction

- Captured face frames should not be persistently stored by the kiosk flow unless explicitly approved.
- CURRENT `/api/match` processes frame in memory and does not save it to disk.
- Mode A should retain result/embedding-derived data only as required.
- Mode B generated profile image retention policy is PROPOSED: use for badge/session then delete at session/retention boundary.
- NFC should store minimal data; detailed session data belongs in local DB/service.

## Data Principles

Minimize:
- names
- images
- raw biometric-like feature data

Do not log raw photos.

## Product Success

The product succeeds when the visitor understands:
1. 어떤 회사/팀에 입사하는지
2. AI가 무엇을 하는지
3. 어디에 카드를 태그하는지
4. 사원증이 언제 출력되는지
5. 스마트미러와 어떻게 이어지는지
6. 퇴근할 때 무엇을 하면 되는지
