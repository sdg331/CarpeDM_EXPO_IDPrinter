# MIRRORTING WORKS · EXPO ID Printer

CarpeDM의 2026 EXPO 사원증 발급·퇴근 리포트 키오스크입니다. **800×1280 세로 터치 화면**을 기준으로, 프레임워크와 빌드 과정 없이 HTML/CSS/JavaScript로 구현했습니다.

하드웨어·함체·프린터 배선·용지 교체·현재 USB 고장까지 포함한 최신 제작 기준은 [`docs/HARDWARE_ENCLOSURE_2026-09-30.md`](docs/HARDWARE_ENCLOSURE_2026-09-30.md)에 통합했습니다. 기존 문서와 충돌할 경우 이 문서와 [`docs/DECISIONS.md`](docs/DECISIONS.md)의 최신 항목을 우선합니다.

## 프론트엔드 실행

Node.js 20 이상에서 별도 패키지 설치 없이 실행합니다.

```sh
npm start
```

- **화면 체험:** <http://localhost:4173/?demo=1>
- **실제 서비스용 UI:** <http://localhost:4173/> — 이 정적 서버에는 백엔드가 없으므로 연결 대기 상태가 정상입니다. 실제 사용 시 아래 FastAPI로 실행하세요.
- Windows PowerShell에서 실행 정책에 막히면 `npm.cmd start`를 사용하세요.

체험 모드에서 입사·퇴근 전체 화면을 확인할 수 있습니다. 상단 **체험 설정**에서 카메라/AI/NFC/프린터 오류, 지연, 기록 없음 등 13가지 상황을 선택할 수 있습니다. 입력한 이름은 메모리에만 유지되며 홈 복귀 또는 새로고침 시 초기화됩니다.

**체험 모드는 실제 촬영·AI 분석·카드 등록·출력을 하지 않습니다.** `?demo=1`을 명시했을 때만 고정 샘플을 사용합니다. 실제 서비스 장애를 샘플 성공으로 바꾸지 않습니다.

## 구현된 화면

2026-09-15 프론트엔드 최종안: 화이트·블루 UI, 팀 소개 카드, 짧은 화면 이동·터치 피드백, 모션 감소 지원을 적용했습니다. 디자인 결정과 검증·연동 인수인계는 [`docs/FRONTEND_FINAL.md`](docs/FRONTEND_FINAL.md)에 정리했습니다.

- 입사: 홈 → 6개 팀과 상세 소개 → 이름 입력 → AI A/B 선택과 설명 → 촬영 → 처리 → 프로필 확인 → NFC 등록 → 출력 → 스마트미러 안내
- 퇴근: 카드 확인 → 체험 기록 확인 → 리포트 미리보기 → 출력 → 완료
- 공통: 오류·재시도, 중복 터치 차단, 45초 유휴 경고/60초 초기화, 완료 후 15초 초기화

## 실제 연동 범위

| 기능 | 현재 상태 |
| --- | --- |
| 카메라 프리뷰 | 브라우저 `getUserMedia` 구현. 장치 권한 필요 |
| 얼굴 감지·캐릭터 매칭 | 기존 `/api/detect`, `/api/match` 계약 연결 |
| AI 프로필 생성 B | 화면·샘플 구현. 실제 로컬 합성 서비스는 연결 예정 |
| NFC 등록·조회 | **백엔드 구현**: ACR1252U PC/SC UID 읽기 + SQLite 세션 매핑. 실물 Pi 검증 필요 |
| 사원증 출력 | **백엔드 구현**: session 기반 렌더 + operationId 중복 방지. ZTP-80USL2 실물 출력 검증 필요 |
| 퇴근 리포트 출력 | 화면·샘플 구현. MirrorTing report 계약/렌더러 연결 예정 |
| MirrorTing 기록 | 화면·샘플 구현. 실제 데이터 조회 서비스 연결 예정 |

기존 FastAPI + YuNet/SFace + 감열 출력 코드를 유지했습니다. 신규 `/api/nfc/register`, `/api/nfc/resolve`, `/api/badge/print`는 로컬 SQLite 세션과 `operationId` 기반 중복 방지를 사용합니다. 기존 `/api/issue`는 호환용으로만 남겨두며 새 UI는 호출하지 않습니다. `screen` 출력 백엔드는 개발용 파일 출력일 뿐 실물 프린터 검증을 대체하지 않습니다.

실제 장치를 연결할 위치는 [`frontend/js/live-integrations.js`](frontend/js/live-integrations.js)입니다. 아직 확정되지 않은 REST 경로를 호출하지 않으며, 구현되지 않은 기능은 연결 준비 안내를 표시합니다. 자세한 인터페이스와 검증 범위는 [`docs/IMPLEMENTATION_STATUS.md`](docs/IMPLEMENTATION_STATUS.md)를 참고하세요.

## 기존 FastAPI 실행

Python 3.12를 권장합니다. 카메라·매칭에는 모델 파일이 필요합니다.

```sh
python -m venv .venv
# Windows
.venv\Scripts\python -m pip install -r requirements.txt
# macOS / Raspberry Pi
.venv/bin/python -m pip install -r requirements.txt
bash scripts/fetch_models.sh
```

모델 파일은 `models/face_detection_yunet_2023mar.onnx`, `models/face_recognition_sface_2021dec.onnx`입니다. Windows에서는 Git Bash로 모델 다운로드 스크립트를 실행할 수 있습니다.

Raspberry Pi에서 ACR1252U를 실제로 사용할 때:

```sh
sudo apt install -y pcscd libpcsclite-dev swig
sudo systemctl enable --now pcscd
export KIOSK_NFC=pcsc
```

NFC 하드웨어 없이 백엔드/UI 연결만 검증할 때는 **명시적으로** mock을 켭니다.

```sh
export KIOSK_NFC=mock
export KIOSK_NFC_MOCK_UID=04AABBCC
```

기본값은 `KIOSK_NFC=disabled`이므로 리더가 없는 상태를 성공으로 가장하지 않습니다. 현재 NFC 구현은 카드 메모리에 개인정보를 쓰지 않고 카드 UID와 로컬 세션을 SQLite에서 연결합니다.

```sh
# Windows
.venv\Scripts\python -m uvicorn backend.app:app --host 127.0.0.1 --port 8002
# macOS / Raspberry Pi
.venv/bin/python -m uvicorn backend.app:app --host 127.0.0.1 --port 8002
```

<http://localhost:8002/>에서 실제 UI, <http://localhost:8002/?demo=1>에서 화면 체험을 엽니다. Pi에는 Pretendard 또는 Noto CJK 한글 폰트가 필요합니다. 이전 프로토타입 실행 문서는 `docs/reference/RUN.md`이며, 새 UI와 다른 동작은 이 README를 우선합니다.

## 테스트

```sh
npm test
# Windows
.venv\Scripts\python -m pytest tests -q
# macOS / Raspberry Pi
.venv/bin/python -m pytest tests -q
```

프론트엔드 핵심 동작 테스트 17개, 기존 백엔드 테스트 14개를 포함합니다. 최신 프론트엔드 검증은 `docs/FRONTEND_FINAL.md`, 실제 하드웨어에서 남은 검증은 `docs/IMPLEMENTATION_STATUS.md`에 기록합니다.

## 구조

```text
frontend/kiosk.html         시작 페이지
frontend/styles/            디자인 토큰·컴포넌트·화면 스타일
frontend/js/app.js          화면 흐름·비동기 작업·유휴 초기화
frontend/js/motion.js       취소 가능한 화면 전환·모달 종료·모션 감소
frontend/js/state.js        현재 관람객 상태·요청 무효화
frontend/js/views.js        화면 마크업
frontend/js/content.js      확정 팀/AI 문구·화면 ID
frontend/js/api-client.js   실제 API와 명시적 샘플 API
frontend/js/camera.js       프리뷰·촬영·스트림 해제
frontend/js/live-integrations.js  구현된 NFC/사원증 backend 연결
backend/app.py             FastAPI routes·idempotency contract
backend/store.py           SQLite session/card/operation state
backend/nfc.py             ACR1252U PC/SC UID reader
backend/badge.py           감열 사원증 렌더
backend/printing.py        screen/ESC-POS/CUPS 출력 계층
assets/                    기존 캐릭터·출력 자산·프로토타입
docs/                      인수인계 명세·구현 상태
tests/frontend/            프론트엔드 회귀 테스트
```

## 출처

- 설계 명세: [mirrorting-works-frontend-handoff](https://github.com/sdg331/mirrorting-works-frontend-handoff), `8059e8e`
- 기존 코드·캐릭터 자산: [CarpeDM_2026DMUEXPO_RaspberryPi](https://github.com/DMUCarpeDM/CarpeDM_2026DMUEXPO_RaspberryPi), `057bd81`

`docs/reference/kiosk-baseline.html`은 변경 전 비교 자료이며 서비스하지 않습니다. 새 화면은 항상 `frontend/kiosk.html`에서 시작합니다.
