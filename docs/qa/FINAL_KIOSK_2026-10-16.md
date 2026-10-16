# 최종 키오스크 커밋·소프트웨어 점검 · 2026-10-16

대상은 `sdg331/CarpeDM_EXPO_IDPrinter`의 `codex/nfc-smart-mirror-link`다. 기존 미커밋42개를 사진 출력·화면 구성·성별 조건을 반영한 얼굴 매칭으로 나눠 모두 커밋했다. 원격 기능 브랜치의 NFC·USB·카드 없는 촬영 수정과 기존 `main`의 응원 인화·출력 복구도 함께 포함한다. 실제 Pi가 알려준 기존 체크아웃은 `f080cda`였으며, 업데이트 대상 브랜치는 아래 명령으로 명시한다.

## 동작 기준

- 추천 조건은 `남자·여자·상관없음`, 기본값은 `상관없음`이다. 남자/여자는 각각 설정된4명, 상관없음은8명을 비교한다. 방문자의 성별을 추정하지 않는다.
- 선택은 촬영·재촬영에 유지되며 새 방문자 초기화 시 상관없음으로 돌아간다. 잘못된 조건이나 다른 조건의 후보를 반환한 워커 결과는 거부한다.
- 운영 추천은 `/api/match/landmarks`, MediaPipe478점·9개 비율을 사용한다. 분석 응답을 받으면 바로 결과로 이동한다. 실패를 SFace/무작위 성공으로 대체하지 않는다.
- 새 아이콘·분석/추천 근거·조회 오류 UI, 카드 없는 촬영, 감마 보정, 응원 문구/도장, 결과 불명 출력 복구를 유지한다.
- 현재 의존성/생성 코드와 달랐던 인쇄 자산8개·비교 벡터를 기존 생성기로 다시 만들었다. 자산 일치 검사를 약하게 바꾸지 않았다.
- 변경 모듈과 호출자의 캐시 버전은 `20261016-final-kiosk-r1`이다. 이전 모듈이 섞여 로드되는 것을 막는다.

## 실제 수행한 검사

- `npm test`:96 passed,0 failed.
- `.venv/bin/python -m pytest tests integrations/mirrorting/test_bridge_client.py -q --tb=short -rs`:216 passed,2 skipped. 생략은 독립 스타일 표본을 요구하는 품질 검사와 선택적인 ESC/POS 인코더 검사다. 기존 FastAPI/Starlette의 TestClient deprecation 경고1개가 있다.
- 전체 프런트엔드 모듈 `node --check`, 백엔드·스크립트·브리지 `compileall`, `git diff --check` 통과.
- 소프트웨어 preflight 통과. 없는 인터프리터를 지정하면 MediaPipe 필수 환경 FAIL과 종료 코드1을 확인했다. 인터프리터/기준 파일 점검은 실제 추론 성공 보증과 구분한다.
- 새 로컬 서버8017에서 공개 캐릭터01/02 × any/male/female의 실제 API6건을 확인했다. 모두 HTTP200, 후보8/4/4명, 실제478점·9개 비율, 조건 밖 후보 없음, 외부 업로드 없음. 닮음 정확도 검증은 아니다.
- 실제 CSS 뷰포트800×1280에서 선택 버튼과 여자01/03/05/07·남자02/04/06/08·전체8명 표시, 이미지 로딩, 가로 넘침 없음, 샘플 촬영/여자 결과, 재촬영 후 여자 조건 유지 확인. 재촬영 전환은 키보드 활성화로도 확인했다. 실제 Pi 터치 입력은 미검증이다.
- 고정 UI 미리보기의 분석 오류에서 안내·재시도·처음으로 버튼, 분석 사진 숨김, 원시 오류 미노출을 확인했다.389×843 웹 결과는 문서 너비389/389, 본문 너비318/318, 여자4명 비교 근거와 이미지 로딩을 확인했다. 브라우저 경고·오류 로그는 없었다.
- Linux ARM64용 MediaPipe0.10.18 Python3.12 wheel을 공식 PyPI에서 다운로드했다. 플랫폼 마커가 Linux ARM64에는0.10.18, Intel Linux/macOS와 Windows에는0.10.21 하나만 선택함을 assert로 확인했다.0.10.18도 별도 Intel Mac 환경에서 공개 샘플 any/male/female의478점·8/4/4명 추천이 성공했다. ARM 바이너리를 실제 Pi에서 실행한 검사는 아니다.

브라우저·API 검사는 NFC disabled, printer screen, 별도 임시 DB를 사용했다. 원본 방문자 사진을 촬영하지 않았다. 공개 샘플 검사와 화면 기록은 Git 제외 경로 `.preview/final-gender-check.json`, `.preview/final-gender-female.jpg`, `.preview/final-gender-male.jpg`에 있다.

## Pi 업데이트

방문자와 출력 작업이 끝난 뒤 기존 서버를 정상 종료한다. 실제 IDPrinter 프로젝트 폴더에서 `git remote -v`, `git status --short`를 먼저 확인한다. 원격은 `https://github.com/sdg331/CarpeDM_EXPO_IDPrinter.git`이어야 한다. 로컬 변경이 있거나 명령이 실패하면 중단하고 변경을 보존한다. `.env`와 세션 DB를 덮어쓰지 않는다.

```sh
git fetch origin
git switch codex/nfc-smart-mirror-link
git pull --ff-only origin codex/nfc-smart-mirror-link
git log -1 --oneline
```

필수 별도 환경이 없다면64비트 OS·Python3.12를 확인하고 설치한다. 기존 NumPy2 키오스크 환경에 MediaPipe를 섞어 설치하지 않는다.

```sh
.venv/bin/python -V
.venv/bin/python -m venv .venv-landmarks
.venv-landmarks/bin/python -m pip install -r requirements-landmarks.txt
.venv/bin/python scripts/fetch_landmark_model.py
.venv/bin/python scripts/preflight.py --hardware
```

비교 기준과 분포 보정 JSON은 저장소에 포함돼 있다. 현재 캐릭터/모델을 유지하면 공개 실사 데이터셋을 다시 준비하거나 보정을 다시 생성할 필요가 없다. preflight 실패 시 서버 시작 전에 원인을 해결한다. 모든 필수 점검이 통과하면 기존 서비스 관리 방법으로 서버를 재시작하고 Pi Chromium의 `http://127.0.0.1:8002/`를 새로고침한다. 터미널 실행 환경이면 다음을 사용한다.

```sh
.venv/bin/python scripts/run_kiosk.py --host 127.0.0.1 --port 8002
```

## 남은 현장 확인

실제 Pi의 패키지 설치·추론 지연·카메라 권한/조명·사람이 느끼는 닮음·터치/한국어 IME·NFC 연결/재사용·프린터 농도/용지 배출/절단·MirrorTing 실제 기록 연동·전원 재인가 후 복구는 현장 확인이 필요하다. Mac/샘플/자동 테스트 결과로 완료 처리하지 않는다.
