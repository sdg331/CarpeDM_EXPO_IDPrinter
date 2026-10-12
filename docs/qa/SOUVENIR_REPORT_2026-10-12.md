# 브루탈리즘 리포트·사진 전용 인화 검증 · 2026-10-12

대상: `CarpeDM_EXPO_IDPrinter-complete`, 현재 미커밋 작업본. 다른 변경·캐릭터 자산·DB를 보존했다. 이 기록은 소프트웨어/브라우저 검증이며 현장 장치 인수 기록이 아니다.

## 적용

- 화면 리포트: 직각 검정 테두리·크림 배경·큰 제목·하드 섀도·번호 섹션·내부 스크롤. 공통 `web.css`의 기존 테두리 제거 규칙을 삭제해 실제 적용을 확인했다.
- 감열 리포트: 576도트·1비트, 굵은 헤더 테두리/섹션 띠. 실제 출처·미측정 값과 긴 리포트 줄바꿈은 유지한다.
- 전용 카드: HOME 별도 진입/일반 퇴근 카드 확인에서 전용 카드면 촬영 분기. 일반 사원증과 분리하고 이름·AI 매칭·MirrorTing 보고서 없이 사진·소개 QR을 인화한다.
- 기존 퇴근 동반 사진은 화면 전용으로 유지한다. 사진 외부 업로드·다운로드 서버는 구현하지 않는다.
- 현재 UI 캐시 버전 `20261012-keepsake-r4`, 캐릭터 사진 버전은 기존 `20261012-readiness-r1`이다.

## 수정 파일

- 구현: `backend/app.py`, `backend/reports.py`, `backend/store.py`, 새 `backend/souvenir.py`.
- 화면/호출/상태: `frontend/js/app.js`, `api-client.js`, `live-integrations.js`, `state.js`, `views.js`, `ui-preview.js`; `frontend/styles/kiosk.css`, `web.css`; `frontend/kiosk.html`, `ui-preview.html`.
- 설정/운영: `.env.example`, `scripts/kiosk_admin.py`, `scripts/preflight.py`.
- 테스트: `tests/frontend/kiosk.test.mjs`, 새 `tests/test_souvenir.py`.
- 문서: `README.md`, 새 `docs/SOUVENIR.md`, `docs/START_HERE.md`, `PROJECT_CONTEXT.md`, `USER_FLOW.md`, `SCREEN_DEFINITION.md`, `UI_STATE_SPEC.md`, `API_CONTRACT.md`, `ERROR_HANDLING.md`, `DECISIONS.md`, `ACCEPTANCE_CRITERIA.md`, `TESTING_GUIDE.md`, `FRONTEND_QA_CHECKLIST.md`, `IMPLEMENTATION_STATUS.md`, `DESIGN.md`, `docs/qa/README.md`, 이 기록. 앞선 미커밋 캐릭터/매칭 변경은 이번 작업에서 다시 수정하지 않았다.

## 테스트

- `npm test`: 프런트 63개 통과. 전용 카드→카메라→촬영 Blob→같은 출력 ID→완료/사진 해제, multipart/삭제 어댑터를 포함한다.
- `.venv/bin/python -m pytest tests -q`: 105개 통과, 1개 skip, 기존 Starlette/httpx 사용 경고 1개. Skip은 독립 스타일 표본이 없는 캐릭터 검사다.
- 새 `tests/test_souvenir.py`: 16개 통과. 승인 재사용/만료/취소, 전용 카드의 입사 등록 차단, 잘못된 카드·URL·이미지, local/origin 제한, QR 해독, 동시 출력·재시작·결과 불명 잠금/운영 복구를 확인한다. 이미 승인된 다른 촬영 권한도 결과 불명 작업을 우회해 출력할 수 없다.
- `node --check`, Python `compileall`, `git diff --check` 통과.
- 기본 `preflight.py` 통과. `--souvenir`는 실제 UID·QR 주소 미설정으로 두 항목 FAIL을 반환했다. 미설정을 성공으로 표시하지 않는다.
- 최초 bare `pytest -q`는 `integrations/mirrorting/test_kiosk_flow.py`의 `app` 모듈 부재로 수집 실패했다. 해당 파일은 별도 MirrorTing 저장소에 적용하는 테스트다. 현재 저장소의 실행 범위인 `pytest tests -q`로 검증했고 테스트 안내에도 이 경계를 적었다.

## 브라우저

현재 8012 FastAPI에서 다음을 확인했다.

- 800×1280 클릭 흐름: HOME 세 번째 진입→카드 시연→촬영→확인→인화 시연→완료. 이름 없이 완료되고 사진 참조를 해제한다.
- `scenario=printer_error`: 첫 인화 실패 화면→명시적 재시도→샘플 완료.
- 기존 퇴근: 카드 확인 시연→기록 확인→사진 없이 리포트→스크롤 가능한 브루탈리즘 리포트. 출력 CTA가 화면 안에 있다.
- 고정 미리보기 7화면×4상태=28개: HOME/리포트/전용 카드/촬영/확인/인화/결과. 이미지 로드, 가로 넘침 없음, 액션 버튼이 main 영역 안에 있음을 확인했다. 고정 화면 상태 검사는 실제 하드웨어 작업을 실행하지 않는다.
- 390×844 웹 HOME/기록 없음 상태: 가로 넘침 없음. 웹 미리보기에는 실물 카드 인화 진입을 표시하지 않는다.
- OS 실제 reduced-motion 전환, 카메라 실사 촬영, NFC 실물 태그는 이번에 검증하지 않았다. 사진/QR에는 반복 장식 애니메이션을 추가하지 않았다.

## 생성 파일

상위 `output/keepsake-20261012/`:

- `report-800x1280.png`: 브루탈리즘 샘플 리포트 화면.
- `souvenir-review-800x1280.png`: 샘플 사진·QR 설정 안내를 표시한 확인 화면.
- `report-thermal-sample.png`: 실제 리포트 렌더러의 테스트 fixture, 576×1346·1비트. 실제 방문자 분석 결과가 아니다.
- `souvenir-thermal-test-url.png`: 실제 사진 인화 렌더러, 576×1185·1비트. 캐릭터 샘플 사진과 **example.org 테스트 QR**이다. 실제 팀 사이트 주소로 사용하지 않는다.

## 남은 설정/현장 검증

최종 로컬 서버는 `KIOSK_NFC=disabled`, `KIOSK_PRINT=screen`, worker 1개로 8012에서 실행했다. health는 응답했고 `souvenir.configured:false`, NFC 미연결, 실물 출력 없음으로 표시했다.

실제 MirrorTing 소개 주소와 전용 카드 UID를 등록해야 한다. 아직 `.env`를 임의로 채우지 않았다. [설정/UID 확인/오류 복구](../SOUVENIR.md)를 따른다. 실제 Pi 카메라·카드·용지 명암·QR 휴대폰 스캔·급지·커터·연속 방문자 초기화는 별도 인수 항목이다.
