# MIRRORTING WORKS · EXPO ID Printer

CarpeDM의 2026 EXPO 사원증 발급·퇴근 리포트 키오스크입니다. HTML/CSS/JavaScript와 로컬 FastAPI를 사용합니다. 라즈베리 파이용 키오스크를 현재 컴퓨터의 브라우저에서 시연합니다. 입사·스마트미러·퇴근의 전시 동선을 중심으로 구성하며 800×1280 세로와 데스크톱 화면을 지원합니다.

## 오늘 중간 점검 실행

이미 준비된 이 컴퓨터에서는 저장소 안에서 다음 명령으로 실행합니다.

```sh
.venv/bin/python -m uvicorn backend.app:app --host 127.0.0.1 --port 8002
```

**<http://127.0.0.1:8002/>**를 열고 입사 → 팀 → 이름 → AI 방식 → 카메라 촬영 → 결과 → 카드 연결 단계 → 출력 미리보기 → 스마트미러 안내 순서로 진행합니다. `?demo=1`도 동일한 동작입니다. 이미 서버가 실행 중이면 명령을 중복 실행하지 않아도 됩니다. 퇴근 화면에서는 카드 확인과 리포트의 미연결 상태를 확인할 수 있습니다.

- 방식 A: 카메라로 촬영한 얼굴을 YuNet·SFace로 처리해 8개 캐릭터 중 매칭합니다.
- 방식 B: 실제 얼굴과 촬영한 옷을 유지하고, 로컬 배경 분리와 얼굴 중심 확대 구도를 적용합니다. 정장을 덧씌우지 않으며 머리카락 경계 품질에 한계가 있습니다.
- 웹사이트에 처음 들어가면 브라우저가 카메라 권한을 요청합니다. 한 번 허용하면 해당 주소의 브라우저 권한을 재사용하며, 촬영 화면에서는 별도 버튼 없이 자동 연결합니다. 파일 업로드는 제공하지 않습니다.
- NFC 등록·물리 출력·MirrorTing 기록의 화면은 미리 볼 수 있지만 실제 장치와 데이터는 미연결입니다. 등록/출력 완료로 표시하지 않습니다. 출력 미리보기에서 실제 PNG를 보조 기능으로 저장할 수 있습니다.
- 첫 화면과 시스템 상태에는 현장 Raspberry Pi 5, Camera Module 3, ACR1252U NFC, ZTP-80USL2 감열 프린터 구성을 함께 표시합니다. 웹 시연과 현장 장치의 역할을 구분하면서 전체 키오스크 구성을 설명할 수 있습니다.
- 완성 프로필은 서버 메모리에 최대 10분 보관하고, 처음으로 돌아가면 삭제를 요청합니다. 사용자가 내려받은 PNG는 컴퓨터에 남습니다.
- 인터넷 공개 배포는 하지 않습니다. 이 컴퓨터에서 서버가 실행 중이어야 합니다.

## 프론트엔드 실행

Node.js 20 이상에서 별도 패키지 설치 없이 실행합니다.

```sh
npm start
```

- **고정 샘플 화면 체험:** <http://localhost:4173/?sample=1>
- **실제 서비스용 UI:** <http://localhost:4173/> — 이 정적 서버에는 백엔드가 없으므로 연결 대기 상태가 정상입니다. 실제 사용 시 아래 FastAPI로 실행하세요.
- Windows PowerShell에서 실행 정책에 막히면 `npm.cmd start`를 사용하세요.

체험 모드에서 입사·퇴근 전체 화면을 확인할 수 있습니다. 공개 시연에서는 설정을 숨기고 정상 흐름만 보여줍니다. 개발 중 오류·지연·기록 없음 등 13가지 상황을 확인하려면 `?demo=1&controls=1`로 접속해 상단 **시연 설정**을 사용합니다. 입력한 이름은 메모리에만 유지되며 홈 복귀 또는 새로고침 시 초기화됩니다.

**고정 샘플 모드는 실제 촬영·AI 분석·카드 등록·출력을 하지 않습니다.** `?sample=1` 또는 개발용 `?demo=1&controls=1`에서만 고정 샘플을 사용합니다. `/`와 `?demo=1`은 실제 웹 체험이며, 실제 서비스 장애를 샘플 성공으로 바꾸지 않습니다.

## 구현된 화면

2026-09-15 프론트엔드 최종안: 화이트·블루 UI, 팀 소개 카드, 짧은 화면 이동·터치 피드백, 모션 감소 지원을 적용했습니다. 디자인 결정과 검증·연동 인수인계는 [`docs/FRONTEND_FINAL.md`](docs/FRONTEND_FINAL.md)에 정리했습니다.

- 입사 운영 UI: 홈 → 6개 팀과 상세 소개 → 이름 입력 → AI A/B 선택과 설명 → 촬영 → 처리 → 프로필 확인 → NFC 등록 → 출력 → 스마트미러 안내
- 공개 데모: 팀·AI 방식의 핵심 선택만 남기고 상세 설명 화면을 생략해 같은 발급 흐름을 빠르게 시연
- 퇴근: 카드 확인 → 체험 기록 확인 → 리포트 미리보기 → 출력 → 완료
- 공통: 오류·재시도와 중복 터치 차단. 운영 UI는 45초 유휴 경고/60초 초기화와 완료 후 15초 초기화를 적용하고, 공개 데모는 발표 중 자동 초기화를 하지 않음

## 실제 연동 범위

| 기능 | 현재 상태 |
| --- | --- |
| 카메라 프리뷰 | 브라우저 `getUserMedia` 구현. 장치 권한 필요 |
| 얼굴 감지·캐릭터 매칭 | 기존 `/api/detect`, `/api/match` 계약 연결 |
| AI 프로필 생성 B | YuNet 품질 확인 + 로컬 GrabCut + 원래 옷을 유지하는 얼굴 중심 구도 및 결과 미리보기 구현 |
| NFC 등록·조회 | 화면·샘플·서비스 인터페이스 구현. ACR1252U 연동 예정 |
| 사원증·리포트 출력 | 화면·샘플 구현. 실제 작업 ID/완료 확인 계약 연결 예정 |
| MirrorTing 기록 | 화면·샘플 구현. 실제 데이터 조회 서비스 연결 예정 |

기존 FastAPI + YuNet/SFace + 감열 출력 코드를 유지했습니다. 기존 `/api/issue`는 물리 출력 완료와 중복 방지를 보장하는 작업 API가 아니므로 새 UI에서 바로 호출하지 않습니다. 특히 `screen` 출력 백엔드의 파일 저장을 실물 출력 완료로 표시하지 않습니다.

NFC·출력·MirrorTing 실제 장치를 연결할 위치는 [`frontend/js/live-integrations.js`](frontend/js/live-integrations.js)입니다. Mode B는 같은 출처의 `/api/profile`에 연결되어 있으며, 나머지 미확정 기능은 임의 REST 경로를 호출하지 않고 연결 준비 안내를 표시합니다. 자세한 인터페이스와 검증 범위는 [`docs/IMPLEMENTATION_STATUS.md`](docs/IMPLEMENTATION_STATUS.md)를 참고하세요.

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

```sh
# Windows
.venv\Scripts\python -m uvicorn backend.app:app --host 127.0.0.1 --port 8002
# macOS / Raspberry Pi
.venv/bin/python -m uvicorn backend.app:app --host 127.0.0.1 --port 8002
```

<http://localhost:8002/>에서 실제 웹 체험, <http://localhost:8002/?kiosk=1>에서 장치 연동용 세로 UI, <http://localhost:8002/?sample=1>에서 고정 샘플 체험을 엽니다. Pi에는 Pretendard 또는 Noto CJK 한글 폰트가 필요합니다. 이전 프로토타입 실행 문서는 `docs/reference/RUN.md`이며, 새 화면의 실행 방식은 이 README를 우선합니다.

## 테스트

```sh
npm test
# Windows
.venv\Scripts\python -m pytest tests -q
# macOS / Raspberry Pi
.venv/bin/python -m pytest tests -q
```

프론트엔드 핵심 동작 테스트와 백엔드 테스트를 포함합니다. 최신 구현 범위와 실제 하드웨어에서 남은 검증은 `docs/IMPLEMENTATION_STATUS.md`에 기록합니다.

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
frontend/js/live-integrations.js  추후 장치 연동 지점
backend/                   기존 매칭·배지·출력 구현
backend/profile.py         Mode B 로컬 분리·얼굴 중심 구도·임시 메모리 저장
assets/                    기존 캐릭터·출력 자산·프로토타입
assets/profile/            사용자 제공 정장 사진과 기존 참고 템플릿
docs/                      인수인계 명세·구현 상태
tests/frontend/            프론트엔드 회귀 테스트
```

Mode B 완성 이미지는 디스크에 기록하지 않고 서버 메모리에 기본 10분,
최대 8개만 유지합니다. 브라우저 세션을 초기화하면 즉시 삭제를 요청하며,
서버는 만료된 결과를 자동 제거합니다. 운영 시 Uvicorn은 기본 단일 worker로
실행해야 메모리 이미지 생성과 조회가 같은 프로세스에서 처리됩니다.

## 출처

- 설계 명세: [mirrorting-works-frontend-handoff](https://github.com/sdg331/mirrorting-works-frontend-handoff), `8059e8e`
- 기존 코드·캐릭터 자산: [CarpeDM_2026DMUEXPO_RaspberryPi](https://github.com/DMUCarpeDM/CarpeDM_2026DMUEXPO_RaspberryPi), `057bd81`

`docs/reference/kiosk-baseline.html`은 변경 전 비교 자료이며 서비스하지 않습니다. 새 화면은 항상 `frontend/kiosk.html`에서 시작합니다.
