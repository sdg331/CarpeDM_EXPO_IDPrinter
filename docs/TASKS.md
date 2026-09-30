# Tasks

기준일: 2026-09-30

하드웨어/함체 상세 기준: [HARDWARE_ENCLOSURE_2026-09-30.md](HARDWARE_ENCLOSURE_2026-09-30.md)

## NOW — 물리 제작 우선순위

- [ ] **ZTP-80USL2 USB 연결부 수리 또는 정확한 하네스 확보**
- [ ] 프린터 실물 깊이/전면 플랜지/용지 덮개 개방 공간 재측정
- [ ] Yahboom 10.1" **디스플레이 베젤/프레임 첫 STL 출력**
- [ ] 세로 디스플레이 실물 피팅 및 HDMI/터치 USB 케이블 간섭 확인
- [ ] Raspberry Pi 5 + 화면 + 터치 구동
- [ ] Pi Camera Module 3용 300 mm 케이블 확보 및 구동
- [ ] 오른쪽 NFC 배치 목업 및 태그 거리 확인
- [ ] COB LED 밝기/확산재/발열 테스트
- [ ] 전원/데이터 케이블 경로 확정

프린터 USB 수리를 기다리는 동안 디스플레이/카메라/UI/NFC/LED/베젤 제작은 계속 진행한다.

## NEXT — 프린터/함체

- [ ] ZTP-80USL2 USB 실제 통신
- [ ] USB 수리가 불가할 경우 RS232 대체 경로 검증
- [ ] basket/cradle 형태의 프린터 장착 구조 확정
- [ ] 프린터 전면에는 출력구만 노출
- [ ] 용지 롤 교체 동작 테스트
- [ ] 자동 커터 테스트
- [ ] paper-out / jam / offline에서 실제 감지 가능한 범위 확인
- [ ] 프린터 서비스 시 USB/전원선 스트레인 릴리프 확인
- [ ] 내부 Pi/전원/케이블 브래킷
- [ ] 후면 서비스 구조
- [ ] Bambu Lab A1 분할 조립 허용오차 검증

## NEXT — NFC

- [ ] ACR1252U 실연동
- [ ] 카드 식별/read/write/verify
- [ ] 최소 NFC payload 확정
- [ ] 오른쪽 배치에서 케이블 노출 없이 고정
- [ ] 금속/주변 구조에 따른 태그 감도 확인
- [ ] 카드 회수·재사용 시 이전 사용자 세션 제거 검증
- [ ] NFC ↔ session 연결

## NEXT — Backend Contract

- [x] Session/employee ID ownership
- [ ] Mode B endpoint/service
- [ ] NFC write/read/verify — UID read + local session mapping 코드는 구현, 실물 PC/SC 검증 및 card-memory write 여부는 TBD
- [x] local DB schema
- [ ] MirrorTing result contract
- [ ] report print renderer
- [x] duplicate side-effect protection — NFC registration + badge print
- [x] printer 작업 ID + 완료/불명 상태 계약
- [x] 출력 재시도 시 중복 출력 방지 — ambiguous outcome은 자동 재출력 금지

## NEXT — UI/UX

- [ ] Front-mounted physical keyboard가 없어도 이름 입력 가능하도록 UX 확정
- [ ] touch-first interaction
- [ ] NFC 위치가 화면 안내와 실제 오른쪽 태그 위치에 일치
- [ ] 프린터 처리 중/완료/오류 상태 명확화
- [ ] 용지 없음 등 백엔드가 확실히 알 수 없는 상태는 단정 표시하지 않음
- [ ] 관람객 중도 이탈 후 자동 초기화
- [ ] 이전 사용자 정보가 다음 세션에 남지 않음

## QA — Real Hardware

- [ ] 800×1280 UI
- [ ] portrait display
- [ ] touch
- [ ] Camera Module 3
- [ ] ACR1252U
- [ ] ZTP-80USL2
- [ ] printer 12V 5A separate power
- [ ] Raspberry Pi 5 official 27W power
- [ ] LED separate 5V path
- [ ] HDMI/USB/CSI bend clearance
- [ ] retry scenarios
- [ ] session isolation
- [ ] NFC card reuse
- [ ] duplicate print prevention
- [ ] Pi reboot recovery
- [ ] power-cycle recovery
- [ ] soak test

## BLOCKED / TBD

### Printer USB connector
Current connector/harness is broken. Wrong cable purchases and an unsuccessful solder attempt have already occurred. Identify the exact mating connector/harness or use competent repair service before further destructive work.

### Printer exact mechanical depth
A previous “850 mm” depth note is almost certainly inconsistent with the physical unit. Use real measurement before final cradle STL.

### Printer basket retention
Basket/cradle direction is fixed; exact bolt/snap/guide retention is TBD.

### LED final length
Hardware is fixed; exact strip length and segmentation depend on brightness/heat tests.

### NFC mechanical mount
Right-side visible/exposed direction is preferred; exact bracket shape is TBD.

### MirrorTing report fields
Need smart mirror output contract.
