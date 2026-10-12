# Project Context

## 현재 중간 점검 범위 · 2026-09-22

사용자 요청에 따라 오늘 점검은 **라즈베리 파이용 전시 키오스크를 현재 컴퓨터의 브라우저에서 시연**합니다.
첫 화면은 입사/퇴근이며 입사 → AI 프로필 → 카드 연결 단계 → 출력 미리보기 → 스마트미러 안내로 이어집니다.
카메라/AI/PNG 생성은 실제 동작합니다. NFC/실물 출력은 미연결 상태로 표시하며 성공으로 만들지 않습니다.
퇴근 화면에는 카드 확인과 체험 기록이 필요한 이유를 보여주고, 없는 리포트를 생성하지 않습니다.
기본 URL(`/`, `?demo=1`)은 이 시연 동선, `?kiosk=1`은 실제 장치 호출 동선, `?sample=1`은 고정 샘플입니다.
브라우저와 운영 모드는 첫 화면과 반응형 시각 스타일을 공유합니다. 현장 목표 화면은 800×1280입니다.

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
- Mode B currently keeps only the generated PNG in process memory for 10 minutes
  by default (maximum 8), requests deletion on browser reset, and uses expiry as
  fallback. Linking `profileId` to the future badge/session boundary remains TBD.
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
