# 체험 리포트 사진·취업지원센터 팁 검증 · 2026-10-12

## 변경 범위

- `backend/career_tips.py`: 첨삭 기반 팁 7개와 세션별 고정 선택.
- `backend/reports.py`: 선택 사진 전체 프레임 인쇄, 번호 섹션, 별도 센터 팁.
- `backend/souvenir.py`: 전체 사진 맞춤·디더링 처리를 리포트와 공유.
- `backend/app.py`: 조회에 로컬 팁 추가, 사진 multipart 출력 경로, 기존 세션/리포트 검증·중복 출력 방지 재사용.
- `frontend/js/app.js`, `live-integrations.js`: 촬영 Blob을 리포트 출력에 전달.
- `frontend/js/views.js`, `content.js`, `api-client.js`, `ui-preview.js`: 실제 인쇄 안내·별도 센터 팁·명시된 고정 샘플. HTML/모듈 URL 캐시 버전 갱신.
- `frontend/styles/kiosk.css`, `web.css`: 사진 전체 구도·작은 마스트헤드·센터 팁 박스.
- `tests/test_reports.py`, `test_api_flow.py`, `tests/frontend/kiosk.test.mjs`: 사진 포함·생략·재시도·중복 출력·안전한 문구 렌더링.
- README 및 계약·상태·흐름·설계·인수 문서: 화면 전용 사진 제한을 새 구현과 구분.

## 첨삭 출처 확인

첨부 DOCX를 원본 그대로 읽고 OOXML의 `FF0000` 글씨와 코멘트를 확인했다. 1~5번 조언, 전화 응대 제안, 마지막 메모·체크리스트 조언만 짧게 정리했다. 원본 문서를 수정하지 않았다. 내부 DOCX 렌더러는 한글 폰트 대체 문제로 일부 한글을 표시하지 못해 문구 확인은 원본 XML을 기준으로 했다. 실제 감열 리포트의 한글은 프로젝트 인쇄 폰트로 렌더링하고 이미지에서 확인했다.

## 자동 검증

- `.venv/bin/python -m pytest tests/test_reports.py tests/test_api_flow.py tests/test_souvenir.py -q`: 변경 초기 **53 passed**; 최종 단어 단위 줄바꿈은 전체 테스트에 포함.
- `.venv/bin/python -m pytest tests -q`: **112 passed, 1 skipped**. 기존 독립 스타일 표본 검사를 제외했으며 Starlette/httpx 기존 사용 중단 예정 경고 1개.
- `npm test`: **65 passed**, 최종 마스트헤드 수정 후 재실행.
- `git diff --check`, `.venv/bin/python -m compileall -q backend`: 통과.
- `.venv/bin/python scripts/preflight.py`: 소프트웨어·모델·8명 자산·한글 인쇄 폰트 통과. 실물 검사는 아님.
- 사진이 세로/가로인 경우 전체 프레임이 포함되고 576도트 1비트 출력임을 확인. 미측정 표기와 마지막 출처를 보존. 짧은 한글 단어가 중간에 끊기지 않도록 가능한 공백 단위로 줄바꿈하며 원문 문자·공백은 보존.
- 200개 샘플 세션에 7개 팁 모두 선택됨. 같은 세션의 팁은 반복 조회에서도 동일.
- 사진 포함 출력 후 JSON/사진 재요청도 같은 작업 결과이며 추가 인쇄 없음. 잘못된 사진·8 MiB 초과·다른 리포트 ID는 작업 시작 전 거부.
- 안전한 프린터 실패에서는 같은 사진/팁으로 명시적 재시도. 장치 제출 후 결과 불명은 잠금 유지.

## API와 실제 렌더러 결합 확인

임시 DB·샘플 카드·MirrorTing 샘플 응답을 사용한 TestClient에서 **실제 render_report → 화면 출력 백엔드 → 미리보기 조회**를 실행했다. 사진 포함 PNG는 **576×1648, 1비트**이며 뒤이은 JSON 재요청은 같은 미리보기를 반환했다. 테스트용 DB는 삭제했고 실제 서버의 방문자 DB는 변경하지 않았다. 물리 NFC·MirrorTing 서버·프린터를 사용한 검사가 아니다.

## 브라우저 확인

800×1280의 실제 샘플 클릭 흐름에서 **퇴근 → 카드 확인 시연 → 사진 선택 → 샘플 촬영 → 확인 → 리포트 → 출력 시연 → 완료**를 확인했다. 첫 리포트 화면에서 얼굴이 보이고, 내부 스크롤로 팁을 읽을 수 있으며 하단 CTA는 1164px 이내·가로 넘침 없음.

사진 없이 진행하면 사진 요소 0개·센터 팁 1개다. 스크롤 후 팁 구역이 리포트 안에 표시되며, 출력 오류 화면의 재시도/초기화 버튼은 각각 1078/1164px 이내다. `printer_error` 시연에서 명시적 재시도를 확인했다. DOM 기반 기본 버튼·스크롤 확인이며 실제 Pi 터치 센서 인수는 아니다.

## 출력 예시

상위 workspace `output/report-photo-tips-20261012/`:

- `report-with-photo-sample.png`: **576×2336**, 캐릭터 사진 + 샘플 점수/문구 + 센터 팁.
- `report-without-photo-sample.png`: **576×1632**, 사진 없이 같은 샘플 기록 + 같은 센터 팁.
- `report-photo-api-sample.png`: 실제 API·렌더러·화면 출력 백엔드 결합 결과, 별도 짧은 샘플.
- `report-screen-800x1280.png`, `report-tip-screen-800x1280.png`: 실제 샘플 클릭 흐름 화면.
- `tip-01-sample.png`~`tip-07-sample.png`, `all-seven-tips-preview.png`: 7개 팁의 글자·줄바꿈 확인용.

모든 사진은 기존 공개 샘플 캐릭터이며 실제 방문자 사진을 결과물로 저장하지 않았다. 예시 점수는 실제 분석 성능·방문자 평가가 아니다.

## 현재 실행 및 남은 인수

8012 서버를 실제 checkout에서 화면 모드(`KIOSK_PRINT=screen`, `KIOSK_NFC=disabled`)로 재시작했다. `/api/health` 응답과 수정한 checkout의 cwd를 확인했다. MirrorTing과 전용 사진 카드 설정은 현재 미설정이며 실제 연동 성공으로 표시하지 않는다.

실물 카메라/NFC·MirrorTing 공동 연결·감열지 얼굴 명암/한글 가독성/긴 용지 배출·절단·장시간 운영은 미확인이다. 사진을 넣으면 종이 길이가 늘어나므로 실제 용지 소비와 인쇄 시간을 현장에서 확인한다.
