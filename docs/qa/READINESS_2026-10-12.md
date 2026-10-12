# 전체 점검 및 실행 준비 · 2026-10-12

대상: `CarpeDM_EXPO_IDPrinter-complete`, 브랜치 `codex/newhire-portrait-integration`, 기준 HEAD `0c66339`와 현재 미커밋 작업본. 기존 사진·코드 변경은 보존했다. 소프트웨어 검증은 통과했으며 실제 Pi 장치 인수는 미완료다. 커밋·배포·systemd 설치는 진행하지 않았다.

## 확인한 문제와 수정

1. 캐릭터 결과가 마음에 들지 않으면 재촬영만 할 수 있었다. 추천 결과에서 8명 중 직접 고르는 창을 추가하고 선택한 ID를 기존 등록/출력 계약으로 전달한다. 등록 후, 처리 중, 오류 상태에서는 선택을 차단한다. 재촬영·새 방문자 시작 시 직접 선택 상태를 제거한다.
2. 결과 문구를 “오늘 함께할 캐릭터예요.”로 변경했다. 직접 선택하면 “내가 고른 캐릭터예요.”를 표시한다. 외모 평가나 닮음 확률을 표시하지 않는다.
3. 브라우저가 이전 HTML/CSS를 읽어 선택창 배치가 깨지는 문제를 확인했다. HTML에 `Cache-Control: no-store, max-age=0`을 적용하고 현재 JS/CSS/사진 버전을 `20261012-readiness-r1`로 통일했다.
4. 정적 화면 미리보기의 결과 화면에 이미 등록된 세션이 들어 있어 새 선택 버튼이 숨는 문제를 수정했다. 미리보기는 실제 카드 등록/출력을 실행하지 않는다.
5. 현재 출근 동선과 맞지 않는 운영 문서의 A/B 발급 안내를 정리하고 [실행 안내](../START_HERE.md)를 추가했다.

주요 수정 파일: `frontend/js/app.js`, `state.js`, `views.js`, `ui-preview.js`, `frontend/styles/kiosk.css`, HTML/버전 참조, `backend/app.py`, 프런트/HTTP 회귀 테스트, README 및 화면/동선/운영 문서. 자산과 특징 벡터는 직전 r6를 유지했다. 새 의존성이나 API는 추가하지 않았다.

## 자동 테스트

| 실행한 검증 | 결과 |
| --- | --- |
| `npm test` | 60 passed, 0 failed |
| `.venv/bin/python -m pytest tests integrations/mirrorting/test_bridge_client.py -q` | 93 passed, 1 skipped, 1 warning |
| `.venv/bin/python scripts/preflight.py` | 의존성·모델·8명 벡터·PNG/WebP/인쇄 자산·한글 폰트 모두 PASS |
| `.venv/bin/python -m pip check` | No broken requirements found |
| `.venv/bin/python -m compileall -q backend scripts` | 통과 |
| `node --check` — frontend/js와 scripts의 JS/MJS 파일 | 통과 |
| `git diff --check` | 통과 |
| `.venv/bin/python scripts/preflight.py --hardware` | 현재 Mac에서 실제 NFC와 실물 출력 설정 FAIL |

Skip 1개는 독립 스타일 표본이 없어서 제외한 얼굴 분리도 검사다. 기존 Starlette/httpx TestClient 사용 관련 경고 1개가 있다. pip의 캐시 디렉터리 권한 경고도 있었으나 의존성 검사 자체는 통과했다. 장치 검사 실패는 이 Mac의 `disabled` NFC / `screen` 출력 설정을 반영한다.

새 회귀 테스트는 유효하지 않은/처리 중/등록 완료 캐릭터 변경 차단, 선택 상태 초기화, 선택한 05번의 NFC 요청·DB 저장·실제 배지 렌더 전달, 8개 선택지와 문구 구분, HTML 캐시 헤더를 검증한다. 기존 방문자 격리·늦은 응답 차단·중복 작업·출력 결과 불명 복구·요청 출처 및 bridge 인증 검사도 통과했다.

## 브라우저와 실제 HTTP 검증

현재 폴더의 FastAPI 서버를 8012에서 확인했다. 설정은 `KIOSK_NFC=disabled`, `KIOSK_PRINT=screen`이다. 8013의 별도 검증 서버는 임시 테스트 DB, mock NFC, screen 출력으로 운영 데이터를 사용하지 않았다.

- 800×1280: 키오스크 18개 화면 × 기본/로딩/오류/불명 상태 = 72개. 제목 누락, 가로 넘침, 화면 밖 버튼 없음. 각 화면에서 사용하지 않는 상태는 기존 표현을 유지한다.
- 390×844: 웹 9개 화면 × 기본/오류/불명 상태 = 27개. 제목과 가로 넘침 검사 통과. 모바일 전체 실사용이나 카메라 품질 검증을 의미하지 않는다.
- 출근 샘플: 팀 → 이름 → 촬영 → 추천 → 선택창 취소 및 포커스 복귀 → 05번 선택 → 카드 연결 시연 → 출력 시연 → 완료. 선택창 8장 로드, 4×2 배치와 행동 버튼을 확인했다. 샘플 완료는 실제 출력이 없다고 표시한다.
- 퇴근 샘플: 카드 확인 → 사진 생략 → 리포트 → 출력 시연 → 완료 → 홈. 다음 화면에 이전 이름이 남지 않는다. 프린터 오류 시나리오에서 안내·재시도 버튼을 확인하고 명시적 재시도로 완료했다.
- 등록되지 않은 카드 샘플: 이름·리포트가 표시되지 않고 오류 안내 후 홈으로 복귀한다.
- 별도 HTTP 흐름 7개: HTML 캐시 차단, 모델/자산 로드, 카드 재사용 시 이전 세션 출력 거절, 선택한 05번 576×808 1비트 배지 생성, 같은/다른 작업 ID로 중복 출력 방지, 현재 카드 조회와 MirrorTing 미설정 안내, 잘못된 캐릭터 ID 거절. 모두 통과했다.

증거는 저장소 상위 `output/readiness-20261012/`에 저장했다. `screens-800x1280.json`, `screens-390x844.json`, `http-flow.json`은 집계 결과이며 실제 방문자 개인정보를 포함하지 않는다.

검증 후 8013 테스트 서버는 종료하고 8012 화면 시연 서버는 유지했다. 현장 장치 설정을 적용한 서버가 아니다.

- [8명 선택창](../../../output/readiness-20261012/character-picker-800x1280.png)
- [직접 선택한 05번](../../../output/readiness-20261012/selected-character-800x1280.png)
- [샘플 프린터 오류](../../../output/readiness-20261012/printer-error-800x1280.png)

## 매칭 품질과 현장 인수

직전 [r6 검증](GLASSES05_2026-10-12.md)의 LFW 평가 660명에서 최대 선택 비중 18.9%, 1·2위 마진 0.02 미만 31.8%를 유지한다. 근접 마진 목표 <25%는 미달이다. 이번 UI 수정으로 모델 품질이 개선됐다고 주장하지 않는다. K-FACE 저장소의 문서/예제는 확보했지만 실제 얼굴 원본은 없으므로 K-FACE 재평가를 완료하지 않았다.

아직 확인하지 않은 항목: 실제 관람객이 느끼는 닮음/만족도, Camera Module 3 초점·조명·Pi 처리시간, 실물 한글 IME/터치, ACR1252U 태그/재연결, ZTP-80USL2 종이·커터·장애 복구, 실제 MirrorTing 공동 흐름, 전원 재인가 및 장시간 연속 운영. 실행 안내의 현장 확인 순서에 따라 결과를 기록해야 한다. 퇴근 기념사진은 화면 미리보기에만 포함하며 종이 사진 출력은 현재 연결되지 않았다.
