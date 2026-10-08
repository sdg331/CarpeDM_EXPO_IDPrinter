# MIRRORTING WORKS · EXPO ID Printer

CarpeDM의 **4-Fit MirrorTing 입사·퇴근 키오스크**입니다. 800×1280 터치 화면에서 팀·이름 선택, 얼굴 촬영과 캐릭터 매칭, NFC 카드 연결, 사원증과 퇴근 리포트 출력으로 이어집니다. HTML/CSS/JavaScript + FastAPI + SQLite를 사용합니다.

## 캐릭터 사진 8명 반영 · 2026-10-07

승인한 사진 중 `char_01.png`~`char_08.png`를 사용합니다. 안내 화면은 4열×2행으로 8명을 보여주며, 192×256 WebP 미리보기를 사용합니다. 결과 화면은 컬러 원본, 감열 사원증은 동일 원본에서 만든 288×384 1비트 이미지를 사용합니다. 9~12번 사진·미리보기·인쇄 자산과 변경 전 비교 데이터는 상위 폴더의 `completion-backups/portraits12-before-8-20261007/`에 보관했습니다.

SFace 비교 데이터도 8명으로 재생성합니다. 이전 스타일 표본은 새 사진과 스타일이 다르므로 재사용하지 않습니다. 현재는 기존 엔진의 **캐릭터 자기 평균 보정 경로**를 사용하며, 실사 관람객 보정은 미완료입니다. 그룹 메타데이터 `?`는 분류 미지정이며 매칭에 영향을 주지 않습니다. 독립 스타일 표본이 없어 분리도 품질 게이트 테스트는 보류(skip)합니다. 실제 관람객의 매칭 품질, Pi 촬영·처리시간, 감열 출력은 별도 검증이 필요합니다.

자산 재생성 후 서버를 다시 시작하세요.

```sh
.venv/bin/python scripts/build_prototypes.py
.venv/bin/python scripts/make_print_assets.py
.venv/bin/python scripts/make_print_assets.py --sweep
```

현재 사진과 같은 스타일의 독립 표본을 확보·검증한 경우에만 `scripts/build_prototypes.py --style-set /path/to/validated-style-set`을 사용합니다. `assets/style_set`은 이전 사진의 표본이므로 새 세트용으로 취급하지 않습니다. 실제 관람객 분포는 동의받은 사진으로 `scripts/distribution_test.py`에서 확인합니다. 모델이 없는 CI 환경에서는 실제 임베딩 재계산 테스트도 건너뜁니다.

## 현재 방문자 UI · 2026-10-05

출근은 이름 입력 후 캐릭터 매칭으로 이어지며 AI B 생성 선택은 제거했습니다. 퇴근은 기록 조회 후 선택적인 기념사진 촬영·재촬영·사진 없이 진행을 제공합니다. 사진은 현재 방문자의 리포트 화면 미리보기에만 포함합니다. **사진 인쇄는 아직 연결되지 않아 실제 출력에는 체험 기록만 들어갑니다.** 사진은 초기화·출력 완료·페이지 종료 시 브라우저 참조를 해제합니다.

아래 B 처리 코드는 이전 기능의 호환성 범위이며 현재 방문자 UI에서는 사용하지 않습니다.

## 구현과 검증 범위

| 기능 | 소프트웨어 구현 | 실제 환경 확인 |
| --- | --- | --- |
| AI A | YuNet/SFace 얼굴 검출·8개 캐릭터 매칭 | 실제 관람객 매칭 품질·Camera Module 3·Pi 처리시간 확인 필요 |
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

### UI 전체 화면 바로 보기

```bash
npm start
```

`http://localhost:4173/static/ui-preview.html`에서 현재 구현된 키오스크/웹 화면 27개를 바로 선택할 수 있습니다. 6개 팀과 기본·로딩·오류·기록 없음·출력 결과 불확실 상태를 선택할 수 있습니다. 상태 표현이 있는 화면에만 해당 상태가 반영됩니다.

화면 선택 후 표시되는 주소를 복사하면 같은 화면/팀/상태로 다시 열립니다. 예: `/static/ui-preview.html?screen=reportPrint&team=design&state=error`.

키오스크 미리보기는 실제 장치의 `kiosk` CSS를 사용해 글자·여백·버튼 크기를 맞춥니다. `frontend/kiosk.html`을 파일로 직접 열면 `/static/`과 `/assets/` 경로를 불러올 수 없으므로 반드시 위 로컬 서버 주소로 접속하세요.

화면 바깥의 미리보기 도구 영역에 고정 UI 안내를 표시합니다. 키오스크 안의 헤더와 하단은 실제 장치 화면과 동일하게 표시하며 `샘플` 배너와 `UI SAMPLE` 표기를 넣지 않습니다. AI·카드·출력 결과 본문의 예시/장치 미사용 안내는 유지합니다.

이 페이지는 기존 `views.js`와 CSS를 재사용하는 고정 UI 미리보기입니다. 사진·이름·기록은 예시이며 디지털 사원증은 기존 브라우저 이미지 생성 기능으로 샘플을 만듭니다. 카메라/AI/API/NFC/출력을 실행하지 않고 자동으로 다음 화면으로 넘어가지 않습니다. 화면 내부 버튼은 동작하지 않습니다. 실제 클릭 흐름은 `/?sample=1&controls=1`에서 확인하세요. 키오스크 화면은 800×1280 원본 크기를 유지하며 작은 창에서는 스크롤합니다. 로딩 표시를 안내 문구 위에 한 번만 표시하며 퇴근 카드 아이콘은 400px 영역에 중앙 정렬합니다. 현재 제거된 키오스크 모드 선택/Mode B 전용 화면은 목록에 포함하지 않습니다.
