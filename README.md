# MIRRORTING WORKS · EXPO ID Printer

CarpeDM의 **4-Fit MirrorTing 입사·퇴근 키오스크**입니다. 800×1280 터치 화면에서 팀·이름 선택, 얼굴 촬영과 캐릭터 매칭, NFC 카드 연결, 사원증과 퇴근 리포트 출력으로 이어집니다. HTML/CSS/JavaScript + FastAPI + SQLite를 사용합니다.

## 현재 방문자 UI · 2026-10-05

출근은 이름 입력 후 캐릭터 매칭으로 이어지며 AI B 생성 선택은 제거했습니다. 퇴근은 기록 조회 후 선택적인 기념사진 촬영·재촬영·사진 없이 진행을 제공합니다. 사진은 현재 방문자의 리포트 화면 미리보기에만 포함합니다. **사진 인쇄는 아직 연결되지 않아 실제 출력에는 체험 기록만 들어갑니다.** 사진은 초기화·출력 완료·페이지 종료 시 브라우저 참조를 해제합니다.

아래 B 처리 코드는 이전 기능의 호환성 범위이며 현재 방문자 UI에서는 사용하지 않습니다.

## 구현과 검증 범위

| 기능 | 소프트웨어 구현 | 실제 환경 확인 |
| --- | --- | --- |
| AI A | YuNet/SFace 얼굴 검출·8개 캐릭터 매칭 | Camera Module 3·Pi 처리시간 확인 필요 |
| AI B | 얼굴·기존 옷 유지, 배경 분리·구도 정리, 임시 결과 저장, 세션 연결·배지 렌더 | 실제 촬영 조건의 품질·성능 확인 필요 |
| NFC | PC/SC UID 읽기, 세션 연결·카드 재사용·동시 요청 방지 | ACR1252U 실물 태그 확인 필요 |
| 사원증/리포트 | 감열 이미지, 작업 ID 중복 방지, 결과 불명 시 운영자 복구 | ZTP-80USL2 통신·용지·커터 확인 필요 |
| MirrorTing | 실제 응답 계약 검증, 인증된 방문자 연결, 조회·리포트 렌더 | 대상 서버에 동봉한 연결 모듈 적용 및 공동 검증 필요 |

AI B는 새 얼굴이나 정장을 생성하지 않습니다. 이전 정장 합성 설계는 추가 구현안이며 현재 실행 결과와 구분합니다. 실제 장치가 없거나 연결되지 않으면 성공으로 바꾸지 않습니다.

## 샘플 화면 실행

Node.js 20 이상에서는 패키지 설치 없이 실행합니다.

```sh
npm start
```

<http://localhost:4173/?sample=1>은 **고정 샘플**이며 카메라·카드·프린터에 접근하지 않습니다. 정적 서버의 기본 `/`에는 백엔드가 없으므로 실제 체험은 FastAPI 서버로 실행합니다.

## Python 설치와 실행

Python 3.12를 기준으로 검증합니다.

```sh
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
bash scripts/fetch_models.sh
cp .env.example .env
.venv/bin/python scripts/preflight.py
.venv/bin/python scripts/run_kiosk.py
```

Windows에서는 `.venv/Scripts/python`을 사용하고 모델 다운로드는 Git Bash에서 실행합니다. `.env.example`을 `.env`로 복사해 설정하세요. 테스트가 필요 없는 설치는 `requirements.txt`를 사용합니다.

서버 기본 주소는 <http://127.0.0.1:8002/>입니다. 포트가 사용 중이면 `scripts/run_kiosk.py --port 8012`처럼 변경합니다. 임시 프로필은 메모리에 있으므로 **worker 1개**로 실행합니다. 제공 실행기는 방문자 식별자·이미지 주소가 로그에 남지 않도록 접근 로그를 끕니다.

### 실행 모드

| 주소 | 동작 |
| --- | --- |
| `/` 또는 `/?kiosk=1` | 실제 카메라·AI·NFC·출력·리포트 API. 미연결 장치는 오류/연결 안내 |
| `/?preview=1` | 실제 카메라·로컬 AI와 디지털 배지 미리보기. NFC·실물 출력 성공으로 표시하지 않음 |
| `/?sample=1` | 명시적인 고정 샘플 화면 체험 |
| `/?sample=1&controls=1` | 샘플 체험 + 오류/지연 시나리오 선택 |

기존 로컬 웹 시연의 `?demo=1`은 `?preview=1`과 같은 의미로 유지합니다. `?demo=1&controls=1`은 샘플입니다. 이전 GitHub 문서의 샘플 링크는 `?sample=1`로 바꾸세요.

기본 `/` 화면은 800×1280 고정 캔버스로 표시됩니다. 작은 브라우저 창에서는 배치 변경 없이 전체 화면만 비율에 맞춰 축소합니다.

운영 대상은 800×1280 라즈베리파이 키오스크이며 물리 키보드를 반드시 연결합니다. 이름은 연결된 키보드로 입력하며 화면 키보드는 제공하지 않습니다.

브라우저 카메라 권한은 사용자가 허용해야 합니다. 현장 Chromium의 권한 유지와 실제 터치/한글 입력은 기기에서 확인합니다.

## Raspberry Pi 장치 연결

```sh
sudo apt install -y pcscd libpcsclite-dev swig libusb-1.0-0-dev fonts-noto-cjk
.venv/bin/python -m pip install -r requirements-hardware.txt
sudo systemctl enable --now pcscd
```

`.env`에서 `KIOSK_NFC=pcsc`와 검증할 프린터 백엔드를 설정합니다. ESC/POS USB의 vendor/product ID는 실제 장치에서 확인하세요. 전원·함체·프린터 연결부 기준은 [하드웨어 문서](docs/HARDWARE_ENCLOSURE_2026-09-30.md)를 따릅니다.

기본 `KIOSK_NFC=disabled`는 카드 연결을 거절합니다. 개발용 `KIOSK_NFC=mock`은 고정 UID를 반환하므로 실제 NFC 검증으로 취급하지 않습니다.

기본 `KIOSK_PRINT=screen`은 메모리 출력 미리보기입니다. ESC/POS/CUPS의 `submitted`는 장치나 대기열로 전송되었다는 뜻입니다. 장치가 알려주지 않는 물리적 출력 완료를 추정하지 않습니다. 결과가 불명확하면 자동 재출력을 차단하고 [운영 절차](docs/OPERATIONS.md)에 따라 확인합니다.

## MirrorTing 연결

MirrorTing은 별도 서버이며 정수 체험 세션 ID와 `X-Session-Token`으로 리포트를 제공합니다. 이 키오스크의 사원번호를 그 API에 직접 전달하면 안 됩니다.

1. `integrations/mirrorting/`의 안내에 따라 대상 서버에 연결 모듈을 적용합니다.
2. 두 서버에 동일한 비밀 연결 토큰을 설정하고, `KIOSK_MIRRORTING_URL`을 신뢰하는 서버 주소로 지정합니다.
3. 스마트미러에서 카드 방문자 연결을 먼저 확인하고 생성한 체험 세션을 그 방문자에게 연결합니다.
4. 퇴근 시 실제 리포트를 조회합니다. 기록 없음·진행 중·분석 오류·연결 실패를 구분합니다.

6개 소속 팀과 MirrorTing의 체험 직무는 서로 다른 개념이며 임의로 자동 변환하지 않습니다. 접근 토큰은 브라우저나 리포트에 표시하지 않습니다. [API 계약](docs/API_CONTRACT.md)을 참고하세요.

## 테스트와 운영

```sh
npm test
.venv/bin/python -m pytest tests integrations/mirrorting/test_bridge_client.py -q
.venv/bin/python scripts/preflight.py
# 실제 Pi에서 장치 설정도 점검
.venv/bin/python scripts/preflight.py --hardware
```

GitHub Actions 설정은 소프트웨어 테스트를 실행합니다. 실제 Actions 실행 결과와 실물 장치 검증은 별도입니다. 최신 로컬 검증 결과는 [구현 상태](docs/IMPLEMENTATION_STATUS.md)에 기록합니다.

- [현장 운영·출력 결과 불명 복구](docs/OPERATIONS.md)
- [개인정보 보관과 삭제](docs/DATA_PRIVACY.md)
- [인수 테스트 기준](docs/ACCEPTANCE_CRITERIA.md)
- [화면 QA](docs/FRONTEND_QA_CHECKLIST.md)
- systemd 예시: `deploy/mirrorting-kiosk.service.example`

원본 촬영 사진은 디스크에 기록하지 않습니다. 생성된 B 프로필은 기본 10분, 출력 미리보기는 5분 동안 서버 메모리에 보관합니다. 이름·UID·MirrorTing 접근 토큰은 기본 24시간 후 삭제/익명화하고, 중복 출력 방지에 필요한 최소 작업 상태는 유지합니다. 사용자가 직접 저장한 PNG는 사용자의 기기에 남습니다.

## 구조

```text
frontend/                  화면·상태·카메라·API 어댑터
backend/app.py             FastAPI 계약·장치 작업·세션 연결
backend/store.py           SQLite 세션·카드·작업 중복 방지
backend/profile.py         로컬 B 프로필·임시 메모리 저장
backend/reports.py         실제 MirrorTing 응답 검증·감열 리포트
backend/badge.py            A/B 배지 렌더
backend/printing.py         메모리 미리보기·ESC/POS·CUPS
integrations/mirrorting/   상대 서버 연결 모듈·적용 안내
scripts/                   실행·점검·운영자 복구
tests/                     프런트·백엔드 회귀 및 계약 테스트
docs/                      제품·설계·현재 계약·운영 기록
```

## 출처

- 설계 명세: [mirrorting-works-frontend-handoff](https://github.com/sdg331/mirrorting-works-frontend-handoff), `8059e8e`
- 기존 코드·캐릭터 자산: [CarpeDM_2026DMUEXPO_RaspberryPi](https://github.com/DMUCarpeDM/CarpeDM_2026DMUEXPO_RaspberryPi), `057bd81`

`docs/reference/`와 구현 상태 문서의 이전 날짜 항목은 이력입니다. 현재 실행 방법은 이 README를 우선합니다.
